# -*- coding: utf-8 -*-
"""
Utilitário de Servidor Local & Live Reload
Portfólio Cyndy Pimentel
Engenheiro Backend & QA: Agente 2 (Conta 2)
"""

import os
import sys
import io
import re
import socket
import webbrowser
import threading
import time
import email.utils
import datetime
import urllib.parse
from pathlib import Path
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Configurar stdout para UTF-8 no Windows de forma segura
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
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

class BoundedFileReader:
    """Wrapper para streaming delimitado de arquivo binário limitado a `length` bytes."""

    def __init__(self, file_obj, length: int):
        self.file_obj = file_obj
        self.remaining = length

    def read(self, size: int = -1):
        if self.remaining <= 0:
            return b""
        if size is None or size < 0 or size > self.remaining:
            to_read = self.remaining
        else:
            to_read = size
        chunk = self.file_obj.read(to_read)
        self.remaining -= len(chunk)
        return chunk

    def close(self):
        if hasattr(self.file_obj, "close"):
            self.file_obj.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, name):
        return getattr(self.file_obj, name)

class CustomPortfolioHandler(SimpleHTTPRequestHandler):
    """Handler customizado com suporte nativo a HTTP 206 (Range Requests), anti-cache e logging limpo."""

    extensions_map = SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.ogv': 'video/ogg',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.wasm': 'application/wasm',
        '.json': 'application/json',
    })

    def end_headers(self):
        # Desativar cache durante desenvolvimento local para refletir alterações imediatas
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # Habilitar CORS caso assets ou fontes externas sejam consumidas
        self.send_header('Access-Control-Allow-Origin', '*')
        # Anunciar explicitamente suporte a Range Requests
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def copyfile(self, source, outputfile):
        """Copia dados com tolerância a desconexões normais de streaming (scrubbing ou abort do cliente)."""
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except OSError as e:
            if getattr(e, 'winerror', None) in (10053, 10054):
                pass
            else:
                raise

    def log_message(self, format, *args):
        # Log limpo e colorido de requisições
        status_code = str(args[1]) if len(args) > 1 else '200'
        if status_code.startswith('2'):
            color = Colors.GREEN
        elif status_code.startswith('3'):
            color = Colors.CYAN
        elif status_code.startswith(('4', '5')):
            color = Colors.RED
        else:
            color = Colors.YELLOW
        sys.stdout.write(f"  {color}[HTTP {status_code}]{Colors.RESET} {args[0]}\n")
        sys.stdout.flush()

    def send_head(self):
        """Implementação com suporte nativo a HTTP 206 Partial Content (RFC 7233)."""
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/', parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            for index in self.index_pages:
                index_path = os.path.join(path, index)
                if os.path.isfile(index_path):
                    path = index_path
                    break
            else:
                return self.list_directory(path)

        ctype = self.guess_type(path)
        if path.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            total_size = fs.st_size

            # Verificação de cache condicional (If-Modified-Since)
            if "If-Modified-Since" in self.headers and "If-None-Match" not in self.headers:
                try:
                    ims = email.utils.parsedate_to_datetime(self.headers["If-Modified-Since"])
                except (TypeError, IndexError, OverflowError, ValueError):
                    pass
                else:
                    if ims.tzinfo is None:
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    if ims.tzinfo is datetime.timezone.utc:
                        last_modif = datetime.datetime.fromtimestamp(fs.st_mtime, datetime.timezone.utc).replace(microsecond=0)
                        if last_modif <= ims:
                            self.send_response(HTTPStatus.NOT_MODIFIED)
                            self.end_headers()
                            f.close()
                            return None

            # Interceptação de Range Requests (HTTP 206)
            range_header = self.headers.get("Range")
            if range_header:
                range_match = re.match(r"^bytes=\s*(\d*)\s*-\s*(\d*)\s*$", range_header.strip())
                if range_match:
                    start_str, end_str = range_match.groups()
                    if start_str or end_str:
                        if start_str and end_str:
                            start = int(start_str)
                            end = int(end_str)
                            if end >= total_size:
                                end = total_size - 1
                        elif start_str:
                            start = int(start_str)
                            end = total_size - 1
                        else:  # Suffix byte range: bytes=-N
                            suffix = int(end_str)
                            if suffix <= 0:
                                start = total_size
                                end = total_size - 1
                            else:
                                start = max(0, total_size - suffix)
                                end = total_size - 1

                        # Range inválido ou insatisfatível conforme RFC 7233
                        if total_size == 0 or start > end or start >= total_size or start < 0:
                            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                            self.send_header("Content-Range", f"bytes */{total_size}")
                            self.send_header("Content-Length", "0")
                            self.end_headers()
                            f.close()
                            return None

                        # Emissão do cabeçalho HTTP 206 Partial Content
                        content_length = end - start + 1
                        self.send_response(HTTPStatus.PARTIAL_CONTENT)
                        self.send_header("Content-Type", ctype)
                        self.send_header("Content-Range", f"bytes {start}-{end}/{total_size}")
                        self.send_header("Content-Length", str(content_length))
                        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                        self.end_headers()

                        f.seek(start)
                        return BoundedFileReader(f, content_length)

            # Resposta completa HTTP 200 OK
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(total_size))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise

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
