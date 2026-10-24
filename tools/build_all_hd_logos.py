# -*- coding: utf-8 -*-
"""
Gerador de Ativos em Alta Definição (800x800) para Clientes do Slide 10.
Utiliza PyQt6.QtSvg e Pillow para renderizar badges vetoriais cristalinos
e o retrato ultra-HD gerado por IA para a Ecicléia Honda Motos.
"""
import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush, QGuiApplication
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt, QRectF

app = QGuiApplication.instance() or QGuiApplication([])

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = PROJECT_ROOT / "assets" / "img"
BRAIN_DIR = Path(r"C:\Users\Alexandre\AppData\Roaming\Antigravity_Conta2_Home\.gemini\antigravity-ide\brain\1caeab1e-f56b-4d82-9aa5-c1a27f5eff65")

def save_hd_versions(qimg_or_pil, slug):
    """Salva a imagem em 800x800 tanto em .jpg quanto em .webp com altíssima qualidade."""
    jpg_path = IMG_DIR / f"{slug}.jpg"
    webp_path = IMG_DIR / f"{slug}.webp"

    if isinstance(qimg_or_pil, QImage):
        # Converte QImage para PIL
        temp_png = IMG_DIR / f"{slug}_temp.png"
        qimg_or_pil.save(str(temp_png), "PNG")
        pil_img = Image.open(temp_png).convert("RGB")
        temp_png.unlink(missing_ok=True)
    else:
        pil_img = qimg_or_pil.convert("RGB")

    # Garante tamanho 800x800 com redimensionamento de alta qualidade se necessário
    if pil_img.size != (800, 800):
        pil_img = pil_img.resize((800, 800), Image.Resampling.LANCZOS)

    pil_img.save(jpg_path, "JPEG", quality=95, optimize=True)
    pil_img.save(webp_path, "WEBP", quality=95, method=6)
    print(f"[OK] [{slug}] HD gerado: JPG ({jpg_path.stat().st_size} B), WEBP ({webp_path.stat().st_size} B)")

# ==============================================================================
# 1. ECICLÉIA HONDA MOTOS (Retrato Fotográfico 1024x1024)
# ==============================================================================
print("\n--- 1. Processando Ecicléia Honda Motos ---")
ecicleia_gen = list(BRAIN_DIR.glob("ecicleia_hd_portrait_*.jpg"))
if ecicleia_gen:
    src_img = Image.open(ecicleia_gen[0])
    save_hd_versions(src_img, "cliente-ecicleia-hondamotos")
else:
    print("Retrato gerado não encontrado, mantendo fallback")

# ==============================================================================
# 2. MOTOBEL EMPILHADEIRAS (800x800 Vector Badge)
# ==============================================================================
print("\n--- 2. Processando Motobel Empilhadeiras ---")
svg_emp = IMG_DIR / "cliente-motobelempilhadeiras.svg"
renderer_emp = QSvgRenderer(str(svg_emp))
qimg_emp = QImage(800, 800, QImage.Format.Format_ARGB32)
qimg_emp.fill(QColor(255, 255, 255))
p = QPainter(qimg_emp)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
renderer_emp.render(p, QRectF(0, 0, 800, 800))
p.end()
save_hd_versions(qimg_emp, "cliente-motobelempilhadeiras")

# ==============================================================================
# 3. HONDA MOTOBEL (800x800 Vector Badge)
# ==============================================================================
print("\n--- 3. Processando Honda Motobel ---")
# Criamos um badge oficial: Fundo branco circular, Asa Honda em vermelho em cima,
# HONDA em vermelho negrito e MOTOBEL em preto/vermelho elegante embaixo
honda_svg = IMG_DIR / "honda_official.svg"
motobel_svg = IMG_DIR / "motobel_colorido.svg"

renderer_honda = QSvgRenderer(str(honda_svg))
renderer_motobel = QSvgRenderer(str(motobel_svg))

qimg_motobel = QImage(800, 800, QImage.Format.Format_ARGB32)
qimg_motobel.fill(QColor(255, 255, 255))
p = QPainter(qimg_motobel)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

# Renderiza a Asa Honda e logo HONDA na parte superior/central (560x320)
renderer_honda.render(p, QRectF(150, 100, 500, 380))

# Renderiza o logotipo oficial Motobel na parte inferior (largura 540x140)
renderer_motobel.render(p, QRectF(140, 520, 520, 145))

# Linha divisória sutil e elegante entre Honda e Motobel
p.setPen(QPen(QColor(220, 224, 230), 3))
p.drawLine(200, 500, 600, 500)

p.end()
save_hd_versions(qimg_motobel, "cliente-honda-motobel")

# ==============================================================================
# 4. HONDA NIPPON (800x800 Vector Badge)
# ==============================================================================
print("\n--- 4. Processando Honda Nippon ---")
qimg_nippon = QImage(800, 800, QImage.Format.Format_ARGB32)
qimg_nippon.fill(QColor(255, 255, 255))
p = QPainter(qimg_nippon)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

# Renderiza a Asa Honda na parte superior
renderer_honda.render(p, QRectF(150, 100, 500, 380))

# Divisória elegante
p.setPen(QPen(QColor(220, 224, 230), 3))
p.drawLine(200, 500, 600, 500)

# Tipografia oficial NIPPON em vermelho/preto negrito
p.setPen(QColor(228, 0, 43)) # Vermelho Honda
font = QFont("Arial", 68, QFont.Weight.Bold)
font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 14)
p.setFont(font)
p.drawText(QRectF(100, 510, 600, 130), Qt.AlignmentFlag.AlignCenter, "NIPPON")

p.setPen(QColor(100, 110, 120))
font_sub = QFont("Arial", 26, QFont.Weight.Bold)
font_sub.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
p.setFont(font_sub)
p.drawText(QRectF(100, 620, 600, 60), Qt.AlignmentFlag.AlignCenter, "MOTOS")

p.end()
save_hd_versions(qimg_nippon, "cliente-honda-nippon")

# ==============================================================================
# 5. GIGA MOTOS SÃO LUÍS BAJAJ (800x800 Vector Badge)
# ==============================================================================
print("\n--- 5. Processando Giga Motos Bajaj ---")
qimg_bajaj = QImage(800, 800, QImage.Format.Format_ARGB32)
# Fundo azul royal oficial Bajaj
qimg_bajaj.fill(QColor(3, 98, 178)) # #0362B2
p = QPainter(qimg_bajaj)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

# Círculo com borda interna sutil
p.setPen(QPen(QColor(255, 255, 255, 40), 6))
p.drawEllipse(20, 20, 760, 760)

# Emblema Bajaj branco estilizado
bajaj_svg = IMG_DIR / "bajaj_official.svg"
renderer_bajaj = QSvgRenderer(str(bajaj_svg))

# Renderiza o logo Bajaj branco na parte superior
renderer_bajaj.render(p, QRectF(220, 80, 360, 350))

# Tipografia "GIGA MOTOS"
p.setPen(QColor(255, 255, 255))
font_giga = QFont("Arial", 64, QFont.Weight.Black)
font_giga.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 8)
p.setFont(font_giga)
p.drawText(QRectF(50, 480, 700, 100), Qt.AlignmentFlag.AlignCenter, "GIGA MOTOS")

# Subtítulo "SÃO LUÍS • BAJAJ"
font_sl = QFont("Arial", 32, QFont.Weight.Bold)
font_sl.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
p.setFont(font_sl)
p.drawText(QRectF(50, 580, 700, 60), Qt.AlignmentFlag.AlignCenter, "SÃO LUÍS • BAJAJ")

# Linha divisória branca fina
p.setPen(QPen(QColor(255, 255, 255, 180), 3))
p.drawLine(240, 460, 560, 460)

p.end()
save_hd_versions(qimg_bajaj, "cliente-gigamotos-saoluisbajaj")

print("\n[OK] Todos os 5 clientes atualizados com ativos HD 800x800 com sucesso!")
