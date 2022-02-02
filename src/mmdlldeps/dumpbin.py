import pkg_resources
import subprocess
from collections import OrderedDict


_VSENV_BATCH_FILE = pkg_resources.resource_filename(__name__, "vsenv.bat")

_FIRST_WORDS = "Dump of file "
_FILE_TYPE_PREFIX = "File Type: "

_SECTION_HEADER_INDENT = "  "
_SUMMARY_HEADER = "Summary"
_DEPENDENCY_LIST_HEADER = "Image has the following dependencies:"
_DELAY_DEPENDENCY_LIST_HEADER = (
    "Image has the following delay load dependencies:"
)
_IMPORT_LIST_HEADER = "Section contains the following imports:"
_DELAY_IMPORT_LIST_HEADER = "Section contains the following delay load imports:"


_CACHED_VS_ENV = None


def _get_vs_env():
    # Return the environment variables resulting from setting up the Visual
    # Studio Developer Command Prompt. This is slow, so doing it once helps.
    global _CACHED_VS_ENV
    if not _CACHED_VS_ENV:
        output = subprocess.run(
            [_VSENV_BATCH_FILE],
            capture_output=True,
            check=True,
            text=True,
        ).stdout
        _CACHED_VS_ENV = dict(
            line.split("=", 1) for line in output.splitlines() if line
        )
    return _CACHED_VS_ENV


def _get_dumpbin_exe():
    return _get_vs_env()["DUMPBIN_EXE"]


def dumpbin(file, option="/summary"):
    output = subprocess.run(
        [_get_dumpbin_exe(), "/nologo", option, file],
        env=_get_vs_env(),
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    return output.strip() + "\n"


def find_dependencies(file):
    dump = dumpbin(file, "/dependents")
    filename, _, sections = _parse_dump_common_parts(dump)

    ordinary_deps, delay_deps = [], []

    for header in (_DEPENDENCY_LIST_HEADER, _DELAY_DEPENDENCY_LIST_HEADER):
        if header in sections:
            dest = {
                _DEPENDENCY_LIST_HEADER: ordinary_deps,
                _DELAY_DEPENDENCY_LIST_HEADER: delay_deps,
            }[header]
            paragraphs = sections[header]
            assert len(paragraphs) == 1
            dest.extend(line.strip() for line in paragraphs[0].splitlines())

    return ordinary_deps, delay_deps


def find_symbol_import(file, symbols, dlls):
    # If file imports any of symbols from any of dlls, return list of pairs
    # (dllname, symbol); otherwise, return empty list.

    if isinstance(symbols, str):
        symbols = [symbols]
    if isinstance(dlls, str):
        dlls = [dlls]

    dump = dumpbin(file, "/imports")
    filename, _, sections = _parse_dump_common_parts(dump)
    ordinary_imports, delay_imports = _parse_symbol_imports(sections)

    found = []
    for imports in (ordinary_imports, delay_imports):
        casemap = {k.lower(): k for k in imports}
        for dll in dlls:
            dll_lower = dll.lower()
            if dll_lower in casemap:
                dll_canon = casemap[dll_lower]
                dll_imports = imports[dll_canon]
                for symbol in symbols:
                    if symbol in dll_imports:
                        found.append((dll_canon, symbol))

    return found


def find_lib_dlls(file):
    # Return the set of DLLs linked by the given import library
    dump = dumpbin(file, "/archivemembers")
    filename, _, _ = _parse_dump_common_parts(dump, parse_sections=False)
    dlls = set(
        line.strip().split()[-1].rstrip("/")
        for line in dump.splitlines()
        if line.startswith("Archive member name at ")
    )
    dlls.discard("")  # Remove the "/" member
    dlls = set(dll for dll in dlls if not dll.lower().endswith(".obj"))
    return dlls


def _parse_dump_common_parts(dump, parse_sections=True):
    # This works for DLL/EXE dependents and imports; other output formats may
    # vary

    # Normalize empty paragraphs so that every conceptual paragraph is separated
    # by "\n\n"
    dump = "\n\n\n\n".join(dump.split("\n\n\n"))

    paragraphs = dump.split("\n\n")

    p = paragraphs.pop(0)
    assert p.startswith(_FIRST_WORDS)
    filename = p[len(_FIRST_WORDS) :]

    p = paragraphs.pop(0)
    assert p.startswith(_FILE_TYPE_PREFIX)
    filetype = p[len(_FILE_TYPE_PREFIX) :]

    if parse_sections:
        sections = _find_sections(paragraphs)
        assert sections
        assert _SUMMARY_HEADER in sections
    else:
        sections = OrderedDict()

    return filename, filetype, sections


def _find_sections(paragraphs):
    # Return an OrderedDict of sections
    # key = section header
    # value = list of section body paragraphs
    # Sections start with section headers, which are paragraphs that start with
    # exactly _SECTION_HEADER_INDENT.
    sections = OrderedDict()
    for p in paragraphs:
        if (
            p.startswith(_SECTION_HEADER_INDENT)
            and p[len(_SECTION_HEADER_INDENT)] != " "
            and "\n" not in p
        ):
            header = p.strip()
            assert header not in sections  # We do not expect duplicates
            sections[header] = []
        else:
            sections[header].append(p + "\n")  # Restore trailing newline

    return sections


def _parse_symbol_imports(sections):
    ordinary_imports, delay_imports = OrderedDict(), OrderedDict()

    for header in (_IMPORT_LIST_HEADER, _DELAY_IMPORT_LIST_HEADER):
        if header in sections:
            dest = {
                _IMPORT_LIST_HEADER: ordinary_imports,
                _DELAY_IMPORT_LIST_HEADER: delay_imports,
            }[header]
            paragraphs = sections[header]
            # Each DLL has 2 paragraphs, but the second may be empty
            for first, second in _pairwise(paragraphs):
                assert first.startswith(" " * 4)
                assert not first.startswith(" " * 5)
                first_line, offset_table = first.split("\n", 1)
                dll_name = first_line[4:]

                if not second.strip():
                    dest[dll_name] = []
                else:
                    assert second.startswith(" " * 5)
                    symbols = [line.split()[-1] for line in second.splitlines()]
                    dest[dll_name] = symbols

    return ordinary_imports, delay_imports


def _pairwise(seq):
    it = iter(seq)
    return zip(it, it)
