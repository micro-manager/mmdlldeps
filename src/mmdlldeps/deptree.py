import fnmatch
import os
from . import dumpbin
from . import executor
from . import systemdlls


def analyze_deps(directory, extensions=("dll", "exe")):
    # Analyzes files in directory with given extensions.
    # Return a dict whose keys are filenames and values are info dicts,
    # containing roots of the determinable dependency trees.
    # Each info dict has the following keys:
    #     calls_loadlibrary: tuple, e.g., ("LoadLibraryA", "LoadLibraryExW") or
    #                        empty
    #     bundled: True
    #     deps: dict
    #         key = filename
    #         value = dict
    #             bundled: boolean
    #             category: e.g., "system", "vc140", None (only if non-bundled)
    #             calls_loadlibrary: (see above) (only if bundled)
    #             deps: (recursive) (only if bundled)
    #             delay_load_deps: (ditto)
    #     delay_load_deps: dict, same structure as deps
    #
    # Caller is responsible for ensuring that all matched files are PE binaries.

    files = [
        file
        for pattern in ["*." + ext for ext in extensions]
        for file in fnmatch.filter(os.listdir(directory), pattern)
    ]

    def analyze_file(file):
        ordinary_deps, delay_deps = dumpbin.find_dependencies(
            os.path.join(directory, file)
        )
        return {
            "bundled": True,
            "calls_loadlibrary": _get_loadlibrary_status(
                os.path.join(directory, file)
            ),
            "deps": {dep: {} for dep in ordinary_deps},
            "delay_load_deps": {dep: {} for dep in delay_deps},
        }

    file_info_futures = [
        (file, executor.executor().submit(analyze_file, file)) for file in files
    ]
    all_bundled = {}
    for file, fut in file_info_futures:
        info = fut.result()
        all_bundled[file] = info

    bundled_casemap = {k.lower(): k for k in files}
    unclaimed = set(k.lower() for k in files)

    for file in files:
        info = all_bundled[file]
        for deptype in ("deps", "delay_load_deps"):
            deps = info[deptype]
            for dep in deps:
                assert not deps[dep]
                dep_lower = dep.lower()
                if dep_lower in bundled_casemap:
                    dep_canon = bundled_casemap[dep_lower]
                    unclaimed.discard(dep_lower)
                    deps[dep] = all_bundled[dep_canon]
                else:
                    deps[dep]["bundled"] = False
                    deps[dep]["category"] = _get_dll_category(dep)

    unclaimed_bundled = {
        k: v for (k, v) in all_bundled.items() if k.lower() in unclaimed
    }

    return unclaimed_bundled


def format_trees(deptrees, hide_categories=()):
    lines = []
    for root in sorted(deptrees, key=lambda x: x.lower()):
        _format_tree(lines, root, deptrees[root], "", "", hide_categories)
    return "\n".join(lines)


def format_tree(rootname, info):
    return format_trees({rootname: info})


def _format_tree(lines, rootname, info, indent_0, indent_n, hide_categories):
    if info["bundled"]:
        annotation = "bundled"
    else:
        category = info["category"]
        if category in hide_categories:
            return
        annotation = category if category else "EXTERNAL"
    lines.append(f"{indent_0}{rootname} ({annotation})")

    if info["bundled"]:
        for func in info["calls_loadlibrary"]:
            lines.append(f"{indent_n}    (calls {func})")

        ordinary_deps = info["deps"]
        for dep in sorted(ordinary_deps, key=lambda x: x.lower()):
            depinfo = ordinary_deps[dep]
            _format_tree(
                lines,
                dep,
                depinfo,
                indent_n + "    ",
                indent_n + "    ",
                hide_categories,
            )

        delay_deps = info["delay_load_deps"]
        for dep in sorted(delay_deps, key=lambda x: x.lower()):
            depinfo = delay_deps[dep]
            _format_tree(
                lines,
                dep,
                depinfo,
                indent_n + "  D ",
                indent_n + "    ",
                hide_categories,
            )

    return lines


_LOADLIBRARY_SYMBOLS = (
    "LoadLibraryA",
    "LoadLibraryW",
    "LoadLibraryExA",
    "LoadLibraryExW",
)
_LOADLIBRARY_DLLS = ("KERNEL32.dll", "KERNEL32")


def _get_loadlibrary_status(file):
    return tuple(
        func
        for (dll, func) in dumpbin.find_symbol_import(
            file, _LOADLIBRARY_SYMBOLS, _LOADLIBRARY_DLLS
        )
    )


_SYSTEM_DLLS = None


def _system_dlls():
    global _SYSTEM_DLLS
    if not _SYSTEM_DLLS:
        _SYSTEM_DLLS = set(k.lower() for k in systemdlls.get_system_dlls())
    return _SYSTEM_DLLS


_VC140_DLLS = set(k.lower() for k in systemdlls.get_vc_dlls(140))


def _get_dll_category(file):
    low = file.lower()
    if low in _system_dlls():
        return "system"
    if low in _VC140_DLLS:
        return "vc140"
    if "." not in file:
        return _get_dll_category(file + ".dll")
