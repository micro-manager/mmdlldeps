@echo off

for /f "usebackq delims=#" %%d in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere" -latest -property installationPath`) do set "VsDevCmdBatchFile=%%d\Common7\Tools\VsDevCmd.bat"

call "%VsDevCmdBatchFile%" >NUL
if errorlevel 1 exit /b

rem Get the full path of dumpbin
for /f "usebackq delims=#" %%f in (`where dumpbin.exe`) do set "DUMPBIN_EXE=%%f"

set