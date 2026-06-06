@echo off
setlocal
if "%1"=="" (
    echo Kullanım: mrrinstall ^<kutuphane_adi^>
    exit /b 1
)

echo [MRR Package Manager] %1 yukleniyor...
python -m pip install %1

if %ERRORLEVEL% equ 0 (
    echo [MRR Package Manager] %1 basariyla kuruldu!
    echo Artik kodunuzda 'add.code "%1"' yazarak kullanabilirsiniz.
) else (
    echo [MRR Package Manager] Kurulum sirasinda bir hata olustu.
)
exit /b %ERRORLEVEL%
