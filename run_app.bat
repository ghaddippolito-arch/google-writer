@echo off
title ACI Writer - Streamlit Server
cd /d "%~dp0"
echo ========================================================
echo       Iniciando ACI Writer (Streamlit Server)
echo ========================================================
echo.
"%LOCALAPPDATA%\Programs\Python\Python311\python.exe" -m streamlit run app.py
pause
