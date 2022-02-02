import glob
import os.path
from . import dumpbin
from . import executor
from . import windowssdk


def get_system_dlls():
    # Returns set of all DLLs linked by the Windows SDK and UCRT libraries
    um_libs = glob.glob(
        os.path.join(
            windowssdk.latest_windows_sdk_libs("10"), "um", "x64", "*.lib"
        )
    )
    ucrt_lib = os.path.join(
        windowssdk.latest_windows_sdk_libs("10"), "ucrt", "x64", "ucrt.lib"
    )
    libs = um_libs + [ucrt_lib]

    lib_dll_futures = [
        (lib, executor.executor().submit(dumpbin.find_lib_dlls, lib))
        for lib in libs
    ]

    all_dlls = set()
    for lib, fut in lib_dll_futures:
        dlls = fut.result()
        all_dlls.update(dlls)

    # A few known system DLLs that do not show up in the Windows 10 SDK
    # msvcrt.dll is not supposed to be used by apps, but people violate this.
    # shcore.dll seems legit, but current Windows SDKs do not link to it(?)
    all_dlls.add("msvcrt.dll")
    all_dlls.add("shcore.dll")

    return all_dlls


def get_vc_dlls(version):
    if version == 140:
        return set(
            [
                "CONCRT140.dll",
                "MSVCP140.dll",
                "VCCORLIB140.dll",
                "VCRUNTIME140.dll",
                "VCRUNTIME140_1.dll",
            ]
        )
    raise NotImplementedError(f"VC DLLs for version {version} not known")
