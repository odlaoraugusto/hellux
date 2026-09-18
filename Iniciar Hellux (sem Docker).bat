@echo off
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
    echo Criando ambiente Python do backend pela primeira vez...
    python -m venv backend\.venv
)

echo Instalando/atualizando dependencias do backend...
backend\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt

if not exist "backend\.env" (
    echo Copiando configuracao padrao do backend...
    copy backend\.env.example backend\.env >nul
)

if not exist "frontend\.env" (
    echo Copiando configuracao padrao do frontend...
    copy frontend\.env.example frontend\.env >nul
)

echo Aplicando migracoes do banco...
pushd backend
.venv\Scripts\python.exe -m alembic upgrade head
popd

if not exist "frontend\node_modules" (
    echo Instalando dependencias do frontend pela primeira vez...
    pushd frontend
    call npm install
    popd
)

echo Ligando o backend...
start "Hellux - Backend (feche esta janela para desligar)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Ligando o frontend...
start "Hellux - Frontend (feche esta janela para desligar)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Aguardando o backend responder...
:esperar
timeout /t 2 /nobreak >nul
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/health > "%TEMP%\hellux_health.txt"
set /p HTTP_CODE=<"%TEMP%\hellux_health.txt"
if not "%HTTP_CODE%"=="200" goto esperar

echo Pronto! Abrindo no navegador...
start http://localhost:5173
exit
