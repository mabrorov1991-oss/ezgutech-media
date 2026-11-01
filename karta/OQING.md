# Kartochka generatori

Muammo: eski shablonda mahsulot surati oq fon ichida kichkina orolcha bo'lib
qolardi — mijoz lentada telefonni yaxshi ko'rmasdi. Bu yerda surat kadrni
to'liq egallaydi, matn esa ustidagi ixcham blokda turadi.

## Ishlatish

```bash
python3 karta/kartochka.py \
    --surat karta/xom/0039.jpg \
    --olcham telegram --uslub shisha \
    --nom "IPHONE 11" --xotira 128GB --kod 0254 \
    --naqd 235 --eski-narx 260 \
    --boshiga 0 --olti 55 --onikki 32 \
    --filial "Qiziltepa" --tel "+998 91 844 00 00" \
    --chiqish karta/kartochka-0254.jpg
```

## Format — `--olcham`

| Qiymat     | O'lcham   | Qayerga                                  |
|------------|-----------|------------------------------------------|
| `telegram` | 1080×1080 | Telegram kanali (standart)               |
| `post`     | 1080×1350 | Instagram / Facebook lentasi             |
| `istoriya` | 1080×1920 | Stories / Reels muqovasi                 |

**Nega Telegram uchun kvadrat?** Telegram, ayniqsa Desktop versiyasi, suratni
balandligi bo'yicha cheklaydi. Shuning uchun 4:5 (1080×1350) kartochka suhbat
oynasida enini to'liq olmaydi — tor bo'lib, kichrayib ko'rinadi. Kvadrat surat
esa har doim to'liq enini oladi. Instagram'da aksincha — 4:5 eng kattasi,
shuning uchun u yerga `--olcham post`.

Istoriyada pastdan 190 px bo'sh qoldiriladi — Telegram/Instagram tugmalari
o'sha joyni yopib qoladi.

## Uslub — `--uslub`

| Qiymat   | Ko'rinishi                                                     |
|----------|----------------------------------------------------------------|
| `shisha` | iOS "liquid glass" — shaffof, xiralashgan oyna blok (standart) |
| `ustma`  | Matn to'g'ridan-to'g'ri suratda, pasti qoraytirilgan            |
| `panel`  | Matn pastdagi oq panelda (eski ko'rinishga yaqin)               |

`shisha` va `ustma` da surat butun kadrni egallaydi — telefon eng katta
ko'rinadi. `panel` da suratga kamroq joy qoladi.

## Surat qanday joylashtiriladi

Qoida: telefon iloji boricha katta, lekin kesilib ketmasin.

- Agar suratni qirqib to'ldirish 20% dan kam yo'qotish bilan bo'lsa — kadr
  to'liq qoplanadi.
- Aks holda surat butunligicha sig'diriladi, yonlardagi bo'sh joy esa o'sha
  suratning xiralashtirilgan nusxasi bilan to'ldiriladi. Oq bo'shliq qolmaydi,
  shuning uchun telefon "mayda" ko'rinmaydi.

Sozlash:

- `--fon blur|rang|oq` — yon fon qanday to'ldirilsin (standart `blur`)
- `--langar yuqori|markaz|past` — qirqim qayerdan olinsin
- `--toldir` — suratni majburan to'liq qoplatish (bir qismi qirqilsa ham)
- `--xom` — suratni avtomatik yaxshilamaslik

Standart holatda surat avtomatik yaxshilanadi: kontrast, ranglar va o'tkirlik
biroz ko'tariladi (do'kon suratlari ko'pincha xira chiqadi).

## Matn maydonlari

| Bayroq        | Izoh                                            |
|---------------|-------------------------------------------------|
| `--nom`       | model nomi (majburiy)                           |
| `--xotira`    | 128GB, 512GB va h.k.                            |
| `--kod`       | tovar kodi — o'ngdagi sariq yorliq              |
| `--naqd`      | naqd narx (majburiy)                            |
| `--eski-narx` | chegirmadan oldingi narx — ustidan chiziladi    |
| `--boshiga`   | boshlang'ich to'lov                             |
| `--uch`       | 3 oylik to'lov                                  |
| `--olti`      | 6 oylik to'lov                                  |
| `--onikki`    | 12 oylik to'lov                                 |
| `--filial`    | filial nomi                                     |
| `--tel`       | telefon raqami                                  |
| `--holat`     | o'ng tepadagi yorliq, mas. `"NASIYA 0%"`        |
| `--asosiy`    | katta raqam nima bo'lsin: `onikki` (standart), `olti`, `uch`, `naqd` |
| `--naqd-rang` | naqd narx rangi: `sariq` (standart), `qizil`, `yashil`, `oq` |
| `--yorliqsiz` | narx yonidagi "NAQD NARXI" yozuvini olib tashlash |

**Katta raqam — 12 oylik to'lov.** Standart holatda kartochkadagi eng katta
raqam naqd narx emas, 12 oylik to'lov bo'ladi (`185$` · `12 OYGA`) — u
arzonroq ko'rinadi va mijozni ko'proq to'xtatadi. Naqd narx yoniga mayda
bo'lib tushadi (`NAQD 1850$`, chegirma bo'lsa eski narx ustidan chizilgan
holda). 12 oylik to'lov berilmasa, katta raqam o'zi naqd narxga o'tadi.
Eski ko'rinish kerak bo'lsa — `--asosiy naqd`.

Narx va nasiya ustunlari bir qatorga sig'masa, shrift kegllari avtomatik
kichrayadi — matnlar hech qachon ustma-ust tushmaydi.

## Namunalar yasash

Har bir format va uslubdan namuna:

```bash
for u in shisha ustma panel; do
  python3 karta/kartochka.py --surat karta/xom/0039.jpg \
      --olcham telegram --uslub $u \
      --nom "IPHONE 17 PRO MAX" --xotira 512GB --kod 0039 \
      --naqd 1850 --eski-narx 1950 --boshiga 0 --olti 330 --onikki 185 \
      --filial "G'ijduvon" --tel "+998 91 249 22 22" \
      --chiqish karta/namuna/telegram-$u.jpg
done
```

`karta/namuna/` git'ga kirmaydi — har safar qaytadan yasaladi.

## Logotip

Generator `karta/brend/logo.png` ni ishlatadi. Bu fayl repoda saqlanmaydi —
birinchi ishga tushganda `karta/kartochka-1813.jpg` dan avtomatik ajratib
olinadi va keshlanadi. Logotip o'zgarsa, `karta/brend/logo.png` ga yangi
shaffof PNG qo'ying — generator o'shani oladi.

Brend sarig'i: `#FEC107`.
