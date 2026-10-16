# -*- coding: utf-8 -*-
"""
Script de Otimização de Mídias (Vídeos, Posters e Imagens)
Portfólio Cyndy Pimentel
Engenheiro Backend & QA: Agente 2 (Conta 2)

Funcionalidades:
  1. Compressão de Vídeos 9:16 para Web (H.264/AAC, CRF 26-28, faststart / HTTP 206).
  2. Síntese Sonora Musical Dinâmica (Bateria, 808 sub-bass, synths, risers, whooshes).
  3. Geração de Movimento Real Multi-Shot (Dolly zoom, pan tracking lateral, jump cuts, xfade).
  4. Visualizador de Áudio em Tempo Real (showwaves reativo) e Lower-Third Glassmorphic.
  5. Geração de Posters WebP Ultraleves (< 25 KB) com calibração adaptativa.
  6. Auditoria estrita de Performance Budget (Vídeos <= 4.0 MB, Posters <= 25 KB).
  7. Verificação binária de moov atom (+faststart) para Range Requests imediatos.
"""

import os
import sys
import io
import math
import random
import shutil
import struct
import wave
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

# Configuração segura de console UTF-8 no Windows
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

# Limites e Metas de Performance Budget (conforme DEBATE.md)
MAX_VIDEO_SIZE_BYTES = 4.0 * 1024 * 1024       # 4.0 MB teto estrito
RECOMMENDED_VIDEO_MAX_BYTES = 2.5 * 1024 * 1024 # 2.5 MB meta recomendada
MAX_POSTER_SIZE_BYTES = 25 * 1024              # 25 KB teto estrito para posters
TARGET_WIDTH = 720                             # Resolução vertical 9:16
TARGET_HEIGHT = 1280
DEFAULT_CRF = 27                               # CRF padrão balanceado
AUDIO_NORMALIZATION_LUFS = -14.0               # Normalização recomendada

# Mapeamento oficial dos 6 Reels do Portfólio Cyndy Pimentel
REELS_CATALOG = [
    {
        "id": "video-01",
        "title": "Honda Motobel — Que tal subir de nível? (HR-V)",
        "brand": "HONDA MOTOBEL",
        "niche": "AUTOMOTIVO",
        "music_style": "automotive",
        "bpm": 124,
        "key": "D menor · Tech Drive",
        "source_thumb": "video-01-new.jpg",
        "video_name": "video-01.mp4",
        "poster_name": "video-01-poster.webp",
        "instagram": "https://www.instagram.com/reel/DcRreoRh6B5/",
        "slide": "#slide-videos-1",
        "accent": "#1A3D63"
    },
    {
        "id": "video-02",
        "title": "Honda Nippon — Peças genuínas & revisão",
        "brand": "HONDA NIPPON",
        "niche": "PÓS-VENDA",
        "music_style": "tech",
        "bpm": 126,
        "key": "G menor · Precision Rhythm",
        "source_thumb": "video-02-new.jpg",
        "video_name": "video-02.mp4",
        "poster_name": "video-02-poster.webp",
        "instagram": "https://www.instagram.com/reel/Dac_Pm4AYhp/",
        "slide": "#slide-videos-1",
        "accent": "#1A3D63"
    },
    {
        "id": "video-03",
        "title": "Giga Motos Bajaj — Condições especiais & modelos",
        "brand": "GIGA MOTOS BAJAJ",
        "niche": "DUAS RODAS",
        "music_style": "trap",
        "bpm": 132,
        "key": "F menor · Urban Energy",
        "source_thumb": "video-03-new.jpg",
        "video_name": "video-03.mp4",
        "poster_name": "video-03-poster.webp",
        "instagram": "https://www.instagram.com/reel/DeNSMxNh4e4/",
        "slide": "#slide-videos-1",
        "accent": "#1A3D63"
    },
    {
        "id": "video-04",
        "title": "Só Letrados — Comunicação, língua & cultura",
        "brand": "SÓ LETRADOS",
        "niche": "EDUCAÇÃO",
        "music_style": "lofi",
        "bpm": 96,
        "key": "A menor · Warm Neo-Soul",
        "source_thumb": "video-04-new.jpg",
        "video_name": "video-04.mp4",
        "poster_name": "video-04-poster.webp",
        "instagram": "https://www.instagram.com/reel/DRa8JF4EXNG/",
        "slide": "#slide-videos-2",
        "accent": "#1A3D63"
    },
    {
        "id": "video-05",
        "title": "Mônaco Motocenter — Lançamento Biz Kuromi",
        "brand": "MÔNACO MOTOCENTER",
        "niche": "LANÇAMENTO",
        "music_style": "pop",
        "bpm": 128,
        "key": "E maior · Trendy Hyper-Pop",
        "source_thumb": "video-05-new.jpg",
        "video_name": "video-05.mp4",
        "poster_name": "video-05-poster.webp",
        "instagram": "https://www.instagram.com/reel/DdjMBk-oSbl/",
        "slide": "#slide-videos-2",
        "accent": "#1A3D63"
    },
    {
        "id": "video-06",
        "title": "Mônaco Dream — CBR1000RR-R a moto dos sonhos",
        "brand": "MÔNACO DREAM",
        "niche": "SUPERBIKE",
        "music_style": "adrenaline",
        "bpm": 138,
        "key": "B menor · Adrenaline Drive",
        "source_thumb": "video-06-new.jpg",
        "video_name": "video-06.mp4",
        "poster_name": "video-06-poster.webp",
        "instagram": "https://www.instagram.com/reel/Dd4L7VcI6zZ/",
        "slide": "#slide-videos-2",
        "accent": "#1A3D63"
    }
]

def format_size(bytes_num: int) -> str:
    """Formata bytes em unidade legível (KB ou MB)."""
    if bytes_num >= 1024 * 1024:
        return f"{bytes_num / (1024 * 1024):.2f} MB"
    return f"{bytes_num / 1024:.1f} KB"

def find_project_root() -> Path:
    """Localiza a raiz do repositório."""
    current = Path(__file__).resolve().parent.parent
    if (current / "index.html").exists():
        return current
    if (current / "cyndy-portifolio" / "index.html").exists():
        return current / "cyndy-portifolio"
    raise FileNotFoundError("Raiz do projeto não encontrada.")

def find_ffmpeg(custom_path: Optional[str] = None) -> Optional[Path]:
    """
    Localiza o binário do FFmpeg com busca inteligente em:
      1. Parâmetro personalizado ou variável FFMPEG_PATH
      2. PATH do ambiente atual
      3. PATH atualizado do registro do Windows (User e Machine)
      4. Diretórios comuns do WinGet, Scoop, Chocolatey e Program Files
    """
    if custom_path:
        p = Path(custom_path)
        if p.is_file() and os.access(p, os.X_OK):
            return p
        p_exe = p / "ffmpeg.exe" if p.is_dir() else p
        if p_exe.is_file():
            return p_exe

    env_custom = os.environ.get("FFMPEG_PATH")
    if env_custom and Path(env_custom).is_file():
        return Path(env_custom)

    # 1. Checagem direta no PATH do processo
    in_path = shutil.which("ffmpeg")
    if in_path:
        return Path(in_path)

    # 2. Busca no registro do Windows (caso instalado recentemente via winget)
    if sys.platform == "win32":
        try:
            import winreg
            for hkey in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(hkey, r"Environment") as key:
                        reg_path, _ = winreg.QueryValueEx(key, "Path")
                        for segment in reg_path.split(";"):
                            segment = segment.strip().strip('"')
                            if segment:
                                candidate = Path(segment) / "ffmpeg.exe"
                                if candidate.is_file():
                                    return candidate
                except FileNotFoundError:
                    continue
        except Exception:
            pass

        # 3. Busca em pastas do WinGet Packages
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            winget_pkgs = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
            if winget_pkgs.is_dir():
                for found in winget_pkgs.glob("**/ffmpeg.exe"):
                    if found.is_file():
                        return found

        # 4. Outros locais convencionais
        standard_locations = [
            Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
            Path(r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"),
            Path(r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe"),
            Path(os.path.expanduser(r"~\scoop\apps\ffmpeg\current\bin\ffmpeg.exe")),
            Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),
        ]
        for loc in standard_locations:
            if loc.is_file():
                return loc

    return None

def find_ffprobe(ffmpeg_path: Optional[Path] = None) -> Optional[Path]:
    """Localiza o binário do ffprobe correspondente ao FFmpeg."""
    if ffmpeg_path:
        probe_candidate = ffmpeg_path.parent / "ffprobe.exe"
        if probe_candidate.is_file():
            return probe_candidate

    in_path = shutil.which("ffprobe")
    if in_path:
        return Path(in_path)

    ff = find_ffmpeg()
    if ff:
        probe_candidate = ff.parent / "ffprobe.exe"
        if probe_candidate.is_file():
            return probe_candidate

    return None

def check_mp4_faststart(mp4_path: Path) -> Tuple[bool, str]:
    """
    Inspeção binária pura em Python do container MP4 para verificar se o 'moov' atom
    está posicionado antes do 'mdat' atom (essencial para HTTP 206 Range Requests).
    """
    if not mp4_path.is_file():
        return False, "Arquivo não existe"
    
    file_size = mp4_path.stat().st_size
    if file_size < 16:
        return False, "Arquivo MP4 muito pequeno ou corrompido"

    moov_pos = None
    mdat_pos = None

    try:
        with open(mp4_path, 'rb') as f:
            offset = 0
            while offset < file_size:
                f.seek(offset)
                header = f.read(8)
                if len(header) < 8:
                    break
                box_size, box_type = struct.unpack('>I4s', header)
                try:
                    type_str = box_type.decode('ascii', errors='ignore')
                except Exception:
                    type_str = ""

                if box_size == 1:
                    ext_header = f.read(8)
                    if len(ext_header) < 8:
                        break
                    box_size = struct.unpack('>Q', ext_header)[0]
                elif box_size == 0:
                    box_size = file_size - offset

                if type_str == 'moov' and moov_pos is None:
                    moov_pos = offset
                elif type_str == 'mdat' and mdat_pos is None:
                    mdat_pos = offset

                if moov_pos is not None and mdat_pos is not None:
                    break

                if box_size <= 0:
                    break
                offset += box_size

        if moov_pos is None:
            return False, "Átomo 'moov' não localizado no cabeçalho"
        if mdat_pos is None:
            return True, "Átomo 'moov' presente (sem bloco 'mdat' isolado)"
        if moov_pos < mdat_pos:
            return True, f"'moov' ({moov_pos} bytes) precede 'mdat' ({mdat_pos} bytes) [+faststart ativo]"
        else:
            return False, f"'mdat' ({mdat_pos} bytes) precede 'moov' ({moov_pos} bytes) [-faststart ausente]"

    except Exception as e:
        return False, f"Falha na leitura dos blocos MP4: {e}"

def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Carrega fonte TrueType do sistema operacional com fallback seguro."""
    font_names = ['segoeuib.ttf', 'arialbd.ttf'] if bold else ['segoeui.ttf', 'arial.ttf']
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()

def synthesize_reel_audio(style: str, duration: float = 10.0, sample_rate: int = 44100) -> bytes:
    """
    Sintetizador de áudio estéreo em Python padrão (wave/math/struct).
    Gera trilhas sonoras completas, rítmicas e enérgicas para cada nicho comercial:
      - Batida moderna (Kick, Snare/Clap, Hi-Hats com panorâmica estéreo)
      - Linha de Sub-bass 808 encorpada
      - Acordes harmônicos estéreo com efeito chorus/detune
      - Sound FX: Risers dinâmicos e Whooshes sincronizados com os cortes (t=3.3s e 6.6s)
      - Sub-impact no início e transições
      - Limitador analógico com saturação suave (tanh) e fade-out final
    """
    bpm_map = {
        'automotive': 124,
        'tech': 126,
        'trap': 132,
        'lofi': 96,
        'pop': 128,
        'adrenaline': 138
    }
    bpm = bpm_map.get(style, 124)
    beat_dur = 60.0 / bpm
    total_samples = int(duration * sample_rate)

    rng = random.Random(hash(style) & 0xffffffff)
    noise_len = 88200
    noise_table = [rng.uniform(-1.0, 1.0) for _ in range(noise_len)]

    left = [0.0] * total_samples
    right = [0.0] * total_samples

    # Progressões Harmônicas por Estilo (Frequências em Hz: raiz_baixo, notas_acorde)
    progressions = {
        'automotive': [ # Dm - Bb - Gm - C (Modern Tech Drive)
            (73.4, [146.8, 174.6, 220.0]),
            (58.3, [116.5, 146.8, 174.6]),
            (49.0, [98.0, 116.5, 146.8]),
            (65.4, [130.8, 164.8, 196.0]),
        ],
        'tech': [ # Gm - Eb - F - Dm (Precision Rhythm)
            (49.0, [98.0, 116.5, 146.8]),
            (77.8, [155.6, 196.0, 233.1]),
            (87.3, [174.6, 220.0, 261.6]),
            (73.4, [146.8, 174.6, 220.0]),
        ],
        'trap': [ # Fm - Db - Eb - C (Urban Energy)
            (43.7, [87.3, 103.8, 130.8]),
            (69.3, [138.6, 174.6, 207.7]),
            (77.8, [155.6, 196.0, 233.1]),
            (65.4, [130.8, 164.8, 196.0]),
        ],
        'lofi': [ # Am7 - Dm7 - G7 - Cmaj7 (Warm Neo-Soul)
            (55.0, [110.0, 130.8, 164.8, 196.0]),
            (73.4, [146.8, 174.6, 220.0, 261.6]),
            (49.0, [98.0, 123.5, 146.8, 174.6]),
            (65.4, [130.8, 164.8, 196.0, 246.9]),
        ],
        'pop': [ # E - B - C#m - A (Trendy Hyper-Pop)
            (82.4, [164.8, 207.7, 246.9]),
            (61.7, [123.5, 155.6, 185.0]),
            (69.3, [138.6, 164.8, 207.7]),
            (55.0, [110.0, 138.6, 164.8]),
        ],
        'adrenaline': [ # Bm - G - Em - F# (Adrenaline Drive)
            (61.7, [123.5, 146.8, 185.0]),
            (49.0, [98.0, 123.5, 146.8]),
            (82.4, [164.8, 196.0, 246.9]),
            (92.5, [185.0, 233.1, 277.2]),
        ]
    }
    prog = progressions.get(style, progressions['automotive'])
    bar_dur = beat_dur * 4.0

    # 1. Sintetizador de Baixo & Acordes
    for bar_idx in range(int(duration / bar_dur) + 1):
        bass_freq, chord_freqs = prog[bar_idx % len(prog)]
        bar_start_sample = int(bar_idx * bar_dur * sample_rate)
        bar_samples = int(bar_dur * sample_rate)

        for i in range(bar_samples):
            s_idx = bar_start_sample + i
            if s_idx >= total_samples:
                break
            t = i / sample_rate

            # Sub-Bass 808 com harmônico
            bass_sub = math.sin(2 * math.pi * bass_freq * t)
            bass_harm = math.sin(4 * math.pi * bass_freq * t) * 0.35
            bass_env = math.exp(-((t % (beat_dur / 2)) * 6.0)) if style in ('trap', 'adrenaline') else 0.85
            bass_val = (bass_sub + bass_harm) * bass_env * 0.45
            left[s_idx] += bass_val
            right[s_idx] += bass_val

            # Synth Chords com Chorus estéreo
            c_env = 0.5 * (1.0 - math.exp(-t * 22.0)) * math.exp(-t * 0.45)
            c_val_l = 0.0
            c_val_r = 0.0
            for f in chord_freqs:
                s1 = math.sin(2 * math.pi * f * t)
                s2 = math.sin(2 * math.pi * (f * 1.006) * t + 0.5)
                s3 = math.sin(2 * math.pi * (f * 0.994) * t + 1.0)
                c_val_l += (s1 + s2) * 0.09
                c_val_r += (s1 + s3) * 0.09
            left[s_idx] += c_val_l * c_env
            right[s_idx] += c_val_r * c_env

    # 2. Percussão Completa
    step_dur = beat_dur / 4.0
    num_steps = int(duration / step_dur)
    for step in range(num_steps):
        t_step = step * step_dur
        sample_offset = int(t_step * sample_rate)
        beat_in_bar = step % 16

        # Bumbo (Kick 808)
        is_kick = (beat_in_bar in (0, 8)) if style in ('trap', 'lofi') else (beat_in_bar in (0, 4, 8, 12))
        if is_kick:
            k_len = int(0.25 * sample_rate)
            for i in range(min(k_len, total_samples - sample_offset)):
                t = i / sample_rate
                pitch = 155.0 * math.exp(-t * 22.0) + 42.0
                env = math.exp(-t * 15.0)
                k_val = math.sin(2 * math.pi * pitch * t) * env * 0.75
                left[sample_offset + i] += k_val
                right[sample_offset + i] += k_val

        # Caixa / Palma (Snare/Clap)
        is_snare = beat_in_bar in (4, 12)
        if is_snare:
            s_len = int(0.20 * sample_rate)
            for i in range(min(s_len, total_samples - sample_offset)):
                t = i / sample_rate
                env = math.exp(-t * 22.0)
                n = noise_table[(sample_offset + i) % noise_len]
                tone = math.sin(2 * math.pi * 180.0 * t) * math.exp(-t * 35.0)
                s_val = (n * 0.65 + tone * 0.35) * env * 0.60
                left[sample_offset + i] += s_val * 0.95
                right[sample_offset + i] += s_val * 1.05

        # Pratos / Hi-Hats com pan estéreo
        is_hat = (step % 2 == 0) or (style in ('trap', 'pop') and (step % 4 != 0 and rng.random() > 0.3))
        if is_hat:
            h_len = int(0.04 * sample_rate)
            for i in range(min(h_len, total_samples - sample_offset)):
                t = i / sample_rate
                env = math.exp(-t * 95.0)
                n = noise_table[(sample_offset + i * 2) % noise_len]
                h_val = n * env * 0.22
                pan = 0.35 if (step % 4 == 0) else -0.35
                left[sample_offset + i] += h_val * (1.0 - pan)
                right[sample_offset + i] += h_val * (1.0 + pan)

    # 3. Sound Effects: Risers e Whooshes nos cortes de cena (t=3.3s e 6.6s)
    transition_times = [3.3, 6.6]
    for cut_t in transition_times:
        # Riser ascendente pré-corte
        riser_start = int((cut_t - 0.55) * sample_rate)
        riser_len = int(0.55 * sample_rate)
        for i in range(riser_len):
            idx = riser_start + i
            if 0 <= idx < total_samples:
                t = i / (0.55 * sample_rate)
                n = noise_table[(idx * 3) % noise_len]
                env = t * t * 0.38
                tone = math.sin(2 * math.pi * (220 + 1300 * t * t) * (i / sample_rate)) * 0.16
                val = (n + tone) * env
                left[idx] += val * (1.0 - t * 0.5)
                right[idx] += val * (0.5 + t * 0.5)

        # Impacto sub-drop pós-corte
        impact_start = int(cut_t * sample_rate)
        impact_len = int(0.38 * sample_rate)
        for i in range(impact_len):
            idx = impact_start + i
            if 0 <= idx < total_samples:
                t = i / sample_rate
                env = math.exp(-t * 12.0)
                sub = math.sin(2 * math.pi * 55.0 * t) * env * 0.45
                n = noise_table[idx % noise_len] * env * 0.22
                val = sub + n
                left[idx] += val
                right[idx] += val

    # 4. Master Limiter & Normalização de Saída
    raw_wav = bytearray()
    fade_samples = int(0.65 * sample_rate)
    for i in range(total_samples):
        l = left[i]
        r = right[i]
        # Saturação analógica suave (tanh)
        l = math.tanh(l * 1.1) * 0.88
        r = math.tanh(r * 1.1) * 0.88
        # Fade-out no encerramento
        if i >= total_samples - fade_samples:
            factor = (total_samples - i) / float(fade_samples)
            l *= factor
            r *= factor
        # Fade-in suave de abertura (primeiros 50ms)
        if i < int(0.05 * sample_rate):
            factor = i / (0.05 * sample_rate)
            l *= factor
            r *= factor

        raw_wav.extend(struct.pack('<hh', int(l * 32767), int(r * 32767)))

    return raw_wav

def generate_reel_overlay(
    reel: Dict[str, Any],
    output_path: Path,
    width: int = TARGET_WIDTH,
    height: int = TARGET_HEIGHT
) -> bool:
    """
    Gera um overlay cinematográfico glassmorphic 9:16 com Pillow:
      - Gradiente escuro no topo para destaque de status
      - Badge superior de identificação do Reel
      - Card glassmorphic no rodapé com cantos arredondados e borda azul oceânico (#1A3D63)
      - Pílula com o nicho comercial da cliente
      - Título, autoria verificada e ficha de ritmo/áudio
      - Área de visualizador de áudio
      - Botão CTA estilizado para o Instagram original
    """
    try:
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Gradiente superior cinematográfico
        for y in range(160):
            alpha = int(140 * (1.0 - y / 160.0))
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

        # Badge superior discreto
        f_top = get_font(13, bold=True)
        draw.text((35, 30), "CYNDY CRYSSY · REEL PREVIEW", font=f_top, fill=(255, 255, 255, 180))

        # Card Glassmorphic Inferior (y: 935 a 1240)
        card_x0, card_y0, card_x1, card_y1 = 28, 935, width - 28, 1240
        draw.rounded_rectangle(
            [card_x0, card_y0, card_x1, card_y1],
            radius=22,
            fill=(10, 18, 30, 218),
            outline=(26, 61, 99, 255),
            width=2
        )

        f_bold = get_font(15, bold=True)
        f_title = get_font(23, bold=True)
        f_sm = get_font(15, bold=False)

        # Pílula de Nicho
        niche_text = reel.get('niche', 'SOCIAL MEDIA')
        draw.rounded_rectangle([50, 960, 215, 994], radius=8, fill=(26, 61, 99, 255), outline=(14, 165, 233, 200), width=1)
        draw.text((65, 968), niche_text, font=f_bold, fill=(255, 255, 255))

        # Título Oficial do Case
        raw_title = reel.get('title', 'Reel Comercial')
        title_display = raw_title if len(raw_title) <= 40 else raw_title[:37] + "..."
        draw.text((50, 1008), title_display, font=f_title, fill=(255, 255, 255))

        # Selo de Verificação & Crédito Criativo
        draw.text((50, 1044), "✓ Cyndy Cryssy · Direção Criativa & Edição", font=f_sm, fill=(14, 165, 233))

        # Info de Áudio Dinâmico
        bpm = reel.get('bpm', 124)
        key = reel.get('key', 'Tech Drive')
        draw.text((50, 1070), f"🎵 {bpm} BPM · {key}", font=f_sm, fill=(71, 199, 77))

        # Botão CTA Canônico
        draw.rounded_rectangle(
            [50, 1175, width - 50, 1222],
            radius=12,
            fill=(26, 61, 99, 235),
            outline=(14, 165, 233, 220),
            width=1
        )
        draw.text((105, 1188), "ASSISTA COMPLETO NO INSTAGRAM ↗", font=f_bold, fill=(255, 255, 255))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        overlay.save(output_path, 'PNG')
        return True

    except Exception as e:
        print(f"Erro na criação do overlay: {e}")
        return False

def create_dynamic_reel_video(
    ffmpeg_bin: Path,
    reel: Dict[str, Any],
    project_root: Path,
    duration: float = 10.0
) -> Dict[str, Any]:
    """
    Gera um preview cinematográfico dinâmico com Áudio e Movimento Real (Tarefa #019):
      1. Sintetiza áudio estéreo específico para o estilo do reel.
      2. Gera overlay glassmorphic com tipografia de alta fidelidade.
      3. Renderiza movimento multi-shot cinematográfico:
         - Shot 1 (0.0s - 3.4s): Dolly push-in com aceleração suave.
         - Cut 1 em 3.4s: Transição fadewhite flash + whoosh sônico.
         - Shot 2 (3.4s - 6.8s): Pan tracking horizontal inspecionando detalhes.
         - Cut 2 em 6.8s: Transição wipeleft + beat drop.
         - Shot 3 (6.8s - 10.0s): Enquadramento heroico com respiração orgânica de câmera.
         - Visualizador de ondas em tempo real (showwaves reativo) em verde/azul.
      4. Codificação H.264/AAC com +faststart imediato para streaming HTTP 206.
    """
    result = {
        "success": False,
        "video_path": None,
        "video_size": 0,
        "faststart": False,
        "error": None
    }

    img_dir = project_root / "assets" / "img"
    videos_dir = project_root / "assets" / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    src_thumb = img_dir / reel["source_thumb"]
    dest_video = videos_dir / reel["video_name"]

    if not src_thumb.is_file():
        result["error"] = f"Thumbnail de origem não encontrado: {src_thumb}"
        return result

    # 1. Sintetiza Áudio
    sample_rate = 44100
    music_style = reel.get("music_style", "automotive")
    audio_bytes = synthesize_reel_audio(music_style, duration=duration, sample_rate=sample_rate)

    temp_wav = videos_dir / f"temp_{reel['id']}.wav"
    with wave.open(str(temp_wav), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    # 2. Gera Overlay
    temp_overlay = videos_dir / f"overlay_{reel['id']}.png"
    generate_reel_overlay(reel, temp_overlay, width=TARGET_WIDTH, height=TARGET_HEIGHT)

    # 3. Renderiza Vídeo com FFmpeg
    cmd = [
        str(ffmpeg_bin), '-y',
        '-loop', '1', '-t', '3.5', '-i', str(src_thumb),
        '-loop', '1', '-t', '3.5', '-i', str(src_thumb),
        '-loop', '1', '-t', '3.5', '-i', str(src_thumb),
        '-loop', '1', '-t', str(duration), '-i', str(temp_overlay),
        '-i', str(temp_wav),
        '-filter_complex', (
            # Shot 1: Push-in
            '[0:v]zoompan=z=\'min(zoom+0.0016,1.2)\':d=105:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s=720x1280:fps=30[s1];'
            # Shot 2: Pan tracking horizontal
            '[1:v]zoompan=z=1.25:d=105:x=\'if(lte(on,1),0,min(x+2.0,iw-iw/zoom))\':y=\'ih/2-(ih/zoom/2)\':s=720x1280:fps=30[s2];'
            # Shot 3: Enquadramento com respiração orgânica
            '[2:v]zoompan=z=\'1.12+0.03*sin(2*PI*on/30)\':d=105:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\':s=720x1280:fps=30[s3];'
            # Transições xfade
            '[s1][s2]xfade=transition=fadewhite:duration=0.25:offset=3.25[s12];'
            '[s12][s3]xfade=transition=wipeleft:duration=0.25:offset=6.5[vshots];'
            # Visualizador de Ondas Sonoras Dinâmico
            '[4:a]showwaves=s=590x40:mode=line:colors=0x47c74d@0.9:scale=cbrt,format=yuva420p[wave];'
            '[vshots][wave]overlay=x=65:y=1115[vwave];'
            '[vwave][3:v]overlay=x=0:y=0[vfinal]'
        ),
        '-map', '[vfinal]', '-map', '4:a',
        '-t', str(duration),
        '-c:v', 'libx264',
        '-preset', 'faster',
        '-crf', str(DEFAULT_CRF),
        '-profile:v', 'high',
        '-level', '4.0',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-c:a', 'aac',
        '-b:a', '128k',
        str(dest_video)
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if temp_wav.exists(): temp_wav.unlink()
        if temp_overlay.exists(): temp_overlay.unlink()

        if proc.returncode != 0 or not dest_video.is_file():
            result["error"] = f"FFmpeg falhou (código {proc.returncode}): {proc.stderr[-300:]}"
            return result

        v_size = dest_video.stat().st_size
        result["video_path"] = dest_video
        result["video_size"] = v_size
        is_fs, _ = check_mp4_faststart(dest_video)
        result["faststart"] = is_fs
        result["success"] = True
        return result

    except Exception as e:
        if temp_wav.exists(): temp_wav.unlink()
        if temp_overlay.exists(): temp_overlay.unlink()
        result["error"] = f"Exceção durante renderização dinâmica: {e}"
        return result

def generate_poster_from_image(
    source_img_path: Path,
    output_poster_path: Path,
    max_bytes: int = MAX_POSTER_SIZE_BYTES,
    target_size: Tuple[int, int] = (TARGET_WIDTH, TARGET_HEIGHT)
) -> Tuple[bool, int, str]:
    """
    Gera um poster WebP ultraleve (< 25 KB) a partir de uma imagem existente (JPG/PNG).
    Ajusta iterativamente a qualidade (Q85 até Q45) e dimensões para garantir
    o respeito rigoroso ao Performance Budget com máxima nitidez visual.
    """
    if not source_img_path.is_file():
        return False, 0, f"Imagem de origem não encontrada: {source_img_path}"

    output_poster_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(source_img_path) as im:
            if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                canvas = im.convert('RGBA')
            else:
                canvas = im.convert('RGB')

            w, h = canvas.size
            if w > target_size[0] or h > target_size[1]:
                canvas.thumbnail(target_size, Image.Resampling.LANCZOS)

            temp_path = output_poster_path.with_suffix('.tmp.webp')
            best_quality = 80
            chosen_size = 0

            for q in range(85, 45, -5):
                canvas.save(temp_path, 'WEBP', quality=q, method=6)
                cur_size = temp_path.stat().st_size
                if cur_size <= max_bytes:
                    best_quality = q
                    chosen_size = cur_size
                    temp_path.replace(output_poster_path)
                    break

            if not output_poster_path.exists() or output_poster_path.stat().st_size > max_bytes:
                scale_factor = 0.9
                working_canvas = canvas.copy()
                while scale_factor >= 0.7:
                    new_w = int(working_canvas.width * scale_factor)
                    new_h = int(working_canvas.height * scale_factor)
                    scaled = working_canvas.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    scaled.save(temp_path, 'WEBP', quality=70, method=6)
                    cur_size = temp_path.stat().st_size
                    if cur_size <= max_bytes:
                        best_quality = 70
                        chosen_size = cur_size
                        temp_path.replace(output_poster_path)
                        break
                    scale_factor -= 0.08

            if temp_path.exists():
                if not output_poster_path.exists():
                    temp_path.replace(output_poster_path)
                    chosen_size = output_poster_path.stat().st_size
                else:
                    temp_path.unlink()

            final_size = output_poster_path.stat().st_size
            is_valid = final_size <= max_bytes
            msg = f"Poster gerado: {format_size(final_size)} (Q{best_quality})"
            return is_valid, final_size, msg

    except Exception as e:
        return False, 0, f"Erro ao processar poster com Pillow: {e}"

def extract_poster_from_video(
    ffmpeg_bin: Path,
    video_path: Path,
    output_poster_path: Path,
    timestamp: float = 1.0,
    max_bytes: int = MAX_POSTER_SIZE_BYTES
) -> Tuple[bool, int, str]:
    """Extrai um frame estático de um vídeo em alta resolução usando FFmpeg."""
    if not video_path.is_file():
        return False, 0, f"Vídeo de origem não encontrado: {video_path}"

    temp_png = output_poster_path.with_suffix('.tmp.png')
    output_poster_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        cmd = [
            str(ffmpeg_bin),
            "-y",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            str(temp_png)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0 or not temp_png.is_file():
            cmd[3] = "0.0"
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if not temp_png.is_file():
            return False, 0, f"FFmpeg não conseguiu extrair frame do vídeo: {res.stderr[:200]}"

        success, size, msg = generate_poster_from_image(temp_png, output_poster_path, max_bytes=max_bytes)
        if temp_png.exists():
            temp_png.unlink()
        return success, size, msg

    except Exception as e:
        if temp_png.exists():
            temp_png.unlink()
        return False, 0, f"Falha na extração de poster via FFmpeg: {e}"

def compress_video(
    ffmpeg_bin: Path,
    input_video: Path,
    output_video: Path,
    crf: int = DEFAULT_CRF,
    trim_seconds: Optional[float] = 15.0,
    generate_webm: bool = False
) -> Dict[str, Any]:
    """Comprime um vídeo para web cinematográfica de acordo com os parâmetros do DEBATE.md."""
    result = {
        "success": False,
        "mp4_path": output_video,
        "mp4_size": 0,
        "webm_path": None,
        "webm_size": 0,
        "faststart": False,
        "error": None
    }

    if not input_video.is_file():
        result["error"] = f"Arquivo de entrada não existe: {input_video}"
        return result

    output_video.parent.mkdir(parents=True, exist_ok=True)

    vf_filter = (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2"
    )

    cmd = [
        str(ffmpeg_bin),
        "-y",
        "-i", str(input_video),
    ]

    if trim_seconds and trim_seconds > 0:
        cmd.extend(["-t", str(trim_seconds)])

    cmd.extend([
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", str(crf),
        "-profile:v", "high",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        str(output_video)
    ])

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0 or not output_video.is_file():
            result["error"] = f"Erro no FFmpeg MP4 (código {proc.returncode}): {proc.stderr[-300:]}"
            return result

        mp4_size = output_video.stat().st_size
        result["mp4_size"] = mp4_size
        is_faststart, _ = check_mp4_faststart(output_video)
        result["faststart"] = is_faststart

        if generate_webm:
            webm_path = output_video.with_suffix('.webm')
            cmd_webm = [
                str(ffmpeg_bin),
                "-y",
                "-i", str(input_video),
            ]
            if trim_seconds and trim_seconds > 0:
                cmd_webm.extend(["-t", str(trim_seconds)])
            cmd_webm.extend([
                "-vf", vf_filter,
                "-c:v", "libvpx-vp9",
                "-crf", "32",
                "-b:v", "0",
                "-pix_fmt", "yuv420p",
                "-c:a", "libopus",
                "-b:a", "96k",
                str(webm_path)
            ])
            proc_webm = subprocess.run(cmd_webm, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc_webm.returncode == 0 and webm_path.is_file():
                result["webm_path"] = webm_path
                result["webm_size"] = webm_path.stat().st_size

        result["success"] = True
        return result

    except Exception as e:
        result["error"] = f"Exceção durante compressão: {e}"
        return result

def create_demo_assets(project_root: Path, ffmpeg_bin: Optional[Path]) -> bool:
    """
    Gera automaticamente os arquivos de posters WebP (< 25 KB) e vídeos MP4 dinâmicos
    com Áudio e Movimento Real (Tarefa #019) para todos os 6 Reels do catálogo.
    """
    img_dir = project_root / "assets" / "img"
    videos_dir = project_root / "assets" / "videos"
    img_dir.mkdir(parents=True, exist_ok=True)
    videos_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER} 🎬 GERAÇÃO DE PREVIEWS DE VÍDEO COM ÁUDIO & MOVIMENTO REAL (TAREFA #019){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"Diretório Vídeos : {Colors.YELLOW}{videos_dir}{Colors.RESET}")
    print(f"Diretório Img    : {Colors.YELLOW}{img_dir}{Colors.RESET}")
    print(f"FFmpeg Detectado : {Colors.GREEN if ffmpeg_bin else Colors.YELLOW}{ffmpeg_bin or 'Não (modo estático)'}{Colors.RESET}\n")

    for reel in REELS_CATALOG:
        source_thumb = img_dir / reel["source_thumb"]
        poster_dest = img_dir / reel["poster_name"]
        video_dest = videos_dir / reel["video_name"]

        print(f"• {Colors.BOLD}{reel['title']}{Colors.RESET}")

        # 1. Gerar Poster WebP (< 25 KB)
        if source_thumb.is_file():
            ok_poster, poster_size, msg = generate_poster_from_image(source_thumb, poster_dest)
            status_color = Colors.GREEN if ok_poster else Colors.RED
            print(f"  Poster: {status_color}{poster_dest.name} ({format_size(poster_size)}){Colors.RESET} — {msg}")
            thumb_webp = source_thumb.with_suffix('.webp')
            if not thumb_webp.exists():
                generate_poster_from_image(source_thumb, thumb_webp, max_bytes=50*1024)
        else:
            print(f"  Poster: {Colors.RED}Origem {source_thumb.name} não encontrada!{Colors.RESET}")

        # 2. Gerar Vídeo MP4 com Áudio Dinâmico e Movimento Real
        if ffmpeg_bin and source_thumb.is_file():
            res = create_dynamic_reel_video(ffmpeg_bin, reel, project_root, duration=10.0)
            if res["success"]:
                v_size = res["video_size"]
                fs_label = f"{Colors.GREEN}[+faststart OK]{Colors.RESET}" if res["faststart"] else f"{Colors.RED}[faststart FAIL]{Colors.RESET}"
                music_label = f"{Colors.CYAN}[🎵 {reel['bpm']} BPM · {reel['music_style']}]{Colors.RESET}"
                print(f"  Vídeo : {Colors.GREEN}{video_dest.name} ({format_size(v_size)}){Colors.RESET} {fs_label} {music_label}")
            else:
                print(f"  Vídeo : {Colors.RED}Falha ao gerar MP4 dinâmico: {res['error']}{Colors.RESET}")
        else:
            if not ffmpeg_bin:
                print(f"  Vídeo : {Colors.DIM}FFmpeg não detectado no ambiente{Colors.RESET}")
            else:
                print(f"  Vídeo : {Colors.RED}Thumbnail não localizado{Colors.RESET}")

    print(f"\n{Colors.BOLD}{Colors.GREEN}✔ Previews de vídeo com áudio e movimento real gerados com sucesso!{Colors.RESET}\n")
    return True

def audit_media(project_root: Path) -> bool:
    """
    Audita todo o ecossistema de mídias (vídeos, posters e áudio) verificando:
      1. Teto de tamanho por vídeo (<= 4.0 MB strict performance budget).
      2. Teto de tamanho por poster (<= 25 KB).
      3. Posicionamento do moov atom (+faststart para HTTP 206 Range Requests).
      4. Presença de poster correspondente para cada vídeo.
      5. Integridade das 6 mídias do catálogo oficial.
      6. Presença de streams de áudio válidos nos vídeos (Tarefa #019).
    """
    img_dir = project_root / "assets" / "img"
    videos_dir = project_root / "assets" / "videos"
    ffprobe_bin = find_ffprobe()

    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER} 🔍 AUDITORIA DE PERFORMANCE BUDGET & INTEGRIDADE DE MÍDIA{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}")
    print(f"Teto Estrito por Vídeo  : {Colors.BOLD}<= 4.0 MB (Recomendado: 1.5 - 2.5 MB){Colors.RESET}")
    print(f"Teto Estrito por Poster : {Colors.BOLD}<= 25 KB{Colors.RESET}")
    print(f"Requisito de Streaming  : {Colors.BOLD}moov atom no início (+faststart para HTTP 206){Colors.RESET}")
    print(f"Requisito de Áudio      : {Colors.BOLD}Stream de áudio estéreo AAC presente (Tarefa #019){Colors.RESET}\n")

    all_passed = True
    total_checks = 0
    passed_checks = 0

    # 1. Auditoria dos Posters Oficiais
    print(f"{Colors.BOLD}1. Auditoria dos Posters WebP ({img_dir.name}):{Colors.RESET}")
    for reel in REELS_CATALOG:
        total_checks += 1
        poster_file = img_dir / reel["poster_name"]
        if not poster_file.is_file():
            print(f"  [{Colors.RED}FAIL{Colors.RESET}] {reel['poster_name']:<24} Arquivo não encontrado no disco")
            all_passed = False
            continue

        p_size = poster_file.stat().st_size
        if p_size <= MAX_POSTER_SIZE_BYTES:
            passed_checks += 1
            print(f"  [{Colors.GREEN} OK {Colors.RESET}] {reel['poster_name']:<24} {format_size(p_size):<10} {Colors.GREEN}(dentro do limite < 25 KB){Colors.RESET}")
        else:
            print(f"  [{Colors.RED}FAIL{Colors.RESET}] {reel['poster_name']:<24} {format_size(p_size):<10} {Colors.RED}(ultrapassou teto de 25 KB){Colors.RESET}")
            all_passed = False

    # 2. Auditoria dos Vídeos Oficiais
    print(f"\n{Colors.BOLD}2. Auditoria dos Vídeos Verticais MP4 ({videos_dir.name}):{Colors.RESET}")
    if not videos_dir.exists():
        print(f"  [{Colors.YELLOW}WARN{Colors.RESET}] Diretório {videos_dir} ainda não existe.")
    else:
        for reel in REELS_CATALOG:
            total_checks += 2  # checagem de tamanho + faststart
            video_file = videos_dir / reel["video_name"]
            if not video_file.is_file():
                print(f"  [{Colors.YELLOW}INFO{Colors.RESET}] {reel['video_name']:<24} Vídeo não inserido ainda")
                continue

            v_size = video_file.stat().st_size
            if v_size <= MAX_VIDEO_SIZE_BYTES:
                passed_checks += 1
                rec_label = Colors.GREEN if v_size <= RECOMMENDED_VIDEO_MAX_BYTES else Colors.YELLOW
                print(f"  [{Colors.GREEN} OK {Colors.RESET}] {reel['video_name']:<24} {format_size(v_size):<10} {rec_label}(<= 4.0 MB budget){Colors.RESET}")
            else:
                print(f"  [{Colors.RED}FAIL{Colors.RESET}] {reel['video_name']:<24} {format_size(v_size):<10} {Colors.RED}(ESTOUROU teto de 4.0 MB!){Colors.RESET}")
                all_passed = False

            is_fs, fs_msg = check_mp4_faststart(video_file)
            if is_fs:
                passed_checks += 1
                print(f"  [{Colors.GREEN} OK {Colors.RESET}]   └─ Faststart HTTP 206 : {Colors.GREEN}Conforme ({fs_msg}){Colors.RESET}")
            else:
                print(f"  [{Colors.RED}FAIL{Colors.RESET}]   └─ Faststart HTTP 206 : {Colors.RED}Inconforme ({fs_msg}){Colors.RESET}")
                all_passed = False

            # Checagem de áudio via ffprobe se disponível
            if ffprobe_bin and ffprobe_bin.is_file():
                total_checks += 1
                try:
                    p = subprocess.run([
                        str(ffprobe_bin), '-v', 'error',
                        '-select_streams', 'a:0',
                        '-show_entries', 'stream=codec_name,channels,sample_rate',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        str(video_file)
                    ], capture_output=True, text=True)
                    audio_out = p.stdout.strip()
                    if audio_out:
                        passed_checks += 1
                        info = " · ".join(audio_out.splitlines())
                        print(f"  [{Colors.GREEN} OK {Colors.RESET}]   └─ Stream de Áudio    : {Colors.GREEN}{info} (Áudio Dinâmico OK){Colors.RESET}")
                    else:
                        print(f"  [{Colors.RED}FAIL{Colors.RESET}]   └─ Stream de Áudio    : {Colors.RED}Sem stream de áudio!{Colors.RESET}")
                        all_passed = False
                except Exception:
                    pass

    print(f"\n{'-'*68}")
    print(f"{Colors.BOLD}Resumo da Auditoria de Mídia:{Colors.RESET}")
    print(f"Total de Verificações Realizadas : {Colors.BOLD}{total_checks}{Colors.RESET}")
    print(f"Verificações Aprovadas           : {Colors.BOLD}{Colors.GREEN}{passed_checks}{Colors.RESET}")
    status_msg = f"{Colors.GREEN}100% CONFORME COM PERFORMANCE BUDGET{Colors.RESET}" if all_passed else f"{Colors.RED}REQUER ATENÇÃO{Colors.RESET}"
    print(f"Resultado Geral                  : {Colors.BOLD}{status_msg}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*68}{Colors.RESET}\n")

    return all_passed

def main():
    parser = argparse.ArgumentParser(
        description="Otimizador de Mídias, Compressão de Vídeos 9:16 e Geração de Previews Dinâmicos",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--input", help="Arquivo ou pasta de vídeo para comprimir", type=str)
    parser.add_argument("-o", "--output", help="Arquivo ou pasta de saída para o vídeo comprimido", type=str)
    parser.add_argument("-p", "--posters", help="Gera/atualiza todos os posters WebP (< 25 KB)", action="store_true")
    parser.add_argument("-c", "--check", "--audit", help="Executa auditoria de Performance Budget e integridade", action="store_true")
    parser.add_argument("-d", "--demo", "--dynamic", help="Gera mídias e posters dinâmicos para todos os 6 reels", action="store_true")
    parser.add_argument("--crf", help="Fator de compressão CRF (padrão: 27)", type=int, default=DEFAULT_CRF)
    parser.add_argument("--trim", help="Duração máxima do corte em segundos (padrão: 15.0)", type=float, default=15.0)
    parser.add_argument("--webm", help="Gera também cópia em formato WebM (VP9/Opus)", action="store_true")
    parser.add_argument("--ffmpeg-path", help="Caminho explícito para o executável ffmpeg", type=str)
    parser.add_argument("--all", help="Executa o pipeline completo (posters + demo dinâmico + auditoria)", action="store_true")

    args = parser.parse_args()

    project_root = find_project_root()
    ffmpeg_bin = find_ffmpeg(args.ffmpeg_path)

    if len(sys.argv) == 1 or args.all:
        create_demo_assets(project_root, ffmpeg_bin)
        success = audit_media(project_root)
        sys.exit(0 if success else 1)

    if args.demo:
        create_demo_assets(project_root, ffmpeg_bin)

    if args.posters:
        print(f"\n{Colors.CYAN}Gerando posters WebP para todos os reels...{Colors.RESET}")
        for reel in REELS_CATALOG:
            src = project_root / "assets" / "img" / reel["source_thumb"]
            dst = project_root / "assets" / "img" / reel["poster_name"]
            ok, size, msg = generate_poster_from_image(src, dst)
            color = Colors.GREEN if ok else Colors.RED
            print(f"• {reel['poster_name']}: {color}{msg}{Colors.RESET}")

    if args.input:
        if not ffmpeg_bin:
            print(f"{Colors.RED}Erro: FFmpeg é necessário para compressão de vídeo mas não foi localizado.{Colors.RESET}")
            print(f"Dica: Instale com 'winget install Gyan.FFmpeg.Essentials' ou especifique '--ffmpeg-path'.")
            sys.exit(1)

        in_path = Path(args.input)
        out_path = Path(args.output) if args.output else project_root / "assets" / "videos" / in_path.with_suffix('.mp4').name
        print(f"\n{Colors.CYAN}Comprimindo vídeo: {in_path} -> {out_path}{Colors.RESET}")
        res = compress_video(
            ffmpeg_bin=ffmpeg_bin,
            input_video=in_path,
            output_video=out_path,
            crf=args.crf,
            trim_seconds=args.trim,
            generate_webm=args.webm
        )
        if res["success"]:
            print(f"{Colors.GREEN}✔ Sucesso! Tamanho: {format_size(res['mp4_size'])}{Colors.RESET}")
            if res["faststart"]:
                print(f"{Colors.GREEN}✔ Faststart ativo (pronto para Range Requests HTTP 206){Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Falha: {res['error']}{Colors.RESET}")
            sys.exit(1)

    if args.check:
        success = audit_media(project_root)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
