@echo off

REM switch working directory to where this file locates
cd /d "%~dp0"

app.exe

echo.

echo Execution finished. Press any key to close this window...

REM wait for any key to continue and suppress the default prompt
pause > nul

exit