@echo off
setlocal enabledelayedexpansion

REM Betigin calisma dizinini KENDI konumuna sabitle - "Yonetici olarak
REM calistir" bazi Windows kurulumlarinda calisma dizinini System32ye
REM sabitleyip goreli yol/robocopy komutlarini sessizce bozabiliyor.
cd /d "%~dp0"

echo ============================================
echo   DIGITAL 5S - TOOL KURULUM
echo ============================================
echo.

set DEFAULT_CORE=..\aktapokus-core
set /p CORE_PATH=Core klasoru nerede? [%DEFAULT_CORE%]: 
if "%CORE_PATH%"=="" set CORE_PATH=%DEFAULT_CORE%

if not exist "%CORE_PATH%\core\docker-compose.yml" goto BADCORE
if not exist "%CORE_PATH%\.env" goto NOENV

echo [1/2] Dosyalar kopyalaniyor: %CORE_PATH%\tools\d5s\
if not exist "%CORE_PATH%\tools\d5s" mkdir "%CORE_PATH%\tools\d5s"
robocopy . "%CORE_PATH%\tools\d5s" /E /XF setup.bat /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 goto COPYFAIL

echo [2/2] Container yeniden build ediliyor - yeni bagimlilik olabilir...
pushd "%CORE_PATH%\core"
docker compose up -d --build
if errorlevel 1 goto BUILDFAIL
popd

echo.
echo ============================================
echo   D5S KURULDU
echo ============================================
echo   Arayuzu yenileyin: http://localhost:8000
echo   Tool listesinde "Digital 5S" gorunmeli.
echo ============================================
pause
exit /b 0

:BADCORE
echo [HATA] Belirtilen yolda aktapokus-core bulunamadi: %CORE_PATH%
echo        core\docker-compose.yml orada olmali. Once core kurulumunu
echo        yapip setup.bat'ini calistirin.
pause
exit /b 1

:NOENV
echo [HATA] %CORE_PATH%\.env bulunamadi.
echo        Once core klasorunde setup.bat'i calistirip core kurulumunu
echo        tamamlayin, sonra bu betigi tekrar calistirin.
pause
exit /b 1

:COPYFAIL
echo [HATA] Dosyalar kopyalanamadi.
pause
exit /b 1

:BUILDFAIL
echo [HATA] Docker build basarisiz oldu. Yukaridaki hatayi kontrol edin.
popd
pause
exit /b 1
