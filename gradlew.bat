@echo off
REM Minimal Gradle bootstrap for environments without the standard wrapper JAR.
set GRADLE_VERSION=8.7
set CACHE_DIR=%USERPROFILE%\.gradle\cto-wrapper
set DIST_DIR=%CACHE_DIR%\gradle-%GRADLE_VERSION%
set ZIP_PATH=%CACHE_DIR%\gradle-%GRADLE_VERSION%-bin.zip

if exist "%DIST_DIR%\bin\gradle.bat" goto run

if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"

if not exist "%ZIP_PATH%" (
  echo Downloading Gradle %GRADLE_VERSION%...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "(New-Object Net.WebClient).DownloadFile('https://services.gradle.org/distributions/gradle-%GRADLE_VERSION%-bin.zip', '%ZIP_PATH%')" || exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force '%ZIP_PATH%' '%CACHE_DIR%'" || exit /b 1

:run
call "%DIST_DIR%\bin\gradle.bat" -p "%~dp0" %*
