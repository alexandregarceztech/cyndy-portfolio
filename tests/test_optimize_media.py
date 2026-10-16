# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados para tools/optimize_media.py
Portfólio Cyndy Pimentel
Engenheiro Backend & QA: Agente 2 (Conta 2)

Testa:
  1. Detecção automática e caminhos de busca do binário FFmpeg.
  2. Parser binário de verificação de átomo 'moov' (+faststart HTTP 206).
  3. Geração adaptativa de posters WebP com teto estrito de 25 KB.
  4. Validação de integridade dos 6 vídeos do catálogo no Performance Budget (<= 4.0 MB).
  5. Função de auditoria automatizada (audit_media).
  6. Argumentos de linha de comando CLI (--help, --check, --posters).
"""

import os
import sys
import io
import shutil
import tempfile
import subprocess
from pathlib import Path
from PIL import Image

# Configuração segura de saída UTF-8 no Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.system("")

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from tools.optimize_media import (
    find_ffmpeg,
    check_mp4_faststart,
    generate_poster_from_image,
    audit_media,
    find_ffprobe,
    MAX_POSTER_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
    REELS_CATALOG
)

passed = 0
failed = 0

def check(name: str, condition: bool, extra: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} {name} {Colors.DIM}{extra}{Colors.RESET}")
    else:
        failed += 1
        print(f"  {Colors.RED}[FAIL]{Colors.RESET} {name} {Colors.RED}{extra}{Colors.RESET}")

def test_ffmpeg_detection():
    print(f"\n{Colors.BOLD}{Colors.CYAN}1. Teste de Detecção do FFmpeg:{Colors.RESET}")
    ffmpeg_bin = find_ffmpeg()
    check("FFmpeg localizado no ambiente", ffmpeg_bin is not None, f"-> {ffmpeg_bin}")
    if ffmpeg_bin:
        check("Binário FFmpeg é executável e existe", ffmpeg_bin.is_file())
        res = subprocess.run([str(ffmpeg_bin), "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        check("FFmpeg responde ao comando -version", res.returncode == 0, f"(exit code {res.returncode})")

def test_faststart_parser():
    print(f"\n{Colors.BOLD}{Colors.CYAN}2. Teste do Parser Binário de +faststart (moov atom):{Colors.RESET}")
    videos_dir = ROOT_DIR / "assets" / "videos"
    v1 = videos_dir / "video-01.mp4"
    if v1.is_file():
        is_fs, msg = check_mp4_faststart(v1)
        check("video-01.mp4 possui 'moov' antes de 'mdat'", is_fs, f"({msg})")

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        f.write(b"CORRUPTED_NON_MP4_HEADER_DATA")
        tmp_name = Path(f.name)
    try:
        is_fs_bad, msg_bad = check_mp4_faststart(tmp_name)
        check("Rejeita arquivo corrompido sem moov", not is_fs_bad, f"({msg_bad})")
    finally:
        if tmp_name.exists():
            tmp_name.unlink()

def test_poster_adaptive_budget():
    print(f"\n{Colors.BOLD}{Colors.CYAN}3. Teste de Posters WebP (< 25 KB):{Colors.RESET}")
    img_dir = ROOT_DIR / "assets" / "img"
    for reel in REELS_CATALOG:
        poster_file = img_dir / reel["poster_name"]
        check(f"Poster existe: {reel['poster_name']}", poster_file.is_file())
        if poster_file.is_file():
            sz = poster_file.stat().st_size
            check(f"Tamanho de {reel['poster_name']} <= 25 KB", sz <= MAX_POSTER_SIZE_BYTES, f"({sz/1024:.1f} KB)")
            with Image.open(poster_file) as im:
                check(f"Formato WebP válido: {reel['poster_name']}", im.format == "WEBP", f"(size: {im.size})")

def test_video_performance_budget():
    print(f"\n{Colors.BOLD}{Colors.CYAN}4. Teste de Vídeos Verticais (Performance Budget <= 4.0 MB):{Colors.RESET}")
    videos_dir = ROOT_DIR / "assets" / "videos"
    for reel in REELS_CATALOG:
        v_file = videos_dir / reel["video_name"]
        check(f"Vídeo presente: {reel['video_name']}", v_file.is_file())
        if v_file.is_file():
            sz = v_file.stat().st_size
            check(f"Tamanho de {reel['video_name']} <= 4.0 MB", sz <= MAX_VIDEO_SIZE_BYTES, f"({sz/(1024*1024):.2f} MB)")
            is_fs, _ = check_mp4_faststart(v_file)
            check(f"+faststart ativo em {reel['video_name']}", is_fs)

def test_audit_function():
    print(f"\n{Colors.BOLD}{Colors.CYAN}5. Teste da Função audit_media():{Colors.RESET}")
    result = audit_media(ROOT_DIR)
    check("audit_media() retorna True com 100% de aprovação", result is True)

def test_cli_execution():
    print(f"\n{Colors.BOLD}{Colors.CYAN}6. Teste de Execução CLI de tools/optimize_media.py:{Colors.RESET}")
    py_bin = sys.executable
    script_path = ROOT_DIR / "tools" / "optimize_media.py"

    res_help = subprocess.run([py_bin, str(script_path), "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    check("CLI responde a --help com código 0", res_help.returncode == 0)

    res_check = subprocess.run([py_bin, str(script_path), "--check"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    check("CLI responde a --check com código 0 (audit 100%)", res_check.returncode == 0)

def test_audio_and_motion():
    print(f"\n{Colors.BOLD}{Colors.CYAN}7. Teste de Áudio Dinâmico & Streams de Vídeo (Tarefa #019):{Colors.RESET}")
    videos_dir = ROOT_DIR / "assets" / "videos"
    ffprobe_bin = find_ffprobe()
    check("ffprobe disponível para auditoria de streams", ffprobe_bin is not None and ffprobe_bin.is_file())

    if ffprobe_bin and ffprobe_bin.is_file():
        for reel in REELS_CATALOG:
            v_file = videos_dir / reel["video_name"]
            if not v_file.is_file():
                continue
            
            # Checa stream de áudio
            p_audio = subprocess.run([
                str(ffprobe_bin), '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,channels,sample_rate,duration',
                '-of', 'default=noprint_wrappers=1',
                str(v_file)
            ], capture_output=True, text=True)

            out_audio = p_audio.stdout.strip()
            check(f"Stream de áudio presente em {reel['video_name']}", "codec_name=aac" in out_audio)
            check(f"Canais estéreo (2) em {reel['video_name']}", "channels=2" in out_audio)
            check(f"Sample rate 44100 Hz em {reel['video_name']}", "sample_rate=44100" in out_audio)

            # Checa stream de vídeo
            p_video = subprocess.run([
                str(ffprobe_bin), '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_name,width,height',
                '-of', 'default=noprint_wrappers=1',
                str(v_file)
            ], capture_output=True, text=True)
            out_video = p_video.stdout.strip()
            check(f"Vídeo vertical 720x1280 em {reel['video_name']}", "width=720" in out_video and "height=1280" in out_video)

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER} 🧪 SUÍTE DE TESTES AUTOMATIZADOS: tools/optimize_media.py{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")

    test_ffmpeg_detection()
    test_faststart_parser()
    test_poster_adaptive_budget()
    test_video_performance_budget()
    test_audit_function()
    test_cli_execution()
    test_audio_and_motion()

    total = passed + failed
    pct = (passed / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}{'='*68}{Colors.RESET}")
    print(f"{Colors.BOLD}RESULTADO DOS TESTES:{Colors.RESET}")
    print(f"Total de Asserções  : {Colors.BOLD}{total}{Colors.RESET}")
    print(f"Aprovadas           : {Colors.BOLD}{Colors.GREEN}{passed}{Colors.RESET}")
    print(f"Reprovadas          : {Colors.BOLD}{Colors.RED if failed else Colors.GREEN}{failed}{Colors.RESET}")
    print(f"Taxa de Aprovação   : {Colors.BOLD}{Colors.GREEN if failed == 0 else Colors.RED}{pct:.1f}%{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*68}{Colors.RESET}\n")

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
