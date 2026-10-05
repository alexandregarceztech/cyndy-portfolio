# -*- coding: utf-8 -*-
"""
Utilitário de Servidor Local & Live Reload
Portfólio Cyndy Pimentel
Engenheiro Backend & QA: Agente 2 (Conta 2)
"""

import os
import sys
import io
import socket
import webbrowser
import threading
import time
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Forçar stdout para UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.system("")

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def find_target_dir():
    """Detecta o diretório correto contendo o index.html."""
    current = Path(__file__).resolve().parent.parent
    if (current / "cyndy-portifolio" / "index.html").exists():
        return current / "cyndy-portifolio"
    if (current / "index.html").exists():
        return current
    raise FileNotFoundError("Diretório com index.html não localizado.")

def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Verifica se a porta está livre para uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) != 0

def find_open_port(start_port: int = 3000, max_port: int = 3010) -> int:
    """Encontra uma porta disponível a partir de start_port."""
    for p in range(start_port, max_port + 1):
        if is_port_available(p):
            return p
    return start_port

class CustomPortfolioHandler(SimpleHTTPRequestHandler):
    """Handler customizado com cabeçalhos adequados e sem cache excessivo."""

    def end_headers(self):
        # Desativar cache durante desenvolvimento local para refletir alterações imediatas
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # Habilitar CORS caso assets ou fontes externas sejam consumidas
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        # Log limpo e colorido de requisições
        status_code = args[1] if len(args) > 1 else '200'
        color = Colors.GREEN if str(status_code).startswith('2') else Colors.YELLOW
        sys.stdout.write(f"  {color}[HTTP {status_code}]{Colors.RESET} {args[0]}\n")
        sys.stdout.flush()

def start_server(port: int = 3000, open_browser: bool = True):
    target_dir = find_target_dir()
    chosen_port = find_open_port(port)
    url = f"http://localhost:{chosen_port}"

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER} 🚀 SERVIDOR LOCAL DE DESENVOLVIMENTO — CYNDY PIMENTEL{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}")
    print(f"Diretório Raiz  : {Colors.YELLOW}{target_dir}{Colors.RESET}")
    print(f"URL Local       : {Colors.BOLD}{Colors.GREEN}{url}{Colors.RESET}")
    print(f"Encerramento    : Pressione {Colors.BOLD}Ctrl + C{Colors.RESET} para finalizar.")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}\n")

    os.chdir(str(target_dir))

    handler_factory = lambda *args, **kwargs: CustomPortfolioHandler(*args, directory=str(target_dir), **kwargs)
    httpd = ThreadingHTTPServer(("127.0.0.1", chosen_port), handler_factory)

    if open_browser:
        def launch_browser():
            time.sleep(0.8)
            print(f"{Colors.BLUE}🌐 Abrindo navegador padrão em {url} ...{Colors.RESET}\n")
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"{Colors.YELLOW}Não foi possível abrir o navegador automaticamente: {e}{Colors.RESET}")

        threading.Thread(target=launch_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Servidor encerrado suavemente pelo usuário (Ctrl + C). Até logo!{Colors.RESET}")
    finally:
        httpd.server_close()

if __name__ == '__main__':
    # Aceita parâmetro opcional de porta (ex: python tools/serve.py 3000)
    # Suporta flag --no-browser para testes automatizados
    p = 3000
    auto_open = True
    for arg in sys.argv[1:]:
        if arg.isdigit():
            p = int(arg)
        elif arg == '--no-browser':
            auto_open = False

    start_server(port=p, open_browser=auto_open)
