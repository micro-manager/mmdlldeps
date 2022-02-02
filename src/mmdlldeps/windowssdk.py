import glob
import os
import os.path


def windows_sdk_root(version):
    path = os.path.join(
        os.environ["ProgramFiles(x86)"], "Windows Kits", version
    )
    if not os.path.exists(path):
        raise RuntimeError(
            f"Windows {version} SDK is not installed ({path} not found)"
        )
    return path


def latest_windows_sdk_libs(version):
    if version == "10":
        libroot = os.path.join(windows_sdk_root(version), "Lib")
        sdk_versions = glob.glob("10.0.*", root_dir=libroot)
        if not sdk_versions:
            path = os.path.join(libroot, "*10.0.*")
            raise RuntimeError(
                f"Windows {version} SDK is not installed ({path} not found)"
            )
        latest_sdk_version = sorted(sdk_versions)[-1]
        return os.path.join(libroot, latest_sdk_version)
    else:
        raise NotImplementedError(
            f"I don't know how to find the Windows {version} SDK"
        )
