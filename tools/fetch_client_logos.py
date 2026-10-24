# -*- coding: utf-8 -*-
import subprocess
import re
import html
import sys
from pathlib import Path

urls = [
    ("cliente-honda-motobel", "https://www.instagram.com/honda.motobel/"),
    ("cliente-honda-nippon", "https://www.instagram.com/honda.nippon/"),
    ("cliente-ecicleia-hondamotos", "https://www.instagram.com/ecicleia_hondamotos/"),
    ("cliente-motobelempilhadeiras", "https://www.instagram.com/motobelempilhadeiras/"),
    ("cliente-gigamotos-saoluisbajaj", "https://www.instagram.com/gigamotossaoluisbajaj/")
]

img_dir = Path(__file__).resolve().parent.parent / "assets" / "img"
img_dir.mkdir(parents=True, exist_ok=True)

for slug, url in urls:
    try:
        proc = subprocess.run(
            ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0", url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        content = proc.stdout
        # Check for profile pic in HTML
        matches = re.findall(r'https:[^"\'\s\\]+cdninstagram\.com[^"\'\s\\]+', content)
        for cand in set(matches):
            if any(k in cand for k in ['150x150', '320x320', '640x640', '1080', 's320', 's640']):
                print(f"[{slug}] HD cand: {cand[:80]}")
        m = re.search(r'<meta property="og:image" content="([^"]+)"', content)
        if m:
            img_url = html.unescape(m.group(1))
            # Test if 320x320 works
            cand_url = re.sub(r'_s100x100_', '_s320x320_', img_url)
            check = subprocess.run(["curl.exe", "-s", "-I", cand_url], capture_output=True, text=True)
            if "200 OK" in check.stdout or "HTTP/2 200" in check.stdout:
                img_url = cand_url
                print(f"[{slug}] Sucesso com s320x320!")
            else:
                # Test removing resize tag
                cand_url2 = re.sub(r'stp=dst-jpg_s100x100_tt6&', '', img_url)
                check2 = subprocess.run(["curl.exe", "-s", "-I", cand_url2], capture_output=True, text=True)
                if "200 OK" in check2.stdout or "HTTP/2 200" in check2.stdout:
                    img_url = cand_url2
                    print(f"[{slug}] Sucesso sem stp!")
                else:
                    print(f"[{slug}] Usando URL original com assinatura intacta")

            print(f"[{slug}] Baixando: {img_url[:70]}...")
            dest_file = img_dir / f"{slug}.jpg"
            dl_proc = subprocess.run(
                ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0", "-o", str(dest_file), img_url],
                check=True
            )
            print(f"[{slug}] Salvo com sucesso em {dest_file.name} ({dest_file.stat().st_size} bytes)")
        else:
            print(f"[{slug}] og:image nao encontrado")
    except Exception as e:
        print(f"[{slug}] Erro: {e}")

