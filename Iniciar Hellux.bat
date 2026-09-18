@echo off
title Hellux
cd /d "%~dp0"

echo Ligando o Hellux...
docker compose up -d

echo Aguardando o backend responder...
:esperar
timeout /t 2 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/health > "%TEMP%\hellux_health.txt"
set /p HTTP_CODE=<"%TEMP%\hellux_health.txt"
if not "%HTTP_CODE%"=="200" goto esperar

echo Pronto! Abrindo no navegador...
start http://localhost:5173

timeout /t 3 /nobreak >nul
exit
