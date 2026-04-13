@echo off
REM Dr. Oh v3.0 launcher (Windows).
REM Directory name audrey_v3.0 has a '.' so it cannot be a Python package name;
REM we cd into it and run the inner `src` module.
set "HERE=%~dp0.."
pushd "%HERE%"
python -m src %*
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
