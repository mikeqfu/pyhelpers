@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "" goto help

REM Custom clean target to remove build artifacts and generated API source files
if "%1" == "clean" (
    if exist "%BUILDDIR%" (
        for /d %%i in (%BUILDDIR%\*) do rmdir /s /q "%%i"
        del /q /f %BUILDDIR%\*
    )
    if exist "%SOURCEDIR%\api" (
        for /d %%i in (%SOURCEDIR%\api\*) do rmdir /s /q "%%i"
        del /q /f %SOURCEDIR%\api\*
    )
    echo.Cleaned build directory and generated API source files.
    goto end
)

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
