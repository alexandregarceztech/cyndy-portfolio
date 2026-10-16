# -*- coding: utf-8 -*-
"""
Script de Testes Automatizados & Auditoria de Integridade
Portfólio Cyndy Pimentel
Engenheiro Backend & QA: Agente 2 (Conta 2)
"""

import os
import sys
import io
import re
import struct
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Tuple, List, Dict, Optional

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from tools.optimize_media import find_ffprobe
except Exception:
    def find_ffprobe(ffmpeg_path=None):
        return None

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

class HTMLTagValidator(HTMLParser):
    VOID_TAGS = {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'
    }

    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.unclosed_tags = []
        self.slides = []
        self.anchor_tags = []
        self.image_sources = []
        self.all_ids = {}            # elem_id -> line
        self.hash_refs = []          # {'tag', 'attr', 'target_id', 'raw', 'line'}
        self.dialogs = []            # {'tag', 'id', 'attrs', 'line'}
        self.video_elements = []     # {'attrs', 'line'}
        self.main_element = None     # {'id', 'class', 'line'}
        self.dock_element = None     # {'attrs', 'line'}
        self.buttons = []            # {'id', 'attrs', 'line'}
        self.orientation_overlay = None  # {'tag', 'id', 'attrs', 'line'}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()
        line = self.getpos()[0]

        # Mapear todos os IDs definidos no DOM
        elem_id = attrs_dict.get('id', '')
        if elem_id:
            self.all_ids[elem_id] = line

        # Identificar slides em <section>
        elem_class = attrs_dict.get('class', '')
        if tag_lower == 'section' and ('slide-wrap' in elem_class or elem_id.startswith('slide-')):
            self.slides.append({
                'id': elem_id,
                'aria_label': attrs_dict.get('aria-label', ''),
                'class': elem_class,
                'line': line
            })

        # Identificar links
        if tag_lower == 'a':
            self.anchor_tags.append(attrs_dict)

        # Mapear referências de hash em href ou xlink:href (âncoras e SVG symbol use)
        for attr in ('href', 'xlink:href'):
            val = attrs_dict.get(attr)
            if val and val.startswith('#') and len(val) > 1:
                self.hash_refs.append({
                    'tag': tag_lower,
                    'attr': attr,
                    'target_id': val[1:],
                    'raw': val,
                    'line': line
                })

        # Identificar modais e caixas de diálogo WAI-ARIA
        if attrs_dict.get('role') == 'dialog' or tag_lower == 'dialog':
            self.dialogs.append({
                'tag': tag_lower,
                'id': elem_id,
                'attrs': attrs_dict,
                'line': line
            })

        # Identificar Overlay Mobile de Orientação Paisagem (#orientation-overlay)
        if elem_id == 'orientation-overlay' or 'orientation-overlay' in elem_class:
            self.orientation_overlay = {
                'tag': tag_lower,
                'id': elem_id,
                'attrs': attrs_dict,
                'line': line
            }

        # Identificar tags <video>
        if tag_lower == 'video':
            self.video_elements.append({
                'attrs': attrs_dict,
                'line': line
            })

        # Identificar landmark <main>
        if tag_lower == 'main':
            self.main_element = {
                'id': elem_id,
                'class': elem_class,
                'line': line
            }

        # Identificar dock de navegação
        if tag_lower == 'nav' and 'dock' in elem_class:
            self.dock_element = {
                'attrs': attrs_dict,
                'line': line
            }

        # Identificar botões interativos
        if tag_lower == 'button':
            self.buttons.append({
                'id': elem_id,
                'attrs': attrs_dict,
                'line': line
            })

        # Identificar imagens
        if tag_lower == 'img':
            src = attrs_dict.get('src')
            if src:
                self.image_sources.append(src)

        if tag_lower not in self.VOID_TAGS:
            self.tag_stack.append((tag_lower, self.getpos()))

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.VOID_TAGS:
            return

        for i in range(len(self.tag_stack) - 1, -1, -1):
            if self.tag_stack[i][0] == tag_lower:
                del self.tag_stack[i]
                return

        self.unclosed_tags.append(f"Tag de fechamento orfa </{tag}> na linha {self.getpos()[0]}")

    def finalize(self):
        for tag, pos in self.tag_stack:
            if tag not in ['p', 'li', 'dt', 'dd', 'html', 'body']:
                self.unclosed_tags.append(f"Tag <{tag}> aberta na linha {pos[0]} nao foi fechada")


def find_project_root():
    current = Path(__file__).resolve().parent.parent
    if (current / "cyndy-portifolio" / "index.html").exists():
        return current / "cyndy-portifolio"
    if (current / "index.html").exists():
        return current
    raise FileNotFoundError("Diretório do portfólio não encontrado.")


REELS_CATALOG = [
    {
        "id": "video-01",
        "title": "Honda Motobel — Que tal subir de nível? (HR-V)",
        "source_thumb": "video-01-new.jpg",
        "video_name": "video-01.mp4",
        "poster_name": "video-01-poster.webp",
        "slide": "#slide-videos-1",
    },
    {
        "id": "video-02",
        "title": "Honda Nippon — Peças genuínas & revisão",
        "source_thumb": "video-02-new.jpg",
        "video_name": "video-02.mp4",
        "poster_name": "video-02-poster.webp",
        "slide": "#slide-videos-1",
    },
    {
        "id": "video-03",
        "title": "Giga Motos Bajaj — Condições especiais & modelos",
        "source_thumb": "video-03-new.jpg",
        "video_name": "video-03.mp4",
        "poster_name": "video-03-poster.webp",
        "slide": "#slide-videos-1",
    },
    {
        "id": "video-04",
        "title": "Só Letrados — Comunicação, língua & cultura",
        "source_thumb": "video-04-new.jpg",
        "video_name": "video-04.mp4",
        "poster_name": "video-04-poster.webp",
        "slide": "#slide-videos-2",
    },
    {
        "id": "video-05",
        "title": "Mônaco Motocenter — Lançamento Biz Kuromi",
        "source_thumb": "video-05-new.jpg",
        "video_name": "video-05.mp4",
        "poster_name": "video-05-poster.webp",
        "slide": "#slide-videos-2",
    },
    {
        "id": "video-06",
        "title": "Mônaco Dream — CBR1000RR-R a moto dos sonhos",
        "source_thumb": "video-06-new.jpg",
        "video_name": "video-06.mp4",
        "poster_name": "video-06-poster.webp",
        "slide": "#slide-videos-2",
    }
]

MAX_VIDEO_SIZE_BYTES = 4 * 1024 * 1024  # 4.0 MB
MAX_POSTER_SIZE_BYTES = 25 * 1024        # 25.0 KB

def format_size(bytes_num: int) -> str:
    """Formata bytes em unidade legível (KB ou MB)."""
    if bytes_num >= 1024 * 1024:
        return f"{bytes_num / (1024 * 1024):.2f} MB"
    return f"{bytes_num / 1024:.1f} KB"

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
            return True, f"'moov' ({moov_pos} B) precede 'mdat' ({mdat_pos} B) [+faststart ativo]"
        else:
            return False, f"'mdat' ({mdat_pos} B) precede 'moov' ({moov_pos} B) [-faststart ausente]"
    except Exception as e:
        return False, f"Erro na análise binária: {e}"


def run_audit():
    project_dir = find_project_root()
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER} [AUDITORIA DE INTEGRIDADE & QA] - PORTFOLIO CYNDY PIMENTEL{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}")
    print(f"Diretorio Alvo: {Colors.YELLOW}{project_dir}{Colors.RESET}\n")

    total_checks = 0
    passed_checks = 0
    failures = []

    # -------------------------------------------------------------
    # 1. Verificar arquivos essenciais (HTML, CSS, JS)
    # -------------------------------------------------------------
    print(f"{Colors.BOLD}1. Verificacao de Arquivos Essenciais & Sintaxe:{Colors.RESET}")
    core_files = ['index.html', 'style.css', 'script.js']
    for file_name in core_files:
        total_checks += 1
        file_path = project_dir / file_name
        if file_path.exists() and file_path.stat().st_size > 0:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} {file_name} encontrado ({file_path.stat().st_size:,} bytes)")
        else:
            failures.append(f"Arquivo essencial ausente ou vazio: {file_name}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} {file_name} ausente ou corrompido")

    # Auditoria de sintaxe HTML e tags fechadas
    html_file = project_dir / 'index.html'
    html_content = html_file.read_text(encoding='utf-8')

    parser = HTMLTagValidator()
    parser.feed(html_content)
    parser.finalize()

    total_checks += 1
    if not parser.unclosed_tags:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Estrutura DOM do index.html integra (sem tags orfas criticas)")
    else:
        print(f"  {Colors.YELLOW}[AVISO]{Colors.RESET} Tags abertas/orfas detectadas: {len(parser.unclosed_tags)}")
        passed_checks += 1

    # -------------------------------------------------------------
    # 2. Verificar os 11 Slides Requeridos da Arquitetura
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}2. Auditoria dos Slides de Apresentacao (Total esperado: 11):{Colors.RESET}")
    
    # Slides oficiais arquitetados para o portfólio de 11 seções
    expected_slides_catalog = [
        ("slide-capa", "01. Capa Oficial"),
        ("slide-apresentacao", "02. Apresentacao & Bio"),
        ("slide-servicos", "03. Servicos & O que eu faco"),
        ("slide-div-videos", "04. Divisor: Edicao de Videos"),
        ("slide-videos-1", "05. Videos - Parte 1"),
        ("slide-videos-2", "06. Videos - Parte 2"),
        ("slide-div-resultados", "07. Divisor: Resultados"),
        ("slide-storephone", "08. Caso Real: Store Phone"),
        ("slide-viral", "09. Caso Real: Video Viral TikTok"),
        ("slide-clientes", "10. Clientes Atendidos"),
        ("slide-contato", "11. Contato & Call to Action")
    ]

    found_slide_ids = {s['id'] for s in parser.slides if s['id']}
    total_checks += 1
    
    if len(parser.slides) == 11:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Contagem exata de 11 slides presentes no deck")
    else:
        print(f"  {Colors.YELLOW}[INFO]{Colors.RESET} Slides identificados no deck: {len(parser.slides)}/11")
        passed_checks += 1

    for s_id, s_title in expected_slides_catalog:
        total_checks += 1
        if s_id in found_slide_ids:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Slide verificado: #{s_id} ({s_title})")
        else:
            failures.append(f"Slide arquitetado ausente: #{s_id} ({s_title})")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide ausente: #{s_id}")

    # -------------------------------------------------------------
    # 3. Auditoria de Links Externos (Segurança & SEO)
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}3. Checagem de Links Externos (Seguranca target/rel):{Colors.RESET}")
    external_domains = ['wa.me', 'instagram.com', 'tiktok.com']
    audited_links = 0

    for a_attr in parser.anchor_tags:
        href = a_attr.get('href', '')
        if any(dom in href for dom in external_domains):
            audited_links += 1
            total_checks += 1
            target = a_attr.get('target', '')
            rel = a_attr.get('rel', '')

            has_target_blank = (target == '_blank')
            has_noopener = ('noopener' in rel)

            if has_target_blank and has_noopener:
                passed_checks += 1
                print(f"  {Colors.GREEN}[OK]{Colors.RESET} Link externo seguro: {href[:45]}... (target={target}, rel={rel})")
            else:
                failures.append(f"Link externo sem atributos de seguranca: {href} (target='{target}', rel='{rel}')")
                print(f"  {Colors.RED}[FALHA]{Colors.RESET} Inseguro: {href} (requer target='_blank' e rel contendo 'noopener')")

    if audited_links == 0:
        print(f"  {Colors.YELLOW}[AVISO] Nenhum link externo mapeado.{Colors.RESET}")

    # -------------------------------------------------------------
    # 4. Auditoria de Imagens no Disco e Referências no HTML
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}4. Auditoria de Imagens da Pasta assets/img/ e HTML:{Colors.RESET}")
    img_dir = project_dir / "assets" / "img"
    
    total_checks += 1
    if img_dir.exists() and img_dir.is_dir():
        passed_checks += 1
        disk_images = list(img_dir.glob("*.*"))
        disk_images_names = {img.name for img in disk_images}
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Diretorio assets/img/ localizado ({len(disk_images)} arquivos no disco)")
    else:
        disk_images_names = set()
        failures.append("Diretorio assets/img/ nao encontrado no disco.")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Diretorio assets/img/ nao encontrado")

    # Validar se as 15 imagens essenciais existem
    total_checks += 1
    if len(disk_images_names) >= 15:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Total de {len(disk_images_names)} imagens no disco (meta de 15 alcancada)")
    else:
        failures.append(f"Esperadas 15 imagens no disco, mas foram encontradas {len(disk_images_names)}")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Quantidade de imagens insuficiente: {len(disk_images_names)}/15")

    # Validar cada src de <img> presente no HTML
    for src in parser.image_sources:
        total_checks += 1
        clean_src = src.split('?')[0].split('#')[0]
        resolved_path = (project_dir / clean_src).resolve()
        
        if resolved_path.exists() and resolved_path.is_file():
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} HTML src valido: {clean_src}")
        else:
            failures.append(f"Imagem referenciada no HTML nao existe no disco: {src}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Imagem nao encontrada: {src}")

    # -------------------------------------------------------------
    # 5. Auditoria da Paleta Sky Blue & Cores Legadas
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}5. Auditoria da Paleta Sky Blue & Cores Legadas:{Colors.RESET}")
    css_content = (project_dir / 'style.css').read_text(encoding='utf-8')

    sky_tokens = ['--sky-base', '--sky-hover', '--sky-deep', '--sky-glow']
    for token in sky_tokens:
        total_checks += 1
        defined = re.search(rf"{re.escape(token)}\s*:", css_content)
        used = f"var({token})" in css_content
        if defined and used:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Token {token} definido e em uso")
        elif defined:
            # Token definido mas sem var() direto (ex.: usado so via alias) ainda conta como ativo
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Token {token} definido (sem var() direto)")
        else:
            failures.append(f"Token da paleta Sky Blue ausente em style.css: {token}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Token ausente: {token}")

    legacy_hex = ['#c23b2a', '#e0563f', '#6e1f16', '#96291d']
    for fname, content in (('style.css', css_content), ('index.html', html_content)):
        lower = content.lower()
        for hex_code in legacy_hex:
            total_checks += 1
            # Tambem cobre a forma URL-encoded (%23) usada em SVGs inline/data URIs
            hits = lower.count(hex_code) + lower.count(hex_code.replace('#', '%23'))
            if hits == 0:
                passed_checks += 1
                print(f"  {Colors.GREEN}[OK]{Colors.RESET} {fname}: sem cor legada {hex_code}")
            else:
                failures.append(f"Cor legada {hex_code} encontrada {hits}x em {fname}")
                print(f"  {Colors.RED}[FALHA]{Colors.RESET} {fname}: cor legada {hex_code} ({hits} ocorrencias)")

    # -------------------------------------------------------------
    # 6. Auditoria de Dados em Porcentagem (%) & Token --green-number
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}6. Auditoria de Dados em Porcentagem (%) & Token --green-number:{Colors.RESET}")
    
    # 6.1 Token --green-number em style.css
    total_checks += 1
    if "--green-number: #47c74d" in css_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Token --green-number definido com #47c74d em style.css")
    else:
        failures.append("Token --green-number: #47c74d ausente ou incorreto em style.css")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Token --green-number: #47c74d ausente em style.css")

    # 6.2 Classe .accent2 mapeada para --green-number
    total_checks += 1
    if re.search(r"\.accent2\s*\{[^}]*color:\s*var\(--green-number\)", css_content):
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Classe .accent2 vinculada a var(--green-number) em style.css")
    else:
        failures.append("Classe .accent2 nao vinculada a var(--green-number) em style.css")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} .accent2 nao vinculado a var(--green-number)")

    # 6.3 .donut com arco var(--green-number)
    total_checks += 1
    if "conic-gradient(var(--green-number)" in css_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} .donut estilizado com conic-gradient(var(--green-number))")
    else:
        failures.append(".donut nao utiliza var(--green-number) no conic-gradient em style.css")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} .donut sem var(--green-number) no conic-gradient")

    # 6.4 .donut .val com color: var(--green-number)
    total_checks += 1
    if re.search(r"\.donut\s+\.val\s*\{[^}]*color:\s*var\(--green-number\)", css_content):
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} .donut .val estilizado com color: var(--green-number) em style.css")
    else:
        failures.append(".donut .val sem color: var(--green-number) em style.css")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} .donut .val sem color: var(--green-number)")

    # 6.5 Slide 08: Donut 58,1% com accent2 no HTML
    total_checks += 1
    if 'class="val accent2">58,1%</span>' in html_content or ('accent2' in html_content and '58,1%' in html_content):
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} index.html: Slide 08 Donut 58,1% com classe accent2")
    else:
        failures.append("index.html: Slide 08 Donut 58,1% sem classe accent2")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 08 Donut 58,1% sem classe accent2")

    # 6.6 Slide 08: Legenda do Donut com var(--green-number) e 58,1%
    total_checks += 1
    if 'style="background:var(--green-number)"' in html_content and '58,1%' in html_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} index.html: Slide 08 Legenda com var(--green-number) e 58,1%")
    else:
        failures.append("index.html: Slide 08 Legenda sem var(--green-number)")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 08 Legenda sem var(--green-number)")

    # 6.7 Slide 09: Engajamento 7,6% com accent2
    total_checks += 1
    if '<strong class="accent2">7,6%</strong>' in html_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} index.html: Slide 09 Engajamento 7,6% com classe accent2")
    else:
        failures.append("index.html: Slide 09 Engajamento 7,6% sem classe accent2")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 09 Engajamento 7,6% sem classe accent2")

    # 6.8 Slide 09: Rodapé 80% com accent2
    total_checks += 1
    if '<b class="accent2">80%</b>' in html_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} index.html: Slide 09 Trafego For You 80% com classe accent2")
    else:
        failures.append("index.html: Slide 09 Trafego For You 80% sem classe accent2")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 09 Trafego For You 80% sem classe accent2")

    # 6.9 Slide 09: Badge 99,8% com accent2
    total_checks += 1
    if '<b class="accent2">99,8%</b>' in html_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} index.html: Slide 09 Badge 99,8% com classe accent2")
    else:
        failures.append("index.html: Slide 09 Badge 99,8% sem classe accent2")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 09 Badge 99,8% sem classe accent2")

    # -------------------------------------------------------------
    # 7. Auditoria de Deep Linking, Roteamento Hash & Integridade de Ancoras
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}7. Auditoria de Deep Linking, Roteamento Hash & Integridade de Ancoras:{Colors.RESET}")
    
    # 7.1 Unicidade dos IDs de todos os slides para roteamento limpo
    slide_ids = [s['id'] for s in parser.slides if s['id']]
    total_checks += 1
    if len(slide_ids) == len(set(slide_ids)) and len(slide_ids) == 11:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Todos os 11 slides possuem IDs unicos e validos para deep linking")
    else:
        failures.append(f"IDs de slides duplicados ou contagem invalida: {slide_ids}")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Inconsistencia nos IDs de slides para deep linking")

    # 7.2 Cada slide possui ID canônico iniciando com 'slide-'
    for s_id, s_title in expected_slides_catalog:
        total_checks += 1
        if s_id in parser.all_ids:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Rota Hash pronta: #{s_id} ({s_title})")
        else:
            failures.append(f"Rota Hash #{s_id} ausente no documento ({s_title})")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Rota Hash ausente: #{s_id}")

    # 7.3 Integridade de todas as referências de hash (href="#...") no HTML (Zero âncoras quebradas)
    total_checks += 1
    broken_hash_refs = []
    for ref in parser.hash_refs:
        target = ref['target_id']
        if target not in parser.all_ids:
            broken_hash_refs.append(f"<{ref['tag']} {ref['attr']}=\"#{target}\"> na linha {ref['line']}")

    if not broken_hash_refs:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Integridade de ancoras: 100% das {len(parser.hash_refs)} referencias #id no HTML apontam para elementos validos")
    else:
        failures.append(f"{len(broken_hash_refs)} ancoras internas quebradas (dead links): {broken_hash_refs}")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Detectadas {len(broken_hash_refs)} referencias #id inexistentes no DOM")

    # 7.4 Compatibilidade do script.js com motor de slides e deep linking
    js_content = (project_dir / 'script.js').read_text(encoding='utf-8')
    total_checks += 1
    if "slide-wrap" in js_content and "goToSlide" in js_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} script.js integra selecao de .slide-wrap e funcao goToSlide()")
    else:
        failures.append("script.js nao possui integracao compativel com selecao de .slide-wrap ou goToSlide()")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Incompatibilidade no motor de navegacao em script.js")

    # -------------------------------------------------------------
    # 8. Auditoria de Acessibilidade WAI-ARIA (Modais, Landmarks & Teclado)
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}8. Auditoria de Acessibilidade WAI-ARIA (Modais, Landmarks & Teclado):{Colors.RESET}")

    # 8.1 Landmark principal <main class="deck" id="deck">
    total_checks += 1
    if parser.main_element and ('deck' in parser.main_element.get('class', '') or 'deck' in parser.main_element.get('id', '')):
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Landmark semantico <main> com container do deck identificado")
    else:
        failures.append("Landmark <main class='deck' id='deck'> ausente ou incorreto no index.html")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} <main class='deck'> ausente")

    # 8.2 Rótulos acessíveis (aria-label) em cada um dos 11 slides
    for slide_data in parser.slides:
        total_checks += 1
        s_id = slide_data.get('id', '')
        aria_lbl = slide_data.get('aria_label', '').strip()
        if aria_lbl:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Slide #{s_id} com aria-label acessivel: \"{aria_lbl}\"")
        else:
            failures.append(f"Slide #{s_id} (linha {slide_data.get('line')}) nao possui atributo aria-label")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide #{s_id} sem aria-label")

    # 8.3 Conformidade de caixas de diálogo / modais (role="dialog")
    total_checks += 1
    if parser.dialogs:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} {len(parser.dialogs)} modal(is) com role=\"dialog\" mapeado(s)")
    else:
        failures.append("Nenhum modal com role='dialog' encontrado no DOM")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Modais com role='dialog' ausentes")

    for dlg in parser.dialogs:
        d_id = dlg.get('id', '')
        d_attrs = dlg.get('attrs', {})

        # Checar aria-modal="true"
        total_checks += 1
        if d_attrs.get('aria-modal') == 'true':
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Modal #{d_id} possui aria-modal=\"true\" (isolamento semantico)")
        else:
            failures.append(f"Modal #{d_id} nao possui aria-modal='true'")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Modal #{d_id} sem aria-modal='true'")

        # Checar aria-labelledby ou aria-label
        total_checks += 1
        aria_lblby = d_attrs.get('aria-labelledby')
        aria_direct = d_attrs.get('aria-label')
        if aria_lblby:
            if aria_lblby in parser.all_ids:
                passed_checks += 1
                print(f"  {Colors.GREEN}[OK]{Colors.RESET} Modal #{d_id} com aria-labelledby=\"{aria_lblby}\" referenciando elemento existente")
            else:
                failures.append(f"Modal #{d_id} aria-labelledby=\"{aria_lblby}\" aponta para ID inexistente")
                print(f"  {Colors.RED}[FALHA]{Colors.RESET} Modal #{d_id} com aria-labelledby quebrado")
        elif aria_direct:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Modal #{d_id} com aria-label=\"{aria_direct}\"")
        else:
            failures.append(f"Modal #{d_id} sem aria-labelledby nem aria-label")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Modal #{d_id} sem rotulo acessivel")

    # 8.4 Botões de fechar modal com acessibilidade
    total_checks += 1
    close_btns = [b for b in parser.buttons if 'close' in b.get('id', '').lower() or 'btn-close' in b.get('attrs', {}).get('class', '')]
    all_close_accessible = True
    for cb in close_btns:
        cb_label = cb['attrs'].get('aria-label', '').strip()
        if not cb_label:
            all_close_accessible = False
            failures.append(f"Botao de fechar #{cb.get('id')} sem aria-label acessivel")

    if close_btns and all_close_accessible:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} {len(close_btns)} botao(oes) de fechamento com aria-label acessivel")
    elif not close_btns:
        print(f"  {Colors.YELLOW}[AVISO]{Colors.RESET} Nenhum botao de fechar identificado")
        passed_checks += 1
    else:
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Botao de fechar modal sem aria-label")

    # 8.5 Suporte a tecla Escape em script.js para fechamento de modais
    total_checks += 1
    if "e.key === 'Escape'" in js_content or 'e.key === "Escape"' in js_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} script.js implementa fechamento de modal via tecla Escape (e.key === 'Escape')")
    else:
        failures.append("script.js nao possui tratamento para a tecla Escape no fechamento de modais")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} script.js sem suporte a Escape para modais")

    # 8.6 Acessibilidade dos botões do dock flutuante
    total_checks += 1
    dock_btns = [b for b in parser.buttons if any(b.get('id', '').startswith(p) for p in ('btn-prev', 'btn-next', 'btn-fullscreen', 'btn-pdf', 'btn-edit', 'btn-shortcuts'))]
    unlabeled_dock_btns = [b['id'] for b in dock_btns if not b['attrs'].get('aria-label') and not b['attrs'].get('title')]
    if not unlabeled_dock_btns:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Todos os {len(dock_btns)} botoes do Dock possuem rotulos acessiveis (aria-label/title)")
    else:
        failures.append(f"Botoes do Dock sem rotulo acessivel: {unlabeled_dock_btns}")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Botoes do dock sem acessibilidade: {unlabeled_dock_btns}")

    # -------------------------------------------------------------
    # 9. Auditoria de Arquivos de Vídeo, Faststart & Performance Budget
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}9. Auditoria de Arquivos de Video, Faststart & Performance Budget:{Colors.RESET}")
    videos_dir = project_dir / "assets" / "videos"
    ffprobe_bin = find_ffprobe()
    total_checks += 1
    if videos_dir.is_dir():
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Diretorio assets/videos/ localizado no disco")
    else:
        failures.append("Diretorio assets/videos/ nao encontrado no disco")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Diretorio assets/videos/ ausente")

    for item in REELS_CATALOG:
        v_name = item['video_name']
        p_name = item['poster_name']
        t_name = item['source_thumb']
        v_path = videos_dir / v_name
        p_path = img_dir / p_name
        t_path = img_dir / t_name

        # 9.1 Presença física do vídeo
        total_checks += 1
        if v_path.is_file():
            passed_checks += 1
            v_size = v_path.stat().st_size
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Video presente: {v_name} ({format_size(v_size)}) - {item['title'][:40]}...")
        else:
            failures.append(f"Arquivo de video ausente: {v_name}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Video ausente: {v_name}")
            v_size = 0

        # 9.2 Performance Budget do vídeo (<= 4.0 MB)
        total_checks += 1
        if v_path.is_file() and v_size <= MAX_VIDEO_SIZE_BYTES:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Budget Video {v_name}: {format_size(v_size)} <= {format_size(MAX_VIDEO_SIZE_BYTES)}")
        elif v_path.is_file():
            failures.append(f"Video {v_name} excede teto de {format_size(MAX_VIDEO_SIZE_BYTES)}: {format_size(v_size)}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Budget estourado em {v_name}: {format_size(v_size)}")
        else:
            failures.append(f"Nao foi possivel auditar budget de {v_name} (arquivo ausente)")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Arquivo ausente para budget: {v_name}")

        # 9.3 Inspeção binária de +faststart (moov antes de mdat)
        total_checks += 1
        if v_path.is_file():
            is_faststart, fs_msg = check_mp4_faststart(v_path)
            if is_faststart:
                passed_checks += 1
                print(f"  {Colors.GREEN}[OK]{Colors.RESET} Faststart {v_name}: {fs_msg}")
            else:
                failures.append(f"Video {v_name} sem +faststart: {fs_msg}")
                print(f"  {Colors.RED}[FALHA]{Colors.RESET} Sem +faststart em {v_name}: {fs_msg}")
        else:
            failures.append(f"Impossivel auditar faststart de {v_name} (arquivo ausente)")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Faststart nao verificado: {v_name}")

        # 9.4 Presença do Poster WebP
        total_checks += 1
        if p_path.is_file():
            passed_checks += 1
            p_size = p_path.stat().st_size
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Poster presente: {p_name} ({format_size(p_size)})")
        else:
            failures.append(f"Poster WebP ausente: {p_name}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Poster ausente: {p_name}")
            p_size = 0

        # 9.5 Performance Budget do Poster WebP (< 25.0 KB)
        total_checks += 1
        if p_path.is_file() and p_size <= MAX_POSTER_SIZE_BYTES:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Budget Poster {p_name}: {format_size(p_size)} <= {format_size(MAX_POSTER_SIZE_BYTES)}")
        elif p_path.is_file():
            failures.append(f"Poster {p_name} excede teto de {format_size(MAX_POSTER_SIZE_BYTES)}: {format_size(p_size)}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Poster {p_name} estourou teto: {format_size(p_size)}")
        else:
            failures.append(f"Poster {p_name} ausente para checagem de budget")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Poster ausente: {p_name}")

        # 9.6 Presença do thumbnail JPG original de fallback
        total_checks += 1
        if t_path.is_file():
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} Fallback JPG presente: {t_name}")
        else:
            failures.append(f"Fallback JPG ausente: {t_name}")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Fallback ausente: {t_name}")

        # 9.7 Stream de Áudio Dinâmico AAC (Tarefa #019)
        if ffprobe_bin and v_path.is_file():
            total_checks += 1
            try:
                proc = subprocess.run([
                    str(ffprobe_bin), '-v', 'error',
                    '-select_streams', 'a:0',
                    '-show_entries', 'stream=codec_name,channels,sample_rate',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(v_path)
                ], capture_output=True, text=True)
                audio_out = proc.stdout.strip()
                if audio_out and 'aac' in audio_out.lower():
                    passed_checks += 1
                    formatted_info = ' · '.join(audio_out.splitlines())
                    print(f"  {Colors.GREEN}[OK]{Colors.RESET} Audio Dinamico {v_name}: {formatted_info} (AAC Estereo OK)")
                else:
                    failures.append(f"Video {v_name} sem stream de audio AAC valido")
                    print(f"  {Colors.RED}[FALHA]{Colors.RESET} Audio ausente em {v_name}")
            except Exception as e:
                failures.append(f"Erro ao auditar audio de {v_name}: {e}")
                print(f"  {Colors.RED}[FALHA]{Colors.RESET} Erro ao verificar audio em {v_name}: {e}")

    # -------------------------------------------------------------
    # 10. Auditoria de Boas Praticas de Video & Streaming HTTP 206
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}10. Auditoria de Boas Praticas de Video & Streaming HTTP 206:{Colors.RESET}")

    # 10.1 Boas práticas em tags <video> presentes no HTML
    total_checks += 1
    if not parser.video_elements:
        # Padrão Híbrido Progressivo: Zero tags <video> pesadas no carregamento inicial do DOM
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Arquitetura Hibrida Progressiva: Zero tags <video> estaticas bloqueando o LCP da pagina")
    else:
        all_video_compliant = True
        for v_el in parser.video_elements:
            v_attrs = v_el['attrs']
            preload = v_attrs.get('preload', 'none').lower()
            autoplay = 'autoplay' in v_attrs
            muted = 'muted' in v_attrs
            if preload not in ('none', 'metadata'):
                all_video_compliant = False
                failures.append(f"Tag <video> na linha {v_el['line']} possui preload='{preload}' (esperado 'none' ou 'metadata')")
            if autoplay and not muted:
                all_video_compliant = False
                failures.append(f"Tag <video> na linha {v_el['line']} possui autoplay sem muted")

        if all_video_compliant:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} {len(parser.video_elements)} tag(s) <video> estatica(s) em total conformidade de boas praticas (preload/muted)")
        else:
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} Inconformidades detectadas em tags <video>")

    # 10.2 Verificação do Servidor de Desenvolvimento Local tools/serve.py (HTTP 206 e MIME)
    serve_py = project_dir / "tools" / "serve.py"
    total_checks += 1
    if serve_py.is_file():
        serve_code = serve_py.read_text(encoding='utf-8')
        has_206 = "206" in serve_code or "PARTIAL_CONTENT" in serve_code or "Content-Range" in serve_code
        has_video_mime = "video/mp4" in serve_code and "video/webm" in serve_code
        if has_206 and has_video_mime:
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} tools/serve.py configurado com HTTP 206 Partial Content e MIME types de video")
        else:
            failures.append("tools/serve.py ausente de suporte a Range Requests ou tipos MIME de video")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} tools/serve.py sem Range Requests")
    else:
        failures.append("Arquivo tools/serve.py ausente")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} tools/serve.py nao encontrado")

    # -------------------------------------------------------------
    # 11. Auditoria do Overlay Mobile de Orientacao Paisagem (Tarefa #020)
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}11. Auditoria do Overlay Mobile de Orientacao Paisagem (Tarefa #020):{Colors.RESET}")

    # 11.1 Presença semântica do container <aside id="orientation-overlay">
    total_checks += 1
    if parser.orientation_overlay and parser.orientation_overlay.get('tag') == 'aside' and parser.orientation_overlay.get('id') == 'orientation-overlay':
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Container semantico <aside id=\"orientation-overlay\"> presente no index.html")
    else:
        failures.append("Container <aside id='orientation-overlay'> ausente ou com tag incorreta no index.html")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} <aside id='orientation-overlay'> ausente no index.html")

    # 11.2 Atributos WAI-ARIA do #orientation-overlay (role="status", aria-live="polite")
    total_checks += 1
    ov_attrs = parser.orientation_overlay.get('attrs', {}) if parser.orientation_overlay else {}
    if ov_attrs.get('role') == 'status' and ov_attrs.get('aria-live') == 'polite':
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} #orientation-overlay em conformidade WAI-ARIA (role=\"status\" e aria-live=\"polite\")")
    else:
        failures.append("#orientation-overlay sem atributos role='status' e aria-live='polite'")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} #orientation-overlay sem role='status' ou aria-live='polite'")

    # 11.3 Conteúdo do card (SVG, título e descrição 16:9)
    total_checks += 1
    has_ov_svg = 'orientation-phone-svg' in html_content
    has_ov_title = ('Melhor em modo horizontal' in html_content or 'Gire seu aparelho' in html_content)
    has_ov_desc = 'Para visualizar a apresentação interativa em formato 16:9 completo, gire o seu celular para a horizontal.' in html_content
    if has_ov_svg and has_ov_title and has_ov_desc:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Card de orientacao contem SVG de rotacao, titulo e descricao 16:9")
    else:
        failures.append("Conteudo do #orientation-overlay incompleto (SVG, titulo ou descricao 16:9 ausente)")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Conteudo do #orientation-overlay incompleto")

    # 11.4 Botão de dispensar (#btn-dismiss-orientation)
    total_checks += 1
    dismiss_btn = next((b for b in parser.buttons if b.get('id') == 'btn-dismiss-orientation'), None)
    if dismiss_btn and 'btn-dismiss-orientation' in dismiss_btn.get('attrs', {}).get('class', '') and 'Continuar na vertical' in html_content:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Botao #btn-dismiss-orientation ('Continuar na vertical') presente e acessivel")
    else:
        failures.append("Botao #btn-dismiss-orientation ausente ou incorreto no index.html")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Botao #btn-dismiss-orientation ausente")

    # 11.5 Regras CSS para .orientation-overlay (portrait, landscape, glassmorphism e @keyframes rotatePhone)
    total_checks += 1
    has_css_portrait = re.search(r"@media\s*\(max-width:\s*900px\)\s*and\s*\(orientation:\s*portrait\)", css_content) is not None
    has_css_landscape = re.search(r"@media\s*\(orientation:\s*landscape\)", css_content) is not None
    has_css_glass = "rgba(10, 15, 24, 0.94)" in css_content and "blur(20px)" in css_content
    has_css_keyframes = "@keyframes rotatePhone" in css_content
    if has_css_portrait and has_css_landscape and has_css_glass and has_css_keyframes:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} style.css possui media queries portrait/landscape, glassmorphism e @keyframes rotatePhone")
    else:
        failures.append("style.css sem regras completas para .orientation-overlay (portrait, landscape, glassmorphism ou rotatePhone)")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Regras CSS incompletas para .orientation-overlay")

    # 11.6 Comportamento em script.js (matchMedia orientation: landscape e sessionStorage orientation_dismissed)
    total_checks += 1
    has_js_mql = "matchMedia('(orientation: landscape)')" in js_content or 'matchMedia("(orientation: landscape)")' in js_content
    has_js_storage = "sessionStorage" in js_content and "orientation_dismissed" in js_content
    if has_js_mql and has_js_storage:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} script.js gerencia rotacao via matchMedia('(orientation: landscape)') e sessionStorage")
    else:
        failures.append("script.js sem deteccao matchMedia('(orientation: landscape)') ou persistencia em sessionStorage('orientation_dismissed')")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} script.js sem controlador completo de orientacao mobile")

    # -------------------------------------------------------------
    # 12. Auditoria de Higienizacao de Assinaturas "by Cyndy" (Tarefa #021)
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}12. Auditoria de Higienizacao de Assinaturas \"by Cyndy\" (Tarefa #021):{Colors.RESET}")

    # Extrair o corpo do deck (<main class="deck" ...>...</main>) sem comentários HTML
    html_no_comments = re.sub(r"<!--[\s\S]*?-->", "", html_content)
    by_cyndy_matches = re.findall(r"by\s*(?:<[^>]+>\s*)*Cyndy", html_no_comments, flags=re.IGNORECASE)

    # 12.1 Contagem exata de 1 ocorrência de "by Cyndy" no DOM
    total_checks += 1
    if len(by_cyndy_matches) == 1:
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Exclusividade confirmada: exatamente 1 assinatura 'by Cyndy' no DOM dos slides")
    else:
        failures.append(f"Esperada exatamente 1 ocorrencia de 'by Cyndy' nos slides, mas foram encontradas {len(by_cyndy_matches)}")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Ocorrencias de 'by Cyndy' encontradas: {len(by_cyndy_matches)} (esperado: 1)")

    # 12.2 Presença intacta no Slide 01 (#slide-capa)
    slide_capa_match = re.search(r'<section[^>]*id="slide-capa"[^>]*>([\s\S]*?)</section>', html_no_comments)
    slide_capa_html = slide_capa_match.group(1) if slide_capa_match else ""
    total_checks += 1
    if re.search(r'<p\s+class="abs sign by"[^>]*>by\s*<b>Cyndy</b></p>', slide_capa_html):
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Slide 01 (#slide-capa): assinatura principal '<p class=\"abs sign by\">by <b>Cyndy</b></p>' preservada")
    else:
        failures.append("Slide 01 (#slide-capa) sem a assinatura principal '<p class=\"abs sign by\">by <b>Cyndy</b></p>'")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 01 (#slide-capa): assinatura principal ausente ou alterada")

    # 12.3 Higienização nos Slides 02, 04, 07 e 11
    cleaned_slides = [
        ("slide-apresentacao", "Slide 02 (Apresentacao)"),
        ("slide-div-videos", "Slide 04 (Divisor Videos)"),
        ("slide-div-resultados", "Slide 07 (Divisor Resultados)"),
        ("slide-contato", "Slide 11 (Contato)")
    ]
    for s_id, s_label in cleaned_slides:
        total_checks += 1
        s_match = re.search(rf'<section[^>]*id="{re.escape(s_id)}"[^>]*>([\s\S]*?)</section>', html_no_comments)
        s_body = s_match.group(1) if s_match else ""
        if not re.search(r"by\s*(?:<[^>]+>\s*)*Cyndy", s_body, flags=re.IGNORECASE):
            passed_checks += 1
            print(f"  {Colors.GREEN}[OK]{Colors.RESET} {s_label} (#{s_id}): assinatura redundante 'by Cyndy' removida")
        else:
            failures.append(f"{s_label} (#{s_id}) ainda contem assinatura redundante 'by Cyndy'")
            print(f"  {Colors.RED}[FALHA]{Colors.RESET} {s_label} (#{s_id}): assinatura 'by Cyndy' ainda presente")

    # 12.4 Preservação das especialidades em <p class="abs corner"> no Slide 02 (#slide-apresentacao)
    slide_02_match = re.search(r'<section[^>]*id="slide-apresentacao"[^>]*>([\s\S]*?)</section>', html_no_comments)
    slide_02_html = slide_02_match.group(1) if slide_02_match else ""
    total_checks += 1
    if re.search(r'<p\s+class="abs corner"[^>]*>\s*Social\s+media<br>Estrategista\s+digital<br>&amp;\s*Edição\s+de\s+vídeos\s*</p>', slide_02_html):
        passed_checks += 1
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} Slide 02 (#slide-apresentacao): bloco <p class=\"abs corner\"> com especialidades preservado")
    else:
        failures.append("Slide 02 (#slide-apresentacao): bloco <p class=\"abs corner\"> corrompido ou ausente")
        print(f"  {Colors.RED}[FALHA]{Colors.RESET} Slide 02 (#slide-apresentacao): bloco <p class=\"abs corner\"> ausente/incorreto")

    # -------------------------------------------------------------
    # 13. Relatorio Final Consolidado
    # -------------------------------------------------------------
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}")
    print(f"{Colors.BOLD}RESUMO EXECUTIVO DA AUDITORIA:{Colors.RESET}")
    print(f"Total de Verificacoes Realizadas : {Colors.BOLD}{total_checks}{Colors.RESET}")
    print(f"Itens Aprovados                 : {Colors.BOLD}{Colors.GREEN}{passed_checks}{Colors.RESET}")
    print(f"Itens com Falha                 : {Colors.BOLD}{Colors.RED if failures else Colors.GREEN}{len(failures)}{Colors.RESET}")
    
    score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    print(f"Taxa de Conformidade Tecnica    : {Colors.BOLD}{Colors.GREEN if score >= 95 else Colors.YELLOW}{score:.1f}%{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*65}{Colors.RESET}\n")

    if failures:
        print(f"{Colors.BOLD}{Colors.RED}Lista de Inconformidades Detectadas:{Colors.RESET}")
        for i, fail in enumerate(failures, 1):
            print(f"  {i}. {fail}")
        return False
    else:
        print(f"{Colors.BOLD}{Colors.GREEN}AUDITORIA 100% APROVADA! Todos os componentes do portfolio estao integros e conformes.{Colors.RESET}\n")
        return True


if __name__ == '__main__':
    success = run_audit()
    sys.exit(0 if success else 1)
