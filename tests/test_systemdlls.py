from mmdlldeps import systemdlls


def test_get_system_dlls():
    dlls = systemdlls.get_system_dlls()
    low = set(d.lower() for d in dlls)
    assert "kernel32.dll" in low
    assert "advapi32.dll" in low
