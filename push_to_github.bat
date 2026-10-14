@echo off
chcp 65001 >nul
echo ========================================================
echo   Google Writer - Subir repositorio a GitHub
echo ========================================================
echo.

set /p REPO_URL="Pega la URL de tu nuevo repositorio de GitHub (ej: https://github.com/tu-usuario/google-writer.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] No ingresaste ninguna URL.
    pause
    exit /b
)

echo.
echo [1/3] Vinculando repositorio remoto...
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" remote remove origin 2>nul
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" remote add origin %REPO_URL%

echo [2/3] Configurando rama principal 'main'...
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" branch -M main

echo [3/3] Subiendo archivos a GitHub...
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo   ¡REPOSITORIO SUBIDO CON ÉXITO A GITHUB!
    echo ========================================================
) else (
    echo [ERROR] Hubo un problema al subir a GitHub. Verifica tus credenciales de GitHub.
)
pause
