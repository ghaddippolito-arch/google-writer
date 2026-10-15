@echo off
title Autenticar Google Docs - ACI Writer
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python311\python.exe" auth_google.py
