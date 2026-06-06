@echo off
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════════════════════
:: MRR Programming Language — CLI Interface v1.0.1 Resilient
:: Memory, Registers, Rings — Offensive Security Language
:: ═══════════════════════════════════════════════════════════

:: Get the directory of this batch file (bin folder)
set BIN_DIR=%~dp0
:: Get the root MRR directory
set MRR_ROOT=%BIN_DIR%..
set PYTHONPATH=%MRR_ROOT%

:: If no arguments, print usage
if "%~1"=="" goto :usage

:: Route commands
set CMD=%~1
shift

if /i "%CMD%"=="run"      goto :cmd_run
if /i "%CMD%"=="build"    goto :cmd_build
if /i "%CMD%"=="compile"  goto :cmd_compile
if /i "%CMD%"=="init"     goto :cmd_init
if /i "%CMD%"=="format"   goto :cmd_format
if /i "%CMD%"=="fmt"      goto :cmd_format
if /i "%CMD%"=="pkg"      goto :cmd_pkg
if /i "%CMD%"=="check"    goto :cmd_check
if /i "%CMD%"=="repl"     goto :cmd_repl
if /i "%CMD%"=="version"  goto :cmd_version
if /i "%CMD%"=="optimize" goto :cmd_optimize
if /i "%CMD%"=="help"     goto :usage
if /i "%CMD%"=="lsp"      goto :cmd_lsp

:: If first arg is a file, treat as "run"
if exist "%CMD%" (
    python -m interpreter.main run "%CMD%" %1 %2 %3 %4 %5 %6 %7 %8
    goto :eof
)

echo [MRR] Bilinmeyen komut: %CMD%
echo Yardim icin: mrr help
goto :eof

:: ─────────────────────────────────────────────────────
:: COMMANDS
:: ─────────────────────────────────────────────────────

:cmd_run
python -m interpreter.main run %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_build
python -m interpreter.main build %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_compile
python -m interpreter.main compile %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_init
python -m interpreter.main init %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_format
python -m interpreter.main format %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_pkg
python -m interpreter.main pkg %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_check
python -m interpreter.main check %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_repl
python -m interpreter.main repl
goto :eof

:cmd_version
python -m interpreter.main version
goto :eof

:cmd_optimize
java -cp "%MRR_ROOT%\optimizer" MrrOptimizer %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:cmd_lsp
python -m interpreter.main lsp %1 %2 %3 %4 %5 %6 %7 %8
goto :eof

:: ─────────────────────────────────────────────────────

:usage
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║  MRR — Memory, Registers, Rings                    ║
echo  ║  Offensive Security Programming Language v1.0.1    ║
echo  ║  Codename: Resilient                               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  USAGE:
echo    mrr ^<command^> [options] [arguments]
echo.
echo  COMMANDS:
echo    run ^<file.mrr^>        Dosyayi calistir (Interpreter)
echo    build ^<file.mrr^>      .mbuild veya .exe olustur
echo    compile ^<file.mrr^>    Makine koduna derle
echo    init [name]            Yeni MRR projesi olustur
echo    format ^<file.mrr^>     Kodu formatla (Prettier benzeri)
echo    fmt ^<file.mrr^>        format komutunun kisayolu
echo    check ^<file.mrr^>      Syntax kontrolu (derlemesiz)
echo    optimize ^<file.mrr^>   Kodu optimize et (Java)
echo    pkg ^<subcmd^>          Paket yoneticisi
echo    repl                   Interaktif REPL terminali
echo    lsp                    LSP sunucusunu baslat
echo    version                Surum bilgisi
echo    help                   Bu yardim mesaji
echo.
echo  PACKAGE MANAGER (pkg):
echo    mrr pkg init [name]       Yeni proje olustur (mrr.toml)
echo    mrr pkg install ^<pkg^>    Paket yukle
echo    mrr pkg remove ^<pkg^>     Paket kaldir
echo    mrr pkg list              Yuklu paketleri listele
echo    mrr pkg update            Paketleri guncelle
echo.
echo  EXAMPLES:
echo    mrr run hello.mrr           Dosyayi calistir
echo    mrr hello.mrr               Kisayol: dosyayi dogrudan calistir
echo    mrr format *.mrr            Tum dosyalari formatla
echo    mrr init my_project         Yeni proje olustur
echo    mrr pkg install scanner     scanner paketini yukle
echo    mrr check vuln_scanner.mrr  Syntax kontrolu
echo.
goto :eof
