"""Gera os mascotes extras: raposa, coruja, tartaruga e castor.

Mesmo estilo da folha (scripts/mascote.py): quadrado arredondado escuro, figura
chapada com olhos, bochechas e um coração pequeno (o "I love").
Saídas em assets/mascotes/: <nome>.png (512 px) e <nome>.ico (16 a 256 px).
Uso: python scripts/mascotes.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / 'assets' / 'mascotes'
SS = 2          # supersampling
SIZE = 1024
# paleta do DESIGN.md (fora de ui/, hex permitido) + tons dos bichos
BG, BORDER, TEXT, DANGER, CHEEK = '#181A2F', '#37415C', '#F3F4F8', '#B4182D', '#F2846A'


def P(v):
    return int(v * SS)


def canvas():
    img = Image.new('RGBA', (SIZE * SS, SIZE * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((P(40), P(40), P(984), P(984)), radius=P(210), fill=BG, outline=BORDER, width=P(22))
    return img, d


def eyes(d, y, dx=92, r=46, white=False):
    for cx in (512 - dx, 512 + dx):
        if white:
            d.ellipse((P(cx - r - 26), P(y - r - 26), P(cx + r + 26), P(y + r + 26)), fill=TEXT)
        d.ellipse((P(cx - r), P(y - r), P(cx + r), P(y + r)), fill=BG)
        d.ellipse((P(cx - 14), P(y - 30), P(cx + 16), P(y)), fill=TEXT)


def cheeks(d, y, dx=170):
    for cx in (512 - dx, 512 + dx):
        d.ellipse((P(cx - 38), P(y - 22), P(cx + 38), P(y + 22)), fill=CHEEK)


def heart(d, hx=512, hy=860, r=30):
    d.ellipse((P(hx - 2 * r), P(hy - r), P(hx), P(hy + r)), fill=DANGER)
    d.ellipse((P(hx), P(hy - r), P(hx + 2 * r), P(hy + r)), fill=DANGER)
    d.polygon([(P(hx - 2 * r + 4), P(hy + 12)), (P(hx + 2 * r - 4), P(hy + 12)), (P(hx), P(hy + 2 * r + 14))],
              fill=DANGER)


def raposa():
    img, d = canvas()
    fur, white = '#F28C3A', '#FFF4E6'
    d.polygon([(P(250), P(180)), (P(400), P(330)), (P(260), P(400))], fill=fur)   # orelhas
    d.polygon([(P(774), P(180)), (P(624), P(330)), (P(764), P(400))], fill=fur)
    d.polygon([(P(275), P(225)), (P(370), P(325)), (P(282), P(365))], fill=BG)
    d.polygon([(P(749), P(225)), (P(654), P(325)), (P(742), P(365))], fill=BG)
    d.polygon([(P(220), P(330)), (P(804), P(330)), (P(512), P(780))], fill=fur)    # cabeça
    d.ellipse((P(220), P(250), P(804), P(560)), fill=fur)
    d.polygon([(P(300), P(500)), (P(724), P(500)), (P(512), P(780))], fill=white)  # focinho
    eyes(d, 470, dx=120, r=40)
    d.ellipse((P(482), P(700), P(542), P(750)), fill=BG)                         # nariz
    heart(d)
    return img


def coruja():
    img, d = canvas()
    body, belly, beak = '#8A6A4F', '#D9C2A3', '#F2B33D'
    d.polygon([(P(260), P(200)), (P(360), P(300)), (P(250), P(340))], fill=body)   # tufos
    d.polygon([(P(764), P(200)), (P(664), P(300)), (P(774), P(340))], fill=body)
    d.ellipse((P(230), P(230), P(794), P(830)), fill=body)
    d.ellipse((P(330), P(520), P(694), P(820)), fill=belly)
    eyes(d, 420, dx=120, r=52, white=True)
    d.polygon([(P(482), P(500)), (P(542), P(500)), (P(512), P(560))], fill=beak)
    for y in (620, 690, 760):                                                      # penas
        d.arc((P(430), P(y - 30), P(500), P(y + 20)), 20, 160, fill=body, width=P(10))
        d.arc((P(524), P(y - 30), P(594), P(y + 20)), 20, 160, fill=body, width=P(10))
    heart(d, hy=880, r=24)
    return img


def tartaruga():
    img, d = canvas()
    shell, plate, skin = '#3E8E5A', '#5FB37A', '#A6D98C'
    d.ellipse((P(400), P(170), P(624), P(400)), fill=skin)                         # cabeça
    for x0, y0 in ((250, 560), (690, 560), (300, 740), (640, 740)):                # patas
        d.ellipse((P(x0), P(y0), P(x0 + 84), P(y0 + 84)), fill=skin)
    d.ellipse((P(250), P(340), P(774), P(820)), fill=shell)                        # casco
    d.regular_polygon((P(512), P(580), P(110)), 6, fill=plate)
    for cx, cy in ((370, 500), (654, 500), (370, 670), (654, 670), (512, 400), (512, 760)):
        d.regular_polygon((P(cx), P(cy), P(56)), 6, fill=plate)
    for cx in (462, 562):                                                          # olhos na cabeça
        d.ellipse((P(cx - 26), P(250), P(cx + 26), P(306)), fill=BG)
        d.ellipse((P(cx - 6), P(258), P(cx + 10), P(274)), fill=TEXT)
    d.arc((P(472), P(300), P(552), P(350)), 20, 160, fill=BG, width=P(10))
    heart(d, hy=575, r=26)
    return img


def castor():
    img, d = canvas()
    fur, muzzle, teeth = '#9C6B43', '#D8B48F', '#FFFFFF'
    for cx in (300, 724):                                                          # orelhas
        d.ellipse((P(cx - 70), P(190), P(cx + 70), P(330)), fill=fur)
        d.ellipse((P(cx - 36), P(224), P(cx + 36), P(296)), fill='#6E4A2D')
    d.ellipse((P(210), P(220), P(814), P(820)), fill=fur)                          # cabeça
    d.ellipse((P(352), P(520), P(672), P(760)), fill=muzzle)                       # focinho
    eyes(d, 450, dx=130, r=42)
    d.ellipse((P(462), P(540), P(562), P(600)), fill=BG)                           # nariz
    d.rounded_rectangle((P(466), P(650), P(508), P(740)), radius=P(10), fill=teeth)  # dentões
    d.rounded_rectangle((P(516), P(650), P(558), P(740)), radius=P(10), fill=teeth)
    cheeks(d, 610, dx=200)
    heart(d, hy=880, r=24)
    return img


MAKERS = {'raposa': raposa, 'coruja': coruja, 'tartaruga': tartaruga, 'castor': castor}

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in MAKERS.items():
        img = make().resize((SIZE, SIZE), Image.LANCZOS)
        img.resize((512, 512), Image.LANCZOS).save(OUT / f'{name}.png')
        img.save(OUT / f'{name}.ico', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128),
                                            (256, 256)])
        print(f'assets/mascotes/{name}.png e .ico')
