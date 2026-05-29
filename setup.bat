@echo off
chcp 65001 >nul 2>&1
title LMPSmart Setup
python "%~dp0setup.py"
cmd /k
