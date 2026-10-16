# -*- coding: utf-8 -*-
"""
Teste de Validação de Range Requests (HTTP 206) no tools/serve.py
Engenheiro Backend & QA: Agente 2 (Conta 2)
"""

import sys
import os
import io
import time
import threading
import http.client
from pathlib import Path

# UTF-8 stdout
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.system("")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.serve import find_target_dir, find_open_port, CustomPortfolioHandler
from http.server import ThreadingHTTPServer

def run_tests():
    print("\n" + "=" * 65)
    print(" 🧪 TESTE DE VALIDAÇÃO: RANGE REQUESTS (HTTP 206) - tools/serve.py")
    print("=" * 65)

    target_dir = find_target_dir()
    test_port = find_open_port(4500, 4600)
    handler_factory = lambda *args, **kwargs: CustomPortfolioHandler(*args, directory=str(target_dir), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", test_port), handler_factory)

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    passed = 0
    total = 0

    def assert_check(description: str, condition: bool, details: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  \033[92m[OK]\033[0m {description}")
        else:
            print(f"  \033[91m[FALHA]\033[0m {description} - {details}")

    try:
        # Obter tamanho real de index.html
        index_file = target_dir / "index.html"
        index_size = index_file.stat().st_size
        index_bytes = index_file.read_bytes()

        # 1. Requisição Regular GET sem Range (HTTP 200)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("GET", "/index.html")
        res = conn.getresponse()
        data = res.read()
        assert_check("GET padrão retorna HTTP 200", res.status == 200, f"Recebido: {res.status}")
        assert_check("GET padrão contém Accept-Ranges: bytes", res.getheader("Accept-Ranges") == "bytes", f"Recebido: {res.getheader('Accept-Ranges')}")
        assert_check("GET padrão retorna tamanho integral exato", len(data) == index_size, f"Recebido: {len(data)}, Esperado: {index_size}")
        assert_check("Conteúdo do GET padrão é idêntico ao arquivo", data == index_bytes)
        conn.close()

        # 2. Requisição com Range explícito start-end (HTTP 206: bytes=0-99)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("GET", "/index.html", headers={"Range": "bytes=0-99"})
        res = conn.getresponse()
        data = res.read()
        assert_check("Range bytes=0-99 retorna HTTP 206", res.status == 206, f"Recebido: {res.status}")
        assert_check("Header Content-Range correto (bytes 0-99/<total>)", res.getheader("Content-Range") == f"bytes 0-99/{index_size}", f"Recebido: {res.getheader('Content-Range')}")
        assert_check("Header Content-Length igual a 100", res.getheader("Content-Length") == "100", f"Recebido: {res.getheader('Content-Length')}")
        assert_check("Corpo retornado tem exatamente 100 bytes", len(data) == 100, f"Recebido: {len(data)}")
        assert_check("Bytes retornados correspondem aos primeiros 100 bytes do arquivo", data == index_bytes[0:100])
        conn.close()

        # 3. Requisição com Range aberto start- (HTTP 206: bytes=100-)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("GET", "/index.html", headers={"Range": "bytes=100-"})
        res = conn.getresponse()
        data = res.read()
        expected_len = index_size - 100
        assert_check("Range bytes=100- retorna HTTP 206", res.status == 206, f"Recebido: {res.status}")
        assert_check(f"Header Content-Range correto (bytes 100-{index_size - 1}/{index_size})", res.getheader("Content-Range") == f"bytes 100-{index_size - 1}/{index_size}")
        assert_check(f"Header Content-Length igual a {expected_len}", res.getheader("Content-Length") == str(expected_len))
        assert_check("Corpo retornado bate perfeitamente com slice index_bytes[100:]", data == index_bytes[100:])
        conn.close()

        # 4. Requisição com Range sufixo -N (HTTP 206: bytes=-50)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("GET", "/index.html", headers={"Range": "bytes=-50"})
        res = conn.getresponse()
        data = res.read()
        assert_check("Range sufixo bytes=-50 retorna HTTP 206", res.status == 206, f"Recebido: {res.status}")
        assert_check(f"Header Content-Range correto para os últimos 50 bytes", res.getheader("Content-Range") == f"bytes {index_size - 50}-{index_size - 1}/{index_size}")
        assert_check("Header Content-Length igual a 50", res.getheader("Content-Length") == "50")
        assert_check("Corpo retornado bate perfeitamente com os últimos 50 bytes do arquivo", data == index_bytes[-50:])
        conn.close()

        # 5. Requisição com Range insatisfatível além do EOF (HTTP 416)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("GET", "/index.html", headers={"Range": f"bytes={index_size + 1000}-"})
        res = conn.getresponse()
        data = res.read()
        assert_check("Range além do EOF retorna HTTP 416 (Range Not Satisfiable)", res.status == 416, f"Recebido: {res.status}")
        assert_check(f"Header Content-Range para 416 é 'bytes */{index_size}'", res.getheader("Content-Range") == f"bytes */{index_size}", f"Recebido: {res.getheader('Content-Range')}")
        assert_check("Corpo retornado em 416 é vazio", len(data) == 0, f"Recebido: {len(data)}")
        conn.close()

        # 6. Requisição com sintaxe Range inválida (deve ignorar e retornar 200 OK completo conforme RFC)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("GET", "/index.html", headers={"Range": "bytes=invalido"})
        res = conn.getresponse()
        data = res.read()
        assert_check("Range inválido causa fallback para HTTP 200 OK", res.status == 200, f"Recebido: {res.status}")
        assert_check("Conteúdo integral é retornado no fallback", len(data) == index_size)
        conn.close()

        # 7. Requisição HEAD com Range (HTTP 206 sem corpo)
        conn = http.client.HTTPConnection("127.0.0.1", test_port)
        conn.request("HEAD", "/index.html", headers={"Range": "bytes=0-49"})
        res = conn.getresponse()
        data = res.read()
        assert_check("HEAD com Range retorna HTTP 206", res.status == 206, f"Recebido: {res.status}")
        assert_check("HEAD com Range reporta Content-Length 50", res.getheader("Content-Length") == "50")
        assert_check("HEAD com Range reporta Content-Range correto", res.getheader("Content-Range") == f"bytes 0-49/{index_size}")
        assert_check("HEAD não envia dados no corpo (tamanho zero)", len(data) == 0)
        conn.close()

        # 8. Verificação de MIME type para vídeo MP4 e WebM
        assert_check("MIME Type .mp4 mapeado para video/mp4", CustomPortfolioHandler.extensions_map.get(".mp4") == "video/mp4")
        assert_check("MIME Type .webm mapeado para video/webm", CustomPortfolioHandler.extensions_map.get(".webm") == "video/webm")
        assert_check("MIME Type .webp mapeado para image/webp", CustomPortfolioHandler.extensions_map.get(".webp") == "image/webp")

    finally:
        server.shutdown()
        server.server_close()

    print("\n" + "=" * 65)
    print(f" RESULTADO: {passed}/{total} verificações aprovadas ({passed/total*100:.1f}%)")
    print("=" * 65)

    if passed == total:
        print("\033[92m[SUCESSO ABSOLUTO] Servidor tools/serve.py 100% conforme com RFC 7233 (HTTP 206)!\033[0m\n")
        return 0
    else:
        print("\033[91m[FALHA] Algumas verificações falharam.\033[0m\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
