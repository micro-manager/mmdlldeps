import os.path
from mmdlldeps import dumpbin
from mmdlldeps import windowssdk


KERNEL32_PATH = "C:\\Windows\\System32\\kernel32.dll"


def test_dumpbin():
    d = dumpbin.dumpbin(KERNEL32_PATH)
    assert d.startswith("Dump of file ")
    assert "File Type: DLL" in d
    assert "Summary" in d


def test_find_dependencies():
    ordinary, delay = dumpbin.find_dependencies(KERNEL32_PATH)
    assert len(ordinary) > 1
    assert "ntdll.dll" in [d.lower() for d in ordinary]


def test_find_symbol_import():
    found = dumpbin.find_symbol_import(KERNEL32_PATH, "Sleep", "KERNELBASE.dll")
    assert len(found) == 1
    dll, sym = found[0]
    assert dll.lower() == "kernelbase.dll"
    assert sym == "Sleep"


def test_find_lib_dlls():
    ucrtlib = os.path.join(
        windowssdk.latest_windows_sdk_libs("10"), "ucrt", "x64", "ucrt.lib"
    )
    dlls = dumpbin.find_lib_dlls(ucrtlib)
    for dll in dlls:
        if dll.startswith("api-ms-win-crt-"):
            return
    assert False


def test_parse_dump_common_parts():
    dump = dumpbin.dumpbin(KERNEL32_PATH)
    filename, filetype, sections = dumpbin._parse_dump_common_parts(dump)
    assert filename == KERNEL32_PATH
    assert filetype == "DLL"
    assert len(sections) == 1  # Summary only
    summary = sections["Summary"]
    assert len(summary) == 1
    assert ".data\n" in summary[0]
