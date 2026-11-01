#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EzguTech kartochka generatori.

Maqsad: telefon KATTA ko'rinsin. Eski shablonda surat oq fon ichida
kichkina orolcha bo'lib qolar edi — bu yerda surat kadrni to'liq egallaydi.

Format (--olcham):
  telegram  1080x1080  Telegram kanali. Telegram (ayniqsa Desktop) baland
                       suratni balandligi bo'yicha cheklaydi — shuning uchun
                       4:5 kartochka tor bo'lib ko'rinadi. Kvadrat har doim
                       to'liq enini oladi.
  post      1080x1350  Instagram / Facebook lentasi (4:5).
  istoriya  1080x1920  Stories / Reels muqovasi.

Uslub (--uslub):
  shisha    matn suratning ustida shaffof "liquid glass" blokda (iOS uslubi)
  ustma     matn to'g'ridan-to'g'ri suratda, pasti qoraytirilgan
  panel     matn pastdagi oq panelda (eski ko'rinishga yaqin)

Misol:
  python3 karta/kartochka.py \
      --surat karta/xom/0039.jpg --olcham telegram --uslub shisha \
      --nom "IPHONE 11" --xotira 128GB --kod 0254 \
      --naqd 235 --eski-narx 260 --boshiga 0 --olti 55 --onikki 32 \
      --filial "Qiziltepa" --tel "+998 91 844 00 00" \
      --chiqish karta/kartochka-0254.jpg
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

# ---------------------------------------------------------------- brend

SARIQ = (254, 193, 7)
# naqd narx uchun urg'u ranglari: (qorong'i fonda, oq fonda)
NAQD_RANGLAR = {
    "sariq": ((254, 193, 7), (196, 138, 0)),
    "qizil": ((255, 82, 70), (214, 38, 30)),
    "yashil": ((48, 209, 88), (22, 140, 60)),
    "oq": (None, None),            # asosiy matn rangi
}
QORA = (17, 17, 17)
KUL = (125, 125, 125)
OQ = (255, 255, 255)

SHRIFT_DIR = "/usr/share/fonts/opentype/inter"
SHRIFTLAR = {
    "qora": "InterDisplay-ExtraBold.otf",
    "qalin": "Inter-Bold.otf",
    "orta": "Inter-SemiBold.otf",
    "oddiy": "Inter-Medium.otf",
    "yengil": "Inter-Regular.otf",
}

ILDIZ = os.path.dirname(os.path.abspath(__file__))
LOGO_YOLI = os.path.join(ILDIZ, "brend", "logo.png")
# Logotip repoda binary fayl sifatida saqlanmaydi — birinchi ishga tushganda
# eski kartochkadan ajratib olinadi va keshlanadi.
LOGO_MANBA = os.path.join(ILDIZ, "kartochka-1813.jpg")
LOGO_KESIM = (368, 8, 712, 102)

# nom: (en, bo'y, pastki xavfsiz chekka, standart uslub)
# xavfsiz chekka — istoriyada ilova tugmalari yopib qoladigan joy.
OLCHAMLAR = {
    "telegram": (1080, 1080, 0, "shisha"),
    "post": (1080, 1350, 0, "shisha"),
    "istoriya": (1080, 1920, 190, "shisha"),
}

PANEL_BOYI = 338     # oq panel balandligi
USTMA_BOYI = 330     # surat ustidagi matn zonasi
SHISHA_BOYI = 330    # shisha blok balandligi
SHISHA_CHETI = 40    # shisha blokning kadr chetidan masofasi


def shrift(nom, olcham):
    return ImageFont.truetype(os.path.join(SHRIFT_DIR, SHRIFTLAR[nom]), olcham)


def matn_eni(d, matn, fnt):
    q = d.textbbox((0, 0), matn, font=fnt)
    return q[2] - q[0]


# ---------------------------------------------------------------- surat

def suratni_yaxshila(im):
    """Do'kon suratlari ko'pincha xira. Yengil kontrast + o'tkirlik + rang."""
    im = ImageOps.autocontrast(im, cutoff=(0.4, 0.2))
    im = ImageEnhance.Color(im).enhance(1.12)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Sharpness(im).enhance(1.35)
    return im


def _qoplash(im, en, boy, langar="markaz"):
    """Zonani to'liq qoplab qirqadi (cover)."""
    k = max(en / im.width, boy / im.height)
    yangi = im.resize((max(en, int(im.width * k + 0.5)),
                       max(boy, int(im.height * k + 0.5))), Image.LANCZOS)
    x = (yangi.width - en) // 2
    if langar == "yuqori":
        y = 0
    elif langar == "past":
        y = yangi.height - boy
    else:
        y = int((yangi.height - boy) * 0.42)   # telefon odatda biroz tepada
    y = max(0, min(y, yangi.height - boy))
    return yangi.crop((x, y, x + en, y + boy))


def surat_zonasi(yol, en, boy, fon="blur", langar="markaz",
                 yaxshila=True, majburiy_qirqim=False, surish=0.0):
    """Surat zonasini tayyorlaydi.

    Qoida: telefon iloji boricha KATTA, lekin kesilib ketmasin.
      - "cover" qirqimi 20% dan kam bo'lsa — zonani to'liq qoplaymiz;
      - aks holda surat butunligicha sig'diriladi, bo'sh yonlar esa o'sha
        suratning xiralashtirilgan nusxasi bilan to'ldiriladi. Oq bo'shliq
        qolmaydi — shuning uchun telefon "mayda" ko'rinmaydi.

    surish: sig'dirilgan suratni tikka siljitish, -1.0 (tepaga)..1.0 (pastga).
    """
    im = Image.open(yol).convert("RGB")
    im = ImageOps.exif_transpose(im)
    if yaxshila:
        im = suratni_yaxshila(im)

    k_cover = max(en / im.width, boy / im.height)
    k_fit = min(en / im.width, boy / im.height)
    yoqotish = 1 - (k_fit / k_cover)

    if majburiy_qirqim or yoqotish <= 0.20:
        return _qoplash(im, en, boy, langar)

    ich_en = int(im.width * k_fit + 0.5)
    ich_boy = int(im.height * k_fit + 0.5)
    ich = im.resize((ich_en, ich_boy), Image.LANCZOS)

    if fon == "oq":
        taglik = Image.new("RGB", (en, boy), OQ)
    elif fon == "rang":
        o = im.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
        tepa = tuple(int(c * 0.55 + 255 * 0.45) for c in o)
        past = tuple(int(c * 0.80) for c in o)
        taglik = Image.new("RGB", (en, boy))
        ch = ImageDraw.Draw(taglik)
        for y in range(boy):
            t = y / max(1, boy - 1)
            ch.line([(0, y), (en, y)],
                    fill=tuple(int(tepa[i] + (past[i] - tepa[i]) * t)
                               for i in range(3)))
    else:  # blur
        taglik = _qoplash(im, en, boy, "markaz")
        taglik = taglik.filter(ImageFilter.GaussianBlur(radius=max(28, en // 26)))
        taglik = ImageEnhance.Brightness(taglik).enhance(0.62)
        taglik = ImageEnhance.Color(taglik).enhance(0.75)

    x = (en - ich_en) // 2
    bosh_joy = (boy - ich_boy) / 2
    y = int(bosh_joy + surish * bosh_joy)
    y = max(0, min(y, boy - ich_boy))

    soya = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    ImageDraw.Draw(soya).rectangle([x, y, x + ich_en, y + ich_boy],
                                   fill=(0, 0, 0, 120))
    soya = soya.filter(ImageFilter.GaussianBlur(26))
    taglik = Image.alpha_composite(taglik.convert("RGBA"), soya).convert("RGB")
    taglik.paste(ich, (x, y))
    return taglik


# ---------------------------------------------------------------- elementlar

def logo_tayyorla():
    """Logotipni qaytaradi; bo'lmasa eski kartochkadan ajratib oladi."""
    if os.path.exists(LOGO_YOLI):
        return Image.open(LOGO_YOLI).convert("RGBA")
    if not os.path.exists(LOGO_MANBA):
        return None
    manba = Image.open(LOGO_MANBA).convert("RGB").crop(LOGO_KESIM)
    w, h = manba.size
    logo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mp, lp = manba.load(), logo.load()
    for y in range(h):
        for x in range(w):
            r, g, b = mp[x, y]
            yorug = (r * 299 + g * 587 + b * 114) / 1000
            alfa = int(max(0, min(255, 255 - yorug * 255 / 235)))
            if alfa:
                lp[x, y] = (17, 17, 17, alfa)
    logo = logo.crop(logo.getbbox())
    try:
        os.makedirs(os.path.dirname(LOGO_YOLI), exist_ok=True)
        logo.save(LOGO_YOLI)
    except OSError:
        pass
    return logo


def logo_chipi(im, x, y, balandlik=44):
    """Kadr tepasida oq "pill" ichida ezgutech logotipi."""
    logo = logo_tayyorla()
    if logo is None:
        return
    k = balandlik / logo.height
    logo = logo.resize((int(logo.width * k + 0.5), balandlik), Image.LANCZOS)

    yon, tik = 30, 20
    en, boy = logo.width + yon * 2, logo.height + tik * 2

    soya = Image.new("RGBA", (en + 40, boy + 40), (0, 0, 0, 0))
    ImageDraw.Draw(soya).rounded_rectangle([20, 20, 20 + en, 20 + boy],
                                           radius=boy // 2, fill=(0, 0, 0, 90))
    soya = soya.filter(ImageFilter.GaussianBlur(10))
    im.paste(soya, (x - 20, y - 20), soya)

    qalqon = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    ImageDraw.Draw(qalqon).rounded_rectangle([0, 0, en, boy], radius=boy // 2,
                                             fill=(255, 255, 255, 242))
    im.paste(qalqon, (x, y), qalqon)
    im.paste(logo, (x + yon, y + tik), logo)


def nishon(im, matn, x, y, fon=SARIQ, rang=QORA, kegl=30, ong=False):
    """Kichik yorliq (KOD, NASIYA 0% va h.k.)."""
    d = ImageDraw.Draw(im)
    f = shrift("qalin", kegl)
    en = int(matn_eni(d, matn, f) + kegl * 1.5)
    boy = int(kegl * 2.05)
    if ong:
        x = int(x - en)
    qatlam = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    ImageDraw.Draw(qatlam).rounded_rectangle([0, 0, en - 1, boy - 1],
                                             radius=boy // 2, fill=fon + (255,))
    im.paste(qatlam, (int(x), int(y)), qatlam)
    d.text((x + en / 2, y + boy / 2 - 2), matn, font=f, fill=rang, anchor="mm")
    return en, boy


def chizilgan_matn(d, xy, matn, fnt, rang, anchor="ls"):
    """Ustidan chizilgan (eski) narx."""
    d.text(xy, matn, font=fnt, fill=rang, anchor=anchor)
    q = d.textbbox(xy, matn, font=fnt, anchor=anchor)
    o = (q[1] + q[3]) / 2
    d.line([(q[0] - 4, o), (q[2] + 4, o)], fill=rang, width=max(3, fnt.size // 16))


def qorayish(im, bosh, oxir, eng_quyuq=238):
    """Pastga qarab quyuqlashadigan qatlam — matn surat ustida o'qilishi uchun."""
    en, boy = im.size
    q = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    d = ImageDraw.Draw(q)
    for y in range(max(0, bosh), boy):
        t = min(1.0, (y - bosh) / max(1, oxir - bosh))
        d.line([(0, y), (en, y)], fill=(8, 8, 10, int((t ** 1.4) * eng_quyuq)))
    return Image.alpha_composite(im.convert("RGBA"), q).convert("RGB")


def shisha_blok(im, x0, y0, x1, y1, radius=52):
    """iOS "liquid glass" uslubidagi shaffof blok.

    Orqa fon — suratning o'sha joyi, kuchli xiralashtirilgan va biroz
    yorituvchi oq plyonka bilan qoplangan; chetida yupqa yorug' halqa.
    """
    en, boy = im.size
    w, h = x1 - x0, y1 - y0

    ich = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(34))
    ich = ImageEnhance.Color(ich).enhance(1.30)
    ich = ImageEnhance.Brightness(ich).enhance(0.86)
    ich = ich.convert("RGBA")

    # tepadan pastga susayadigan oq yaltirash
    plyonka = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plyonka)
    for y in range(h):
        t = y / max(1, h - 1)
        pd.line([(0, y), (w, y)], fill=(255, 255, 255, int(70 - 46 * t)))
    ich = Image.alpha_composite(ich, plyonka)
    # matn o'qilishi uchun yengil quyuqlashtirish
    ich = Image.alpha_composite(ich, Image.new("RGBA", (w, h), (10, 13, 18, 104)))

    niqob = Image.new("L", (w, h), 0)
    ImageDraw.Draw(niqob).rounded_rectangle([0, 0, w - 1, h - 1],
                                            radius=radius, fill=255)
    ich.putalpha(niqob)

    soya = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    ImageDraw.Draw(soya).rounded_rectangle([x0, y0 + 12, x1, y1 + 12],
                                           radius=radius, fill=(0, 0, 0, 120))
    soya = soya.filter(ImageFilter.GaussianBlur(24))
    natija = Image.alpha_composite(im.convert("RGBA"), soya)
    natija.paste(ich, (x0, y0), ich)

    halqa = Image.new("RGBA", (en, boy), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halqa)
    hd.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=radius,
                         outline=(255, 255, 255, 110), width=2)
    hd.rounded_rectangle([x0 + 3, y0 + 3, x1 - 4, y1 - 4], radius=radius - 3,
                         outline=(255, 255, 255, 38), width=1)
    return Image.alpha_composite(natija, halqa).convert("RGB")


# ---------------------------------------------------------------- matn bloki

def malumot_bloki(im, tepa, matn_tagi, chet, a, qorongi):
    """Nom / narx / nasiya / filial. Pastdan yuqoriga hisoblanadi."""
    en = im.size[0]
    d = ImageDraw.Draw(im)

    if qorongi:
        r_asos, r_yordam, r_past, r_chiziq = OQ, (198, 198, 198), (228, 228, 228), None
    else:
        r_asos, r_yordam, r_past, r_chiziq = QORA, KUL, (70, 70, 70), (234, 234, 234)

    ong_chet = en - chet

    # --- pastki qator: filial / telefon
    pastki = " · ".join(x for x in (a.filial, a.tel) if x)
    if pastki:
        f_p = shrift("orta", 32)
        while matn_eni(d, pastki, f_p) > en - chet * 2 and f_p.size > 22:
            f_p = shrift("orta", f_p.size - 2)
        d.text((en / 2, matn_tagi - 28), pastki, font=f_p, fill=r_past, anchor="ms")
        yc = matn_tagi - 84
        if r_chiziq:
            d.line([(chet, yc), (ong_chet, yc)], fill=r_chiziq, width=3)
        else:
            ch = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(ch).line([(chet, yc), (ong_chet, yc)],
                                    fill=(255, 255, 255, 72), width=3)
            im.paste(Image.alpha_composite(im.convert("RGBA"), ch).convert("RGB"),
                     (0, 0))
            d = ImageDraw.Draw(im)
        narx_tagi = matn_tagi - 116
    else:
        narx_tagi = matn_tagi - 42

    # --- narx qatori: chapda asosiy narx, o'ngda qolgan nasiya ustunlari.
    # Asosiy narx — standart holatda 12 oylik to'lov: u naqd narxdan
    # arzonroq ko'rinadi. --asosiy bilan o'zgartiriladi.
    hammasi = [("boshiga", a.boshiga), ("3 oy", a.uch),
               ("6 oy", a.olti), ("12 oy", a.onikki)]
    tanlov = {"onikki": "12 oy", "olti": "6 oy", "uch": "3 oy"}.get(a.asosiy)
    bosh_qiy = bosh_yorliq = None
    if tanlov:
        for nom_o, qiy in hammasi:
            if nom_o == tanlov and qiy is not None:
                bosh_qiy, bosh_yorliq = qiy, nom_o.upper() + "GA"
                break
    if bosh_qiy is None:                  # 12 oylik berilmagan — naqd narx
        bosh_qiy = a.naqd
        oylar = [t for t in hammasi if t[1] is not None]
    else:
        oylar = [t for t in hammasi if t[1] is not None and t[0] != tanlov]

    bor = en - chet * 2
    oraliq = 54

    qorongi_r, oq_r = NAQD_RANGLAR[a.naqd_rang]
    r_naqd = (qorongi_r if qorongi else oq_r) or r_asos

    def yon_qatorlar(k_yor):
        """Asosiy narx yonidagi qatorlar: [(matn, shrift, chizilganmi, rang)]."""
        q = []
        if bosh_yorliq:
            q.append([(bosh_yorliq, shrift("qalin", k_yor + 2), False, r_yordam)])
            ikki = [("NAQD", shrift("qalin", k_yor + 1), False, r_yordam),
                    (f"{a.naqd}$", shrift("qora", k_yor + 25), False, r_naqd)]
            if a.eski_narx:
                ikki.append((f"{a.eski_narx}$", shrift("orta", k_yor + 1),
                             True, r_yordam))
            q.append(ikki)
        elif a.eski_narx:
            q.append([(f"{a.eski_narx}$", shrift("orta", k_yor + 19), True, r_yordam)])
            q.append([("NAQD NARXI", shrift("qalin", k_yor), False, r_yordam)])
        elif a.naqd_yorliq:
            q.append([("NAQD NARXI", shrift("qalin", k_yor + 3), False, r_yordam)])
        return q

    def yon_eni(k_yor):
        e = 0
        for qator in yon_qatorlar(k_yor):
            e = max(e, sum(matn_eni(d, t, f) for t, f, _, _ in qator)
                    + 14 * (len(qator) - 1))
        return e

    def chap_eni(k_narx, k_yor):
        w = matn_eni(d, f"{bosh_qiy}$", shrift("qora", k_narx))
        yon = yon_eni(k_yor)
        return w + (24 + yon if yon else 0)

    def ustun_enlari(k_q, k_l):
        f_q, f_l = shrift("qora", k_q), shrift("orta", k_l)
        return [max(matn_eni(d, f"{q}$", f_q), matn_eni(d, n.upper(), f_l))
                for n, q in oylar]

    k_narx, k_yor, k_q, k_l = 100, 23, 50, 25
    while True:
        enlar = ustun_enlari(k_q, k_l)
        bo = max(26, int(k_q * 0.86))
        ong = sum(enlar) + bo * max(0, len(enlar) - 1)
        if chap_eni(k_narx, k_yor) + (oraliq + ong if oylar else 0) <= bor:
            break
        if k_q > 34:
            k_q -= 2
            k_l = max(19, k_l - 1)
            continue
        if k_narx > 68:
            k_narx -= 4
            continue
        if k_yor > 19:
            k_yor -= 2
            continue
        if len(oylar) > 2:
            oylar = oylar[1:]
            k_q, k_l, k_narx = 50, 25, 100
            sys.stderr.write("ogohlantirish: nasiya ustunlari sig'madi, "
                             "qisqartirildi\n")
            continue
        break

    f_narx = shrift("qora", k_narx)
    d.text((chet, narx_tagi), f"{bosh_qiy}$", font=f_narx, fill=r_asos, anchor="ls")
    x = chet + matn_eni(d, f"{bosh_qiy}$", f_narx) + 24

    qatorlar = yon_qatorlar(k_yor)
    joylar = ([narx_tagi - int(k_narx * 0.52), narx_tagi - 2]
              if len(qatorlar) == 2 else [narx_tagi - 8])
    for qator, yq in zip(qatorlar, joylar):
        xx = x
        for t, f, chiziq, rang in qator:
            if chiziq:
                chizilgan_matn(d, (xx, yq), t, f, rang)
            else:
                d.text((xx, yq), t, font=f, fill=rang, anchor="ls")
            xx += matn_eni(d, t, f) + 14

    enlar = ustun_enlari(k_q, k_l)
    bo = max(26, int(k_q * 0.86))
    ox = ong_chet
    for (nom_o, qiy), ust in zip(reversed(oylar), reversed(enlar)):
        d.text((ox, narx_tagi - int(k_q * 0.76)), f"{qiy}$",
               font=shrift("qora", k_q), fill=r_asos, anchor="rs")
        d.text((ox, narx_tagi), nom_o.upper(), font=shrift("orta", k_l),
               fill=r_yordam, anchor="rs")
        ox -= ust + bo

    # --- model nomi + KOD yorlig'i
    nom = a.nom.upper()
    if a.xotira:
        nom += "  ·  " + a.xotira
    kod_en = (matn_eni(d, "KOD " + str(a.kod), shrift("qalin", 28)) + 68
              if a.kod else 0)
    f_nom = shrift("qora", 54)
    while matn_eni(d, nom, f_nom) > en - chet * 2 - kod_en and f_nom.size > 30:
        f_nom = shrift("qora", f_nom.size - 2)
    y_nom = min(tepa + 30, narx_tagi - 106 - f_nom.size)
    d.text((chet, y_nom), nom, font=f_nom, fill=r_asos, anchor="la")
    if a.kod:
        nishon(im, "KOD " + str(a.kod), ong_chet, y_nom + 4, kegl=28, ong=True)


# ---------------------------------------------------------------- yig'ish

def yasa(a):
    en, boy, xavfsiz, std_uslub = OLCHAMLAR[a.olcham]
    uslub = a.uslub or std_uslub

    if uslub == "panel":
        zona = boy - xavfsiz - PANEL_BOYI
        im = Image.new("RGB", (en, boy), OQ)
        im.paste(surat_zonasi(a.surat, en, zona, fon=a.fon, langar=a.langar,
                              yaxshila=not a.xom, majburiy_qirqim=a.toldir), (0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, zona, en, boy], fill=OQ)
        d.rectangle([0, zona, en, zona + 7], fill=SARIQ)
        tepa, matn_tagi, chet, qorongi = zona, boy - xavfsiz, 56, False

    elif uslub == "ustma":
        tepa = boy - xavfsiz - USTMA_BOYI
        im = surat_zonasi(a.surat, en, boy, fon=a.fon, langar=a.langar,
                          yaxshila=not a.xom, majburiy_qirqim=a.toldir,
                          surish=-0.8)
        im = qorayish(im, tepa - 300, tepa + 40, 246)
        matn_tagi, chet, qorongi = boy - xavfsiz - 12, 56, True

    else:  # shisha
        y1 = boy - xavfsiz - SHISHA_CHETI
        y0 = y1 - SHISHA_BOYI
        im = surat_zonasi(a.surat, en, boy, fon=a.fon, langar=a.langar,
                          yaxshila=not a.xom, majburiy_qirqim=a.toldir,
                          surish=-0.8)
        im = shisha_blok(im, SHISHA_CHETI, y0, en - SHISHA_CHETI, y1)
        tepa, matn_tagi = y0, y1 - 16
        chet, qorongi = SHISHA_CHETI + 44, True

    logo_chipi(im, 40, 40)
    if a.holat:
        nishon(im, a.holat.upper(), en - 40, 44, kegl=28, ong=True)

    malumot_bloki(im, tepa, matn_tagi, chet, a, qorongi)
    return im


def main(argv=None):
    p = argparse.ArgumentParser(description="EzguTech kartochka generatori")
    p.add_argument("--surat", required=True, help="xom surat yo'li")
    p.add_argument("--chiqish", required=True, help="natija fayli (.jpg)")
    p.add_argument("--nom", required=True, help="model nomi, mas. 'IPHONE 11'")
    p.add_argument("--xotira", default="", help="mas. 128GB")
    p.add_argument("--kod", default="", help="tovar kodi")
    p.add_argument("--naqd", required=True, help="naqd narx (raqam)")
    p.add_argument("--eski-narx", default="", help="chegirmadan oldingi narx")
    p.add_argument("--boshiga", default=None, help="boshlang'ich to'lov")
    p.add_argument("--uch", default=None, help="3 oylik to'lov")
    p.add_argument("--olti", default=None, help="6 oylik to'lov")
    p.add_argument("--onikki", default=None, help="12 oylik to'lov")
    p.add_argument("--filial", default="", help="filial nomi")
    p.add_argument("--tel", default="", help="telefon raqami")
    p.add_argument("--holat", default="", help="o'ng tepadagi yorliq, mas. 'NASIYA 0%'")
    p.add_argument("--olcham", default="telegram", choices=sorted(OLCHAMLAR),
                   help="telegram 1080x1080 | post 1080x1350 | istoriya 1080x1920")
    p.add_argument("--uslub", default=None, choices=("shisha", "ustma", "panel"),
                   help="shisha — shaffof oyna blok (iOS uslubi); "
                        "ustma — matn to'g'ridan-to'g'ri suratda; "
                        "panel — pastdagi oq panel")
    p.add_argument("--fon", default="blur", choices=("blur", "rang", "oq"),
                   help="surat sig'masa yon fon qanday to'ldirilsin")
    p.add_argument("--langar", default="markaz", choices=("yuqori", "markaz", "past"),
                   help="qirqim qayerdan olinsin")
    p.add_argument("--toldir", action="store_true",
                   help="suratni majburan to'liq qoplatish (qirqilsa ham)")
    p.add_argument("--xom", action="store_true",
                   help="suratni avtomatik yaxshilamaslik")
    p.add_argument("--asosiy", default="onikki",
                   choices=("onikki", "olti", "uch", "naqd"),
                   help="katta raqam sifatida nima chiqsin (standart: 12 oylik "
                        "to'lov — arzonroq ko'rinadi)")
    p.add_argument("--naqd-rang", default="sariq", choices=sorted(NAQD_RANGLAR),
                   help="naqd narx rangi: sariq (standart), qizil, yashil, oq")
    p.add_argument("--yorliqsiz", dest="naqd_yorliq", action="store_false",
                   help="narx yonidagi 'NAQD NARXI' yozuvini olib tashlash")
    p.add_argument("--sifat", type=int, default=92)
    a = p.parse_args(argv)

    if not os.path.exists(a.surat):
        sys.exit(f"surat topilmadi: {a.surat}")

    im = yasa(a)
    os.makedirs(os.path.dirname(os.path.abspath(a.chiqish)), exist_ok=True)
    im.save(a.chiqish, quality=a.sifat, subsampling=0, optimize=True)
    print(f"{a.chiqish}  {im.width}x{im.height}  "
          f"{os.path.getsize(a.chiqish) // 1024} KB")


if __name__ == "__main__":
    main()
