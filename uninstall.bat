@echo off
setlocal enabledelayedexpansion

REM Betigin calisma dizinini KENDI konumuna sabitle - "Yonetici olarak
REM calistir" bazi Windows kurulumlarinda calisma dizinini System32ye
REM sabitleyip goreli yol/robocopy komutlarini sessizce bozabiliyor.
cd /d "%~dp0"

echo ============================================
echo   DIGITAL 5S - TOOL KALDIRMA
echo ============================================
echo.

set DEFAULT_CORE=..\aktapokus-core
set /p CORE_PATH=Core klasoru nerede? [%DEFAULT_CORE%]: 
if "%CORE_PATH%"=="" set CORE_PATH=%DEFAULT_CORE%

if not exist "%CORE_PATH%\tools\d5s" goto NOTINSTALLED

echo Bu islem sunu SILECEK: %CORE_PATH%\tools\d5s\
echo Klasorlerinizdeki analiz edilen dosyalar ETKILENMEZ - sadece
echo D5S'in kendi kodu silinir.
echo.
set DB_FILE=%CORE_PATH%\tools\d5s\audit\d5s_audit.sqlite
if exist "%DB_FILE%" (
    echo Islem gecmisi ^(audit log^) bulundu, otomatik yedeklenecek.
)
echo.
choice /c ED /m "Devam edilsin mi? (E=Evet, D=Dur)"
if errorlevel 2 goto CANCELLED

if not exist "%DB_FILE%" goto SKIPBACKUP
echo [1/3] Islem gecmisi yedekleniyor...
for /f "delims=" %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
copy "%DB_FILE%" "%CORE_PATH%\d5s_audit_backup_%TS%.sqlite" >nul
if errorlevel 1 goto BACKUPFAIL
echo       Yedek: %CORE_PATH%\d5s_audit_backup_%TS%.sqlite
goto DODELETE

:SKIPBACKUP
echo [1/3] Yedeklenecek islem gecmisi bulunamadi, atlaniyor.

:DODELETE
echo [2/3] Dosyalar siliniyor: %CORE_PATH%\tools\d5s\
rmdir /s /q "%CORE_PATH%\tools\d5s"
if exist "%CORE_PATH%\tools\d5s" goto DELFAIL

echo [3/3] Container yeniden baslatiliyor...
pushd "%CORE_PATH%\core"
docker compose restart app
popd

echo.
echo ============================================
echo   D5S KALDIRILDI
echo ============================================
echo   Arayuzu yenileyin: http://localhost:8000
echo   Tool listesinde artik gorunmemeli.
echo ============================================
pause
exit /b 0

:NOTINSTALLED
echo D5S zaten kurulu degil: %CORE_PATH%\tools\d5s bulunamadi.
pause
exit /b 0

:CANCELLED
echo Iptal edildi, hicbir sey silinmedi.
pause
exit /b 0

:BACKUPFAIL
echo [HATA] Yedekleme basarisiz oldu. Guvenlik icin silme islemi durduruldu.
pause
exit /b 1

:DELFAIL
echo [HATA] Dosyalar silinemedi - klasor kullanimda olabilir.
echo        Docker Desktop'i durdurup tekrar deneyin.
pause
exit /b 1
