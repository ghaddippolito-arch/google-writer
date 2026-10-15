@echo off
chcp 65001 >nul
echo ========================================================
echo   ACI Writer - Subir código a GitHub
echo ========================================================
echo.
echo Repositorio destino: https://github.com/ghaddippolito-arch/google-writer
echo.
echo GitHub requiere un token de acceso personal para subir código:
echo 1. Abre en tu navegador: https://github.com/settings/tokens/new?scopes=repo^&description=GoogleWriterDeploy
echo 2. Baja hasta el final y haz clic en "Generate token".
echo 3. Copia el token que empieza con "ghp_..."
echo.
set /p TOKEN="Pega tu token de GitHub aquí (ghp_...): "

if "%TOKEN%"=="" (
    echo [ERROR] No ingresaste ningún token.
    pause
    exit /b
)

echo.
echo Subiendo código a GitHub...
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" remote remove origin 2>nul
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" remote add origin https://github.com/ghaddippolito-arch/google-writer.git
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" branch -M main
"%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe" push -u https://%TOKEN%@github.com/ghaddippolito-arch/google-writer.git main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo   ¡CÓDIGO SUBIDO EXITOSAMENTE A TU GITHUB!
    echo ========================================================
) else (
    echo [ERROR] Ocurrió un error al subir. Verifica que el token sea correcto.
)
pause
