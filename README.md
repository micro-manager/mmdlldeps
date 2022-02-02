# DLL dependency reporting script for Micro-Manager

This is a developer/maintainer tool to analyze Micro-Manager DLLs and help
diagnose dependency issues.

## Requirements

- Windows
- A recent version (e.g. 2019, 2022) of Visual Studio with C++ Desktop
  Development workload
- Windows 10 SDK (usually installed with Visual Studio)
- Python (e.g. 3.10)

## Input

A Micro-Manager install directory (or staging directory)

## Usage

Clone the source code and install by running `pip install .` at the source root.
If developing `mmdlldeps`, install into a virtual environment using `pip install
--editable .`.

See `mmdlldeps --help` for usage.

Typically, run

```sh
mmdlldeps --mmreport --hide-system --hide-vc140 MM_DIR
```

where `MM_DIR` is a Micro-Manager installation or stage directory (or any
directory containing a collection of DLLs and executables of interest).

The `--mmreport` option causes the output to be categorized. Without
`--mmreport` the output will be in a generic format (no Micro-Manager-specific
assumptions made).

## Interpreting the output

The output lists each DLL, together with its knowable dependency tree. DLLs that
show up as a dependency to another DLL are skipped from being listed at the top
level.

DLLs are annotated:

- `bundled`: file is present in the input directory
- `system`: DLL is known to be a Windows system DLL (linked via the Windows
  SDK, including the Universal C Runtime)
- `vc140`: DLL is known to be part of the Visual Studio 2015-2022
  Redistributable (i.e., part of the C++ runtime)
- `EXTERNAL`: DLL is not bundled and not part of a known category

In addition, DLLs that call the `LoadLibrary` or `LoadLibraryEx` function are
indicated in an indented line. Note that there are other ways a DLL can depend
on external DLLs, such as via Microsoft COM (cf. `mmgr_dal_NikonTI.dll`) or by
running an external executable (cf. `mmgr_dal_OlympusIX83.dll`).

There is no substitute for detailed knowledge of Windows and Visual Studio APIs,
SDKs, and runtimes, but here are some rules of thumb:

- `EXTERNAL` dependencies `MSVCP100.dll` and `MSVCR100.dll` are part of the
  Visual C++ 2010 Redistributable (runtime). Similarly for different versions:
  `80` = 2005, `90` = 2008, `100` = 2010, `110` = 2012, `120` = 2013. Vendor
  DLLs that have these dependencies will _generally_ work with device adapters
  built with v140 (modern Visual C++, 2015+) _if_ (1) the correct
  Visual C++ Redistributable is installed and (2) the interface to the DLL is
  in C, not C++.

  - C++ APIs typically have problems (sometimes obvious, sometimes subtle)
    between DLLs built against different runtime versions prior to VS2015. C
    APIs, if designed correctly, typically avoid such problems. But neither
    of these statements is absolute.

- Vendor DLLs listed as `EXTERNAL` usually need to be installed by the user.
  Either they are placed in a system directory (so that they are available to
  all apps), or the user needs to copy them into the Micro-Manager directory,
  or, in some cases, the SDK may have a special mechanism to load the DLL(s)
  from their installed location.

  - `EXTERNAL` DLLs may have further (transitive) non-system dependencies,
    which are not reported (because they are unknowable without analyzing those
    missing DLLs).

  - How exact a version match is required for external DLLs with the version
    used in the build depend on the DLL. See the above comments regarding C and
    C++ runtime versions, but it also depends on the vendor's practices.

- DLLs that are not listed as a dependency may by loaded using one of the
  `LoadLibrary` family functions. These dependencies can only be manually
  determined (usually from the device adapter source code).

  - Sometimes, the vendor provides a static library (`.lib`) that handles the
    loading of their DLL via `LoadLibrary`. In this case, the device adapter
    will call `LoadLibrary` even if the function does not show up in the device
    adapter source code.

  - The non-device-adapter DLLs categorized at the top level as "orphans" are
    mostly those loaded via `LoadLibrary` by one of the device adapters, or as
    a JNI library by the Java runtime. Grep their names in the source code to
    find out.
