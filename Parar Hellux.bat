@echo off
title Hellux
cd /d "%~dp0"

echo Desligando o Hellux...
docker compose stop

echo Pronto.
timeout /t 2 /nobreak >nul
exit
