@echo off
title 2 Agentes — Monitor & Orquestrador Autonomo
color 0B
chcp 65001 >nul

echo ============================================================
echo         2 AGENTES - MISSION CONTROL & ORQUESTRADOR
echo ============================================================
echo.

set SCRIPT_DIR=E:\Projetos\2 agentes\
set TARGET_DIR=%~1

if "%TARGET_DIR%"=="" (
    set TARGET_DIR=%CD%
    echo [*] Monitorando diretorio atual: %TARGET_DIR%
) else (
    echo [*] Diretorio alvo recebido: %TARGET_DIR%
)

echo.
echo [*] Conectando ao painel em http://127.0.0.1:8000/ ...
start "" "http://127.0.0.1:8000/"

:: Tenta alternar o projeto via API caso o servidor ja esteja rodando
python -c "import urllib.request, json; req = urllib.request.Request('http://127.0.0.1:8000/api/project/switch', data=json.dumps({'target_dir': r'%TARGET_DIR%'}).encode(), headers={'Content-Type': 'application/json'}); urllib.request.urlopen(req, timeout=1); print('[*] Projeto alternado com sucesso no servidor ativo!')" 2>nul

if %ERRORLEVEL% EQU 0 (
    echo [*] O monitor ja estava ativo em segundo plano e foi sincronizado com este projeto!
    timeout /t 3 >nul
    exit /b 0
)

echo [*] Servidor nao estava ativo. Iniciando novo processo do servidor...
python "%SCRIPT_DIR%src\monitor\server.py" --port 8000 --target "%TARGET_DIR%"

pause
