import argparse
from . import deptree


def print_mmreport(results, hide_categories):
    def has_external_dep(info):
        for dep, depinfo in info["deps"].items():
            if not depinfo["bundled"] and not depinfo["category"]:
                return True
        for dep, depinfo in info["delay_load_deps"].items():
            if not depinfo["bundled"] and not depinfo["category"]:
                return True
        return False

    def has_bundled_dep(info):
        for dep, depinfo in info["deps"].items():
            if depinfo["bundled"]:
                return True
        for dep, depinfo in info["delay_load_deps"].items():
            if depinfo["bundled"]:
                return True
        return False

    orphans, da_extdep, da_bundled, da_loadlib, da_nodep = {}, {}, {}, {}, {}
    for file, info in results.items():
        if not file.startswith("mmgr_dal_"):
            orphans[file] = info
        elif has_external_dep(info):
            da_extdep[file] = info
        elif has_bundled_dep(info):
            da_bundled[file] = info
        elif info["calls_loadlibrary"]:
            da_loadlib[file] = info
        else:
            da_nodep[file] = info

    print("Orphans (possibly loaded by LoadLibrary) ({}):".format(len(orphans)))
    print(deptree.format_trees(orphans, hide_categories))
    print()
    print(
        "Device adapters with external dependencies ({}):".format(
            len(da_extdep)
        )
    )
    print(deptree.format_trees(da_extdep, hide_categories))
    print()
    print(
        "Device adapters with bundled dependencies ({}):".format(
            len(da_bundled)
        )
    )
    print(deptree.format_trees(da_bundled, hide_categories))
    print()
    print("Device adapters that call LoadLibrary ({}):".format(len(da_loadlib)))
    print(deptree.format_trees(da_loadlib, hide_categories))
    print()
    print("Device adapters with no dependencies ({}):".format(len(da_nodep)))
    print(deptree.format_trees(da_nodep, hide_categories))
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="python -m mmdlldeps",
        description="Generate DLL dependency report for directory",
    )
    parser.add_argument(
        "directory",
        help="the directory containing DLLs and EXEs to analyze",
    )
    parser.add_argument(
        "--hide-system",
        action="store_true",
        help="do not list Windows system DLLs as dependencies",
    )
    parser.add_argument(
        "--hide-vc140",
        action="store_true",
        help="do not list Visual Studio 2015-2022 runtime DLLs",
    )
    parser.add_argument(
        "--mmreport",
        action="store_true",
        help="generate report tailored to Micro-Manager distribution",
    )

    args = parser.parse_args()

    results = deptree.analyze_deps(args.directory)
    hide_categories = []
    if args.hide_system:
        hide_categories.append("system")
    if args.hide_vc140:
        hide_categories.append("vc140")
    if args.mmreport:
        print_mmreport(results, hide_categories)
    else:
        print(deptree.format_trees(results, hide_categories=hide_categories))


if __name__ == "__main__":
    main()
