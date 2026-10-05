# -*- coding: utf-8 -*-
"""
Script de Otimização e Conversão de Imagens
Portfólio Cyndy Pimentel
Engenheiro Backend & QA: Agente 2 (Conta 2)
"""

import os
import sys
import io
from pathlib import Path
from PIL import Image

# Configurar stdout para UTF-8 de forma segura no Windows
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

def find_img_dir() -> Path:
    """Localiza o diretório assets/img do projeto."""
    current = Path(__file__).resolve().parent.parent
    candidate_1 = current / "cyndy-portifolio" / "assets" / "img"
    if candidate_1.exists():
        return candidate_1
    candidate_2 = current / "assets" / "img"
    if candidate_2.exists():
        return candidate_2
    raise FileNotFoundError("Diretório assets/img não foi localizado.")

def format_size(bytes_num: int) -> str:
    """Formata bytes em KB legível."""
    return f"{bytes_num / 1024:.1f} KB"

def optimize_and_convert_images(quality: int = 85):
    img_dir = find_img_dir()

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER} 🖼️  OTIMIZAÇÃO & CONVERSÃO DE IMAGENS — WEBP HIGH QUALITY{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"Diretório Alvo : {Colors.YELLOW}{img_dir}{Colors.RESET}")
    print(f"Qualidade WebP : {Colors.BOLD}{quality} (High Fidelity){Colors.RESET}")
    print(f"Modo Fallback  : {Colors.GREEN}Arquivos originais JPG preservados 100% intactos{Colors.RESET}\n")

    # Mapear imagens originais (JPG, JPEG, PNG)
    supported_exts = {'.jpg', '.jpeg', '.png'}
    source_files = [f for f in sorted(img_dir.iterdir()) if f.is_file() and f.suffix.lower() in supported_exts]

    if not source_files:
        print(f"{Colors.RED}Nenhuma imagem suportada encontrada no diretório.{Colors.RESET}")
        return False

    total_orig_size = 0
    total_webp_size = 0
    converted_count = 0

    print(f"{'Arquivo Original':<30} {'Tamanho Orig':<14} {'Tamanho WebP':<14} {'Economia':<10}")
    print(f"{'-'*30} {'-'*14} {'-'*14} {'-'*10}")

    for src_file in source_files:
        orig_size = src_file.stat().st_size
        total_orig_size += orig_size

        dest_file = src_file.with_suffix('.webp')

        try:
            with Image.open(src_file) as im:
                # Se for RGBA ou P, converte de acordo
                if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                    im.save(dest_file, 'WEBP', quality=quality, method=6)
                else:
                    im_rgb = im.convert('RGB')
                    im_rgb.save(dest_file, 'WEBP', quality=quality, method=6)

            webp_size = dest_file.stat().st_size
            total_webp_size += webp_size
            converted_count += 1

            saved_bytes = orig_size - webp_size
            saved_pct = (saved_bytes / orig_size) * 100

            color = Colors.GREEN if saved_bytes > 0 else Colors.YELLOW
            print(f"{src_file.name:<30} {format_size(orig_size):<14} {format_size(webp_size):<14} {color}{saved_pct:+.1f}%{Colors.RESET}")

        except Exception as e:
            print(f"{src_file.name:<30} {Colors.RED}Erro na conversão: {e}{Colors.RESET}")

    total_saved = total_orig_size - total_webp_size
    total_saved_pct = (total_saved / total_orig_size * 100) if total_orig_size > 0 else 0

    print(f"{'-'*68}")
    print(f"{Colors.BOLD}Resumo Geral:{Colors.RESET}")
    print(f"Total de Imagens Mapeadas : {Colors.BOLD}{len(source_files)}{Colors.RESET}")
    print(f"Total Convertidas para WebP: {Colors.BOLD}{Colors.GREEN}{converted_count}{Colors.RESET}")
    print(f"Peso Total Original       : {Colors.BOLD}{format_size(total_orig_size)}{Colors.RESET}")
    print(f"Peso Total em WebP        : {Colors.BOLD}{Colors.GREEN}{format_size(total_webp_size)}{Colors.RESET}")
    print(f"Economia de Banda / Carga : {Colors.BOLD}{Colors.GREEN}{format_size(total_saved)} ({total_saved_pct:.1f}% menor){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}\n")

    return True

if __name__ == '__main__':
    # Aceita parâmetro opcional de qualidade (ex: python tools/optimize_images.py 90)
    q = 88
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        q = int(sys.argv[1])
    
    success = optimize_and_convert_images(quality=q)
    sys.exit(0 if success else 1)
