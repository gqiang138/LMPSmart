@echo off
chcp 65001 >nul
title lmpsmart — Smart Installer
echo.
echo ╔══════════════════════════════════════════════╗
echo ║         lmpsmart Installation Wizard           ║
echo ╚══════════════════════════════════════════════╝
echo.
python "%~dp0install.py"
pause
