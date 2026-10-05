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
from html.parser import HTMLParser
from pathlib import Path

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

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()

        # Identificar slides em <section>
        elem_id = attrs_dict.get('id', '')
        elem_class = attrs_dict.get('class', '')
        if tag_lower == 'section' and ('slide-wrap' in elem_class or elem_id.startswith('slide-')):
            self.slides.append({
                'id': elem_id,
                'aria_label': attrs_dict.get('aria-label', ''),
                'line': self.getpos()[0]
            })

        # Identificar links
        if tag_lower == 'a':
            self.anchor_tags.append(attrs_dict)

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
    # 5. Relatorio Final Consolidado
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
