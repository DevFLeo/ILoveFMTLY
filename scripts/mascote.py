"""Gera o mascote do ILoveFMTLY (a folha com dobra, olhos, bochechas e coração).

Saídas em assets/: logo.png (1024 px) e app.ico (16 a 256 px, ícone do .exe e da janela).
Uso: python scripts/mascote.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
S = 1024 * 2  # supersampling
def P(v): return int(v * 2)
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# paleta do DESIGN.md (este script fica fora de ui/, onde hex é proibido)
BG, BORDER, ACC, DANGER, TEXT = '#181A2F', '#37415C', '#FDA481', '#B4182D', '#F3F4F8'
d.rounded_rectangle((P(40), P(40), P(984), P(984)), radius=P(210), fill=BG, outline=BORDER, width=P(22))
# sombra da folha
x0, y0, x1, y1, f = 262, 170, 762, 860, 170
d.rounded_rectangle((P(x0+18), P(y0+26), P(x1+18), P(y1+26)), radius=P(60), fill='#11132A')
# folha com canto dobrado
d.rounded_rectangle((P(x0), P(y0), P(x1), P(y1)), radius=P(60), fill=ACC)
d.polygon([(P(x1-f), P(y0-2)), (P(x1+2), P(y0-2)), (P(x1+2), P(y0+f))], fill=BG)
d.polygon([(P(x1-f), P(y0)), (P(x1-f), P(y0+f)), (P(x1), P(y0+f))], fill=DANGER)
# olhos
for cx in (420, 604):
    d.ellipse((P(cx-46), P(410), P(cx+46), P(522)), fill=BG)
    d.ellipse((P(cx-14), P(428), P(cx+16), P(460)), fill=TEXT)
# bochechas
for cx in (350, 674):
    d.ellipse((P(cx-38), P(540), P(cx+38), P(584)), fill='#F2846A')
# sorriso
d.arc((P(452), P(500), P(572), P(600)), start=20, end=160, fill=BG, width=P(18))
# coração (ILove) embaixo
hx, hy, r = 512, 720, 46
d.ellipse((P(hx-2*r), P(hy-r), P(hx), P(hy+r)), fill=DANGER)
d.ellipse((P(hx), P(hy-r), P(hx+2*r), P(hy+r)), fill=DANGER)
d.polygon([(P(hx-2*r+6), P(hy+18)), (P(hx+2*r-6), P(hy+18)), (P(hx), P(hy+2*r+22))], fill=DANGER)
img = img.resize((1024, 1024), Image.LANCZOS)
img.save(ASSETS / 'logo.png')
img.save(ASSETS / 'app.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128),
                                    (256, 256)])
print('assets/logo.png e assets/app.ico gerados')
