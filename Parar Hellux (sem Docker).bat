@echo off
echo Desligando o Hellux (backend e frontend)...

for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%p >nul 2>&1

echo Pronto. Pode fechar as janelas do backend/frontend se ainda estiverem abertas.
timeout /t 2 /nobreak >nul
exit
