"""Генератор сторінок «Файна поляна».

Навіщо: кожен текст на сайті записано тут ОДИН раз — українською (іде прямо в HTML)
і англійською (іде в i18n/en.json під тим самим ключем data-i18n). Так HTML і переклад
не розходяться. Результат — звичайні статичні .html-файли, які можна відкрити й правити вручну.

Запуск:  python3 tools/build-pages.py   (з кореня репозиторію)
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://faina-polyana.vercel.app"
SIZES = json.loads((ROOT / "tools" / "image-sizes.json").read_text(encoding="utf-8"))
EN = {}  # ключ → англійський текст


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(s, quote=True)


def E(tag, key, uk, en, cls="", attrs=""):
    """Елемент із перекладом: український текст у HTML, англійський — в en.json."""
    EN[key] = en
    c = f' class="{cls}"' if cls else ""
    return f'<{tag}{c} data-i18n="{key}"{attrs}>{esc(uk)}</{tag}>'


def tattr(pairs):
    """Атрибути з перекладом: [(attr, key, uk, en)] → 'alt="…" data-i18n-attr="alt:key"'."""
    out, spec = [], []
    for attr, key, uk, en in pairs:
        EN[key] = en
        out.append(f'{attr}="{esc(uk)}"')
        spec.append(f"{attr}:{key}")
    return " ".join(out) + f' data-i18n-attr="{";".join(spec)}"'


LEAF = ('<svg aria-hidden="true" focusable="false" viewBox="0 0 120 20" class="leafline{c}">'
        '<path d="M0 10h44M76 10h44" stroke="#C9D8BC" stroke-width="2"/>'
        '<path d="M50 14 C 52 4, 62 2, 70 4 C 68 12, 60 16, 50 14 Z" fill="#78B454"/></svg>')


def leaf(center=False):
    return LEAF.format(c=" mx-auto" if center else "")


def head(key, label_uk, label_en, h_uk, h_en, center=False, lead=None, light=False):
    """Заголовок секції: рукописна мітка + H2 + листочок + (опційно) вступ."""
    c = " text-center" if center else ""
    hcls = "h2" + c + (" text-white" if light else "")
    lcls = "label" + c + (" text-pink" if light else "")
    out = E("p", f"{key}.label", label_uk, label_en, lcls) + E("h2", f"{key}.title", h_uk, h_en, hcls) + leaf(center)
    if lead:
        out += E("p", f"{key}.lead", lead[0], lead[1], "txt max-w-3xl" + (" mx-auto text-center" if center else "") + (" text-[#E6E7E8]" if light else ""))
    return out


def img(name, key, alt_uk, alt_en, cls, sizes="(min-width: 768px) 50vw, 100vw", lightbox=False, eager=False):
    w, h = SIZES[name]
    big = min(w, 1600)
    src_big = f"assets/photos/{name}-{big}.webp"
    srcset = f"assets/photos/{name}-800.webp 800w, {src_big} {big}w"
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    tag = (f'<img src="assets/photos/{name}-800.webp" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" '
           f'{load} class="{cls}" {tattr([("alt", key, alt_uk, alt_en)])}>')
    if lightbox:
        return f'<a href="{src_big}" class="glightbox block h-full" data-gallery="fp" aria-label="Збільшити фото">{tag}</a>'
    return tag


def section(inner, cls="", sid=""):
    i = f' id="{sid}"' if sid else ""
    return f'<section{i} class="{cls}"><div class="wrap py-20" data-aos="fade-up">{inner}</div></section>\n'


def split(photo, key, alt, label, title, text, bg="", reverse=False, extra="", sid=""):
    """Блок «фото на пів екрана + текст» (агрохолдинг-стиль)."""
    p = f'<div class="min-h-[380px] md:min-h-[460px] bg-cloud">{img(photo, key + ".alt", alt[0], alt[1], "w-full h-full object-cover", lightbox=True)}</div>'
    body = "".join(E("p", f"{key}.p{i}", uk, en, "txt") for i, (uk, en) in enumerate(text))
    t = (f'<div class="px-6 md:px-16 py-16 flex flex-col justify-center {bg}" data-aos="fade-up">'
         + E("p", f"{key}.label", label[0], label[1], "label") + E("h2", f"{key}.title", title[0], title[1], "h2")
         + leaf() + body + extra + "</div>")
    i = f' id="{sid}"' if sid else ""
    return f'<div{i} class="grid md:grid-cols-2">{t + p if reverse else p + t}</div>\n'


def hero(key, label, title, lead, buttons=""):
    return (f'<section class="relative hero-bg bg-cover bg-center">'
            f'<div class="absolute inset-0 bg-gradient-to-b from-white/75 via-white/40 to-white/85" aria-hidden="true"></div>'
            f'<div class="relative wrap max-w-4xl text-center pt-24 pb-28 md:pt-32 md:pb-40">'
            + E("p", f"{key}.label", label[0], label[1], "label")
            + E("h1", f"{key}.title", title[0], title[1], "font-slab font-semibold text-4xl md:text-6xl leading-tight mb-5")
            + E("p", f"{key}.lead", lead[0], lead[1], "font-slab italic text-xl md:text-2xl leading-relaxed text-body mb-8")
            + (f'<div class="flex flex-wrap justify-center gap-3">{buttons}</div>' if buttons else "")
            + "</div></section>\n")


def btn(href, key, uk, en, kind="btn-red"):
    return E("a", key, uk, en, kind, f' href="{href}"')


# Карта Західної України. Межі областей: Natural Earth admin-1 (public domain) через пакет datamaps 0.5.9 (MIT).
# Основна карта: lon 24.0–26.4, lat 48.6–50.0 (рівнокутна проєкція з поправкою cos(49.3°)) → 600×534.
MAP_W, MAP_H = 600, 534
LON0, LON1, LAT0, LAT1 = 24.0, 26.4, 48.6, 50.0
WEST = json.loads((ROOT / "tools" / "west-ukraine.geojson").read_text(encoding="utf-8"))
UKR = json.loads((ROOT / "tools" / "ukraine-inset.geojson").read_text(encoding="utf-8"))


def proj(lat, lon):
    return round((lon - LON0) / (LON1 - LON0) * MAP_W, 1), round((LAT1 - lat) / (LAT1 - LAT0) * MAP_H, 1)


def geo_path(geom, fn):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = []
    for poly in polys:
        for ring in poly:
            pts, last = [], None
            for lon, lat in ring:
                xy = fn(lat, lon)
                xy = (round(xy[0]), round(xy[1]))
                if xy != last:
                    pts.append(f"{xy[0]} {xy[1]}")
                    last = xy
            if len(pts) > 2:
                out.append("M" + "L".join(pts) + "Z")
    return "".join(out)


# (id, lat, lon, укр, англ, хаб?, dx, dy, anchor) — 12 пунктів приймання + хаб (демо-розміщення)
POINTS = [("hub", 49.47, 25.24, "Городище (хаб)", "Horodyshche (hub)", True, 0, -20, "middle"),
          ("kozova", 49.43, 25.15, "Козова", "Kozova", False, -12, 16, "end"),
          ("berezhany", 49.45, 24.94, "Бережани", "Berezhany", False, 0, -13, "middle"),
          ("zboriv", 49.66, 25.14, "Зборів", "Zboriv", False, 0, -14, "middle"),
          ("zbarazh", 49.66, 25.78, "Збараж", "Zbarazh", False, 0, -14, "middle"),
          ("pidhaitsi", 49.27, 25.13, "Підгайці", "Pidhaitsi", False, -12, 5, "end"),
          ("terebovlia", 49.30, 25.70, "Теребовля", "Terebovlia", False, 12, 5, "start"),
          ("monastyryska", 49.09, 25.17, "Монастириська", "Monastyryska", False, -12, 5, "end"),
          ("buchach", 49.06, 25.39, "Бучач", "Buchach", False, 12, 5, "start"),
          ("chortkiv", 49.02, 25.80, "Чортків", "Chortkiv", False, 12, 5, "start"),
          ("rohatyn", 49.41, 24.61, "Рогатин", "Rohatyn", False, -12, 5, "end"),
          ("burshtyn", 49.26, 24.63, "Бурштин", "Burshtyn", False, -12, 5, "end"),
          ("halych", 49.12, 24.72, "Галич", "Halych", False, 0, 22, "middle")]
OBLAST_LABELS = [("Ternopil'", 49.62, 26.05), ("Ivano-Frankivs'k", 48.72, 24.45), ("L'viv", 49.88, 24.35), ("Khmel'nyts'kyy", 49.93, 26.12)]


def map_svg(key):
    names = {f["properties"]["id"]: f["properties"] for f in WEST["features"]}
    hx, hy = proj(49.47, 25.24)
    aria = ("Карта Західної України: хаб у Городищі та 12 пунктів приймання в Тернопільській та Івано-Франківській областях",
            "Map of Western Ukraine: the Horodyshche hub and 12 collection points in the Ternopil and Ivano-Frankivsk regions")
    parts = [f'<svg viewBox="0 0 {MAP_W} {MAP_H}" class="w-full h-auto rounded-2xl" role="img" {tattr([("aria-label", key + ".aria", *aria)])}>',
             f'<rect width="{MAP_W}" height="{MAP_H}" fill="#F7FAF4"/>']
    for f in WEST["features"]:
        home = f["properties"]["id"] in ("Ternopil'", "Ivano-Frankivs'k")
        parts.append(f'<path d="{geo_path(f["geometry"], proj)}" fill="{"#DDEBD3" if home else "#EEF2EA"}" stroke="#FFFFFF" stroke-width="2.5" stroke-linejoin="round"/>')
    for oid, lat, lon in OBLAST_LABELS:
        x, y = proj(lat, lon)
        pr = names[oid]
        parts.append(E("text", f"map.obl.{pr['en'].lower()}", pr["uk"] + " обл.", pr["en"] + " Oblast", "", f' x="{x}" y="{y}" text-anchor="middle" font-size="13" font-style="italic" fill="#7A8075"'))
    for name, lat, lon, uk, en in [("ternopil", 49.553, 25.594, "Тернопіль", "Ternopil"), ("ifrank", 48.922, 24.711, "Івано-Франківськ", "Ivano-Frankivsk")]:
        x, y = proj(lat, lon)
        parts.append(f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" fill="#9AA0A4"/>')
        parts.append(E("text", f"map.city.{name}", uk, en, "", f' x="{x + 10}" y="{y + 5}" font-size="14" fill="#5A5F63"'))
    for pid, lat, lon, *_ in POINTS[1:]:
        x, y = proj(lat, lon)
        parts.append(f'<line x1="{x}" y1="{y}" x2="{hx}" y2="{hy}" stroke="#78B454" stroke-width="1.5" stroke-dasharray="5 5" opacity=".8"/>')
    for pid, lat, lon, uk, en, is_hub, dx, dy, anchor in POINTS:
        x, y = proj(lat, lon)
        r, fill = (12, "#E4303C") if is_hub else (7, "#3F7A2A")
        EN[f"{key}.{pid}.t"] = en
        parts.append(f'<g><title data-i18n="{key}.{pid}.t">{esc(uk)}</title><circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="#FFFFFF" stroke-width="2.5"/></g>')
        parts.append(E("text", f"{key}.{pid}", uk, en, "", f' x="{x + dx}" y="{y + dy}" text-anchor="{anchor}" font-size="{16 if is_hub else 13}" font-weight="{700 if is_hub else 500}" fill="#2F3336" paint-order="stroke" stroke="#F7FAF4" stroke-width="3"'))
    # Вставка: уся Україна з рамкою показаної ділянки
    ix, iy, iw, ih = 418, 404, 170, 118
    ip = lambda lat, lon: (ix + (lon - 22.1) / (40.3 - 22.1) * iw, iy + (52.4 - lat) / (52.4 - 44.3) * ih)
    parts.append(f'<rect x="{ix - 6}" y="{iy - 6}" width="{iw + 12}" height="{ih + 12}" rx="8" fill="#FFFFFF" stroke="#E4E4E0"/>')
    parts.append('<path d="' + "".join(geo_path(f["geometry"], ip) for f in UKR["features"]) + '" fill="#DDEBD3" stroke="#FFFFFF" stroke-width=".6"/>')
    (ax, ay), (bx, by) = ip(LAT1, LON0), ip(LAT0, LON1)
    parts.append(f'<rect x="{round(ax, 1)}" y="{round(ay, 1)}" width="{round(bx - ax, 1)}" height="{round(by - ay, 1)}" fill="none" stroke="#E4303C" stroke-width="2"/>')
    parts.append(E("text", f"{key}.ukraine", "Україна", "Ukraine", "", f' x="{ix + 4}" y="{iy + 10}" font-size="11" font-weight="700" fill="#5A5F63"'))
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------- shared layout
PAGES = [("index.html", "nav.home", "Головна", "Home"),
         ("partners.html", "nav.partners", "Партнерам", "For partners"),
         ("plans.html", "nav.plans", "Наші плани", "Our plans"),
         ("intake.html", "nav.intake", "Приймання ягід", "Berry intake"),
         ("contacts.html", "nav.contacts", "Контакти", "Contacts")]

CDN = {
    "aos_css": ('https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css', 'sha384-/rJKQnzOkEo+daG0jMjU1IwwY9unxt1NBw3Ef2fmOJ3PW/TfAg2KXVoWwMZQZtw9'),
    "aos_js": ('https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js', 'sha384-n1AULnKdMJlK1oQCLNDL9qZsDgXtH6jRYFCpBtWFc+a9Yve0KSoMn575rk755NJZ'),
    "glb_css": ('https://cdn.jsdelivr.net/npm/glightbox@3.3.1/dist/css/glightbox.min.css', 'sha384-GPAzSuZc0kFvdIev6wm9zg8gnafE8tLso7rsAYQfc9hAdWCpOcpcNI5W9lWkYcsd'),
    "glb_js": ('https://cdn.jsdelivr.net/npm/glightbox@3.3.1/dist/js/glightbox.min.js', 'sha384-MZZbZ6RXJudK43v1qY1zOWKOU2yfeBPatuFoKyHAaAgHTUZhwblRTc9CphTt4IGQ'),
}
FONTS = "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&amp;family=Roboto+Slab:ital,wght@0,400;0,600;0,700;1,400&amp;family=Marck+Script&amp;display=swap"


def page_head(file, key, title_uk, title_en, desc_uk, desc_en, scripts=()):
    url = f"{SITE}/{'' if file == 'index.html' else file}"
    EN[key + ".desc"] = desc_en
    css_async = lambda href, sri: (f'<link rel="stylesheet" href="{href}" integrity="{sri}" crossorigin="anonymous" media="print" onload="this.media=\'all\'">'
                                   f'<noscript><link rel="stylesheet" href="{href}"></noscript>')
    js = lambda href, sri: f'<script src="{href}" integrity="{sri}" crossorigin="anonymous" defer></script>'
    extra = "".join(f'  <script src="js/{s}" defer></script>\n' for s in scripts)
    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  {E("title", key + ".title", title_uk, title_en)}
  <meta name="description" content="{esc(desc_uk)}" data-i18n-attr="content:{key}.desc">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Файна поляна">
  <meta property="og:locale" content="uk_UA">
  <meta property="og:locale:alternate" content="en_US">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{esc(title_uk)}">
  <meta property="og:description" content="{esc(desc_uk)}">
  <meta property="og:image" content="{SITE}/assets/img/og-image.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Логотип «Файна поляна» на тлі ягідного поля">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="theme-color" content="#3F7A2A">
  <link rel="icon" href="assets/img/favicon.png" type="image/png">
  <link rel="apple-touch-icon" href="assets/img/apple-touch-icon.png">
  <link rel="preload" as="image" href="assets/img/hero-field.webp" type="image/webp" fetchpriority="high">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preload" as="style" href="{FONTS}" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="{FONTS}"></noscript>
  {css_async(*CDN["aos_css"])}
  {css_async(*CDN["glb_css"])}
  <link rel="stylesheet" href="css/tailwind.css">
  {js(*CDN["aos_js"])}
  {js(*CDN["glb_js"])}
  <script src="js/i18n.js" defer></script>
  <script src="js/main.js" defer></script>
{extra}  <script src="/_vercel/insights/script.js" defer></script>
</head>
"""


def header(active):
    links, mlinks = [], []
    for f, key, uk, en in PAGES:
        cur = f == active
        aria = ' aria-current="page"' if cur else ""
        cls = "relative py-2 hover:text-berrydk" + (" text-berrydk after:absolute after:left-0 after:right-0 after:-bottom-0.5 after:h-0.5 after:rounded after:bg-berry" if cur else "")
        links.append(E("a", key, uk, en, cls, f' href="{f}"{aria}'))
        mcls = "block rounded-xl px-4 py-3 " + ("bg-blush text-berrytx font-bold" if cur else "hover:bg-cloud")
        mlinks.append(E("a", key, uk, en, mcls, f' href="{f}"{aria}'))
    EN["ui.skip"] = "Skip to main content"
    return f"""<body>
<a class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded focus:bg-white focus:px-4 focus:py-2" href="#main" data-i18n="ui.skip">Перейти до основного вмісту</a>
<div class="bg-leafdk text-[#E9F3E2] text-sm text-center px-4 py-2">+380&nbsp;67&nbsp;000&nbsp;00&nbsp;00 · info@fainapolyana.com.ua · {E("span", "top.hours", "Пн–Пт 9:00–18:00", "Mon–Fri 9:00–18:00 (UTC+2)")}</div>
<header class="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-[#ECECE6] shadow-[0_4px_20px_rgba(47,51,54,0.06)]">
  <div class="wrap flex items-center gap-6 h-20">
    <a href="index.html" class="flex items-center gap-3 shrink-0" {tattr([("aria-label", "ui.home", "Файна поляна — на головну", "Faina Polyana — home")])}>
      <img src="assets/img/logo.webp" alt="" width="311" height="343" class="h-14 w-auto">
      {E("span", "ui.badge", "Тернопільщина", "Ternopil region", "hidden sm:inline-block rounded-full bg-mint text-leafdk text-xs font-bold px-3 py-1")}
    </a>
    <nav {tattr([("aria-label", "ui.nav", "Основна навігація", "Main navigation")])} class="hidden lg:flex items-center gap-7 text-[15px] font-medium">{"".join(links)}</nav>
    <div class="ml-auto flex items-center gap-3">
      <div role="group" {tattr([("aria-label", "ui.lang", "Мова сайту", "Site language")])} class="flex rounded-full bg-cloud p-1 text-sm font-bold">
        <button type="button" class="lang-btn rounded-full px-4 py-2" data-lang="uk" aria-pressed="true" lang="uk">UA</button>
        <button type="button" class="lang-btn rounded-full px-4 py-2" data-lang="en" aria-pressed="false" lang="en">EN</button>
      </div>
      {E("a", "ui.cta", "Стати партнером", "Become a partner", "hidden md:inline-flex rounded-full bg-berrydk hover:bg-berrytx text-white text-sm font-bold px-5 py-3", ' href="contacts.html#form"')}
      <button type="button" id="menuBtn" class="lg:hidden w-11 h-11 rounded-full bg-cloud flex items-center justify-center" aria-expanded="false" aria-controls="mobileNav" {tattr([("aria-label", "ui.menu", "Відкрити меню", "Open menu")])}>
        <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
    </div>
  </div>
  <nav id="mobileNav" {tattr([("aria-label", "ui.mnav", "Мобільна навігація", "Mobile navigation")])} class="lg:hidden hidden border-t border-[#ECECE6] bg-white">
    <div class="wrap py-3 grid gap-1 text-base font-medium">{"".join(mlinks)}{E("a", "ui.cta", "Стати партнером", "Become a partner", "mt-2 text-center rounded-full bg-berrydk text-white font-bold px-5 py-3", ' href="contacts.html#form"')}</div>
  </nav>
</header>
<main id="main">
"""


def footer(cta=True):
    band = ""
    if cta:
        band = (f'<section class="bg-berrydk text-white"><div class="wrap py-5 flex flex-wrap items-center justify-between gap-4"><div class="flex flex-wrap items-baseline gap-x-4 gap-y-1">'
                + E("p", "cta.title", "Шукаєте надійного постачальника замороженої ягоди?", "Looking for a reliable supplier of frozen berries?", "font-slab font-bold text-lg")
                + E("p", "cta.text", "Відповімо протягом одного робочого дня.", "We reply within one business day.", "text-white")
                + "</div>" + E("a", "cta.btn", "Надіслати запит", "Send an inquiry", "rounded-full bg-white px-6 py-2.5 text-sm font-bold uppercase tracking-wider text-berrytx transition-colors hover:bg-blush", ' href="contacts.html#form"')
                + "</div></section>\n")
    nav = "<br>".join(E("a", k, uk, en, "hover:text-white", f' href="{f}"') for f, k, uk, en in PAGES[1:])
    return f"""</main>
{band}<footer class="bg-forest text-[#C5D3C0]">
  <div class="wrap py-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4 leading-relaxed">
    <div>{E("p", "f.coop", "СК «Файна поляна»", "Faina Polyana Agricultural Cooperative", "font-slab text-white text-lg mb-3")}{E("p", "f.coop.t", "Ягідний кооператив: 153 сімейні господарства, власне заморожування та прямий експорт.", "Berry cooperative: 153 family farms, in-house freezing and direct export.")}{E("p", "f.edrpou", "ЄДРПОУ 40104479", "EDRPOU code 40104479")}</div>
    <div>{E("p", "f.addr", "Адреса", "Address", "font-slab text-white text-lg mb-3")}{E("p", "f.addr.t", "вул. Тернопільська, 2д, с. Городище, Тернопільська обл., 47633, Україна", "2d Ternopilska St, Horodyshche, Ternopil Oblast, 47633, Ukraine")}</div>
    <div>{E("p", "f.contacts", "Контакти", "Contacts", "font-slab text-white text-lg mb-3")}<p>+380&nbsp;67&nbsp;000&nbsp;00&nbsp;00<br>info@fainapolyana.com.ua</p></div>
    <div>{E("p", "f.pages", "Розділи", "Sections", "font-slab text-white text-lg mb-3")}<p>{nav}</p></div>
  </div>
  <div class="bg-forestdk text-center text-sm py-4 px-4">{E("span", "f.copy", "© 2026 Файна поляна. Демо-версія сайту: частина даних демонстраційна.", "© 2026 Faina Polyana. Demo website: some data is for demonstration only.")}</div>
</footer>
</body>
</html>
"""


# ================================================================ INDEX
def page_index():
    b = hero("h.hero", ("Ягідний кооператив · Тернопільщина", "Berry cooperative · Ternopil region"),
             ("Як 153 сімейні господарства стали експортером європейського рівня", "How 153 family farms became a European-grade exporter"),
             ("Українські ягоди, заморожені на власних потужностях, відсортовані за європейськими стандартами й доставлені партнерам напряму, без посередників.",
              "Ukrainian berries frozen at our own facility, sorted to European standards and delivered to partners directly, with no middlemen."),
             btn("contacts.html#form", "h.hero.b1", "Стати партнером", "Become a partner") + btn("#about", "h.hero.b2", "Дізнатися про нас", "About us", "btn-out"))
    figs = [("153", "h.f1", "виробники з 10 громад", "producers from 10 communities", "text-berry"),
            ("800+ т", "h.f2", "ягід переробляємо за сезон", "of berries processed per season", "text-orangetx"),
            ("15 т", "h.f3", "шокового заморожування на добу", "of blast freezing per day", "text-leafdk"),
            ("300 т", "h.f4", "одночасного зберігання", "of cold storage capacity", "text-rose"),
            ("3000+ м²", "h.f5", "виробничих приміщень", "of production space", "text-stone")]
    units = {"800+ т": "800+ t", "15 т": "15 t", "300 т": "300 t", "3000+ м²": "3,000+ m²"}
    fig_html = "".join(f'<p class="mb-4">{E("b", k + "n", n, units.get(n, n), "font-slab text-4xl " + c)}<br>{E("span", k, uk, en)}</p>' for n, k, uk, en, c in figs)
    about = [("«Файна поляна» з'явилася у 2015 році, коли кілька сімейних господарств із сіл Тернопільщини вирішили працювати разом за класичною європейською моделлю кооперації.",
              "Faina Polyana was founded in 2015, when several family farms from villages of the Ternopil region decided to work together under the classic European cooperative model."),
             ("Ідея була простою: дрібний виробник окремо не може гарантувати покупцю ні обсягів, ні стабільної якості, ні сертифікацій. Сотня виробників зі спільними стандартами, власними потужностями та єдиним контролем якості — може.",
              "The idea was simple: a small grower alone cannot guarantee a buyer volumes, consistent quality or certification. A hundred growers with shared standards, their own facilities and one quality control system can."),
             ("Сьогодні кооператив об'єднує 153 виробники з десяти громад Тернопільської та Івано-Франківської областей. Кожен учасник вирощує ягоди на власній землі, а кооператив бере на себе приймання, охолодження, заморожування, сортування, зберігання, логістику та продаж.",
              "Today the cooperative unites 153 producers from ten communities in the Ternopil and Ivano-Frankivsk regions. Each member grows berries on their own land, while the cooperative handles intake, cooling, freezing, sorting, storage, logistics and sales."),
             ("У 2018 році ми збудували перший в Україні кооперативний цех заморожування ягід. Кооператив викупив майданчик за власні кошти, а нещодавно добудував новий склад заморожених ягід площею понад 650 м² — і вже готує наступний етап розширення.",
              "In 2018 we built Ukraine's first cooperative berry-freezing facility. The cooperative bought the site with its own funds, recently completed a new 650 m² frozen-berry warehouse and is already preparing the next stage of expansion.")]
    about_html = "".join(E("p", f"h.about.p{i}", uk, en, "txt dropcap" if i == 0 else "txt") for i, (uk, en) in enumerate(about))
    b += f"""<section id="about" class="wrap py-20" data-aos="fade-up">
  {head("h.about", "Про кооператив", "About us", "Кооператив, який виріс із довіри", "A cooperative built on trust")}
  <div class="grid gap-12 lg:grid-cols-[1fr_300px] items-start">
    <div class="md:columns-2 gap-10">{about_html}</div>
    <aside class="rounded-md bg-cloud border-t-4 border-orange p-6" {tattr([("aria-label", "h.figs.aria", "Кооператив у цифрах", "The cooperative in figures")])}>
      {E("p", "h.figs", "У цифрах", "In figures", "label text-orangetx")}{fig_html}<p class="font-slab font-bold text-xl text-leafdk">ISO 22000 · FSSC 22000</p>
    </aside>
  </div>
</section>
"""
    adv = [("bg-berry", "Стабільні обсяги", "Stable volumes", "Сировина з понад 100 га насаджень учасників і від перевірених виробників сусідніх областей. Неврожай в одному господарстві не загрожує контракту.", "Raw material comes from over 100 ha of members' plantations and from trusted growers in neighbouring regions. A poor harvest on one farm never puts a contract at risk."),
           ("bg-orange", "Простежуваність кожної партії", "Traceability of every lot", "Ми знаємо, з якої ділянки, від якого виробника й якого дня надійшла ягода — на всьому шляху до вашого складу.", "We know which plot, which grower and which day every berry came from — all the way to your warehouse."),
           ("bg-leaf", "Агрономічний супровід", "Agronomic support", "Учасники працюють з агрономами кооперативу — якість закладається ще на плантації.", "Members work with the cooperative's agronomists, so quality is built in on the plantation."),
           ("bg-rose", "Мотивовані виробники", "Motivated growers", "Члени кооперативу, які отримують оплату в кінці сезону, мають премію 50%. Здавати найкращу ягоду вигідно кожному.", "Members who take payment at the end of the season receive a 50% premium, so delivering the best berries pays off for everyone."),
           ("bg-sprout", "Без посередників", "No middlemen", "Уся обробка — у нас, контракт — напряму з вами. Чесна ціна, прозоре походження й пряма відповідальність за якість.", "All processing is done in-house and the contract is directly with you: a fair price, transparent origin and direct responsibility for quality.")]
    adv_html = "".join(f'<div><h3 class="font-slab font-bold text-xl mb-2 flex items-center gap-2"><span class="dot {c}" aria-hidden="true"></span>{E("span", f"h.adv{i}.t", tu, te)}</h3>{E("p", f"h.adv{i}.d", du, de, "text-[17px] leading-relaxed text-body")}</div>'
                       for i, (c, tu, te, du, de) in enumerate(adv))
    b += section(head("h.model", "Кооперативна модель", "Cooperative model", "Одна угода — 153 господарства, які працюють як одне ціле", "One contract — 153 farms working as one",
                      lead=("Для покупця кооператив поєднує масштаб великого постачальника з контролем, який можливий лише тоді, коли знаєш кожного виробника особисто.",
                            "For a buyer, the cooperative combines the scale of a large supplier with the control that is only possible when you know every grower personally."))
                 + f'<div class="grid gap-10 md:grid-cols-2 lg:grid-cols-3 mt-6">{adv_html}</div>', "bg-cloud")
    b += split("kontrol-yakosti", "h.s1", ("Контроль якості замороженої малини та ожини в хабі", "Quality check of frozen raspberries and blackberries at the hub"),
               ("01–02 · Вирощування та приймання", "01–02 · Growing and intake"), ("Ягода в холоді вже за кілька годин після збору", "Berries are chilled within hours of picking"),
               [("Сімейні господарства вирощують ягоди під супроводом агрономів кооперативу. Дванадцять пунктів приймання стоять поруч із плантаціями: кожну партію оглядають, зважують і маркують — так ми зберігаємо простежуваність до кожного виробника.",
                 "Family farms grow berries with support from the cooperative's agronomists. Twelve collection points stand next to the plantations: every lot is inspected, weighed and labelled, so traceability reaches each individual grower.")])
    b += split("sortuvannya", "h.s2", ("Ручне сортування замороженої малини на конвеєрі", "Hand sorting of frozen raspberries on a conveyor"),
               ("03–05 · Заморожування, сортування, зберігання", "03–05 · Freezing, sorting, storage"), ("IQF при −35 °C і сортування за класами A / B", "IQF at −35 °C and grading into classes A / B"),
               [("У хабі в Городищі кожна ягода замерзає окремо й зберігає форму, колір і смак. Потім продукцію калібрують за специфікацією покупця й зберігають при −18 °C на складах до 300 т — холодовий ланцюг не переривається.",
                 "At the Horodyshche hub every berry is frozen individually and keeps its shape, colour and taste. The product is then graded to the buyer's specification and stored at −18 °C in warehouses of up to 300 t — the cold chain is never broken.")], "bg-mint", True)
    b += split("pakuvannya", "h.s3", ("Заморожена малина в коробці з харчовим вкладишем", "Frozen raspberries in a carton with a food-grade liner"),
               ("06 · Пакування та експорт", "06 · Packing and export"), ("Швеція, Німеччина, Франція, Канада, США", "Sweden, Germany, France, Canada, USA"),
               [("Фасуємо продукцію у формат, потрібний партнеру, зокрема під його торговою маркою. Власна логістика доставляє вантаж за погодженим графіком із повним пакетом експортних документів.",
                 "We pack in the format each partner needs, including under their own brand. Our own logistics deliver on an agreed schedule with a full set of export documents.")], "bg-peach")
    berries = [("raspberry", "Малина", "Raspberry", True)] + [(k, u, e, False) for k, u, e in [("strawberry", "Полуниця", "Strawberry"), ("wild", "Суниця", "Wild strawberry"), ("blueberry", "Лохина", "Blueberry"), ("blackberry", "Ожина", "Blackberry"), ("currant", "Смородина", "Black currant"), ("redcurrant", "Порічки", "Red currant"), ("cherry", "Вишня", "Sour cherry"), ("seabuckthorn", "Обліпиха", "Sea buckthorn"), ("elder", "Бузина", "Elderberry"), ("viburnum", "Калина", "Viburnum")]]
    chips = "".join(f'<li class="chip">{E("span", "berry." + k, u, e)}</li>' for k, u, e, main in berries)
    b += f"""<section class="wrap py-20 grid gap-14 lg:grid-cols-2" data-aos="fade-up">
  <div>{head("h.range", "Асортимент", "Product range", "Ягоди, які ми пропонуємо", "The berries we offer")}
    {E("p", "h.range.p", "Наша головна культура — малина. Україна вже другий рік поспіль є світовим лідером з експорту замороженої малини, і Західна Україна — один з її ключових регіонів.", "Our main crop is raspberry. Ukraine has been the world's leading exporter of frozen raspberries for the second year in a row, and Western Ukraine is one of its key regions.", "txt")}
    <ul class="flex flex-wrap gap-2.5 mb-5">{chips}</ul>
    {E("p", "h.range.f", "Формати: ціла ягода, crumble, суміші. Пакування 10 кг або 300 г – 1 кг під маркою покупця.", "Formats: whole berries, crumble, mixes. Packed in 10 kg cartons or 300 g – 1 kg retail packs under the buyer's brand.", "text-muted")}
  </div>
  <div class="border-t-[6px] border-leaf bg-cloud p-8 md:p-10 rounded-b-md">
    {E("p", "h.q.label", "Якість і безпечність", "Quality and safety", "label")}<h2 class="h2">ISO 22000:2018 · FSSC 22000</h2>{leaf()}
    {E("p", "h.q.p", "Стандарти, які визнають провідні роздрібні мережі та виробники харчової продукції Європи й Північної Америки.", "Standards recognised by leading retailers and food manufacturers in Europe and North America.", "txt")}
    <ul class="list-disc pl-5 mb-6 text-[17px] leading-loose text-body">{E("li", "h.q.1", "Безперервний холодовий ланцюг", "Unbroken cold chain")}{E("li", "h.q.2", "Простежуваність партії до виробника", "Lot traceability to the grower")}{E("li", "h.q.3", "Контроль на кожному етапі", "Control at every stage")}{E("li", "h.q.4", "Лабораторні дослідження в акредитованих лабораторіях", "Testing in accredited laboratories")}</ul>
    {btn("contacts.html#form", "h.q.btn", "Запросити сертифікати", "Request certificates", "btn-green")}
  </div>
</section>
<div class="grid md:grid-cols-2 bg-forest text-white">
  <div class="px-6 md:px-16 py-16" data-aos="fade-up">{head("h.geo", "Географія", "Geography", "Мережа приймання та хаб у Городищі", "Collection network and the Horodyshche hub", light=True)}
    {E("p", "h.geo.p", "Пункти приймання розташовані безпосередньо в громадах, де вирощують ягоди. Звідти сировина швидко потрапляє до центрального хабу в Городищі неподалік Тернополя.", "Collection points are located right in the communities where berries are grown. From there the fruit quickly reaches the central hub in Horodyshche near Ternopil.", "txt text-[#E6E7E8]")}
    <p class="mb-2 flex items-center gap-2"><span class="dot bg-berry" aria-hidden="true"></span>{E("span", "h.geo.hub", "Хаб «Файна поляна» — с. Городище", "Faina Polyana hub — Horodyshche")}</p>
    <p class="flex items-center gap-2"><span class="dot bg-sprout" aria-hidden="true"></span>{E("span", "h.geo.pts", "12 пунктів: Козова, Бережани, Підгайці, Зборів, Збараж, Теребовля, Бучач, Чортків, Монастириська, Рогатин, Бурштин, Галич", "12 points: Kozova, Berezhany, Pidhaitsi, Zboriv, Zbarazh, Terebovlia, Buchach, Chortkiv, Monastyryska, Rohatyn, Burshtyn, Halych")}</p>
  </div>
  <div class="p-6 md:p-12 flex items-center bg-[#35553A]">{map_svg("map.h")}</div>
</div>
<section class="wrap py-20 grid gap-14 lg:grid-cols-2 items-center" data-aos="fade-up">
  <div>{E("p", "h.mkt.label", "Ринок", "Market", "label")}{E("p", "h.mkt.num", "€250,8 млн", "€250.8 million", "font-slab font-bold text-5xl md:text-6xl text-berry mb-3")}
    {E("p", "h.mkt.p", "виручка України від експорту замороженої малини в сезоні 2025/26 (63,3 тис. т). Ми прагнемо, щоб українська ягода продавалася під власним, українським ім'ям.", "Ukraine's revenue from frozen raspberry exports in the 2025/26 season (63,300 t). We want Ukrainian berries to be sold under their own, Ukrainian name.", "txt")}
    {E("p", "h.mkt.src", "Джерело: Асоціація «Ягідництво України»", "Source: Ukrainian Berries Association", "text-sm text-muted")}</div>
  <div class="grid grid-cols-2 gap-7">
    <div class="tile border-t-[3px] border-berry pt-3">{E("h3", "h.w1.t", "Власні потужності", "Own facilities", "font-slab font-bold")}{E("p", "h.w1.d", "Заморожування, сортування й зберігання під одним дахом.", "Freezing, sorting and storage under one roof.", "mt-1 text-body")}</div>
    <div class="tile border-t-[3px] border-leaf pt-3">{E("h3", "h.w2.t", "Сертифікована якість", "Certified quality", "font-slab font-bold")}<p class="mt-1 text-body">ISO 22000 · FSSC 22000</p></div>
    <div class="tile border-t-[3px] border-orange pt-3">{E("h3", "h.w3.t", "Прозорість", "Transparency", "font-slab font-bold")}{E("p", "h.w3.d", "Простежуваність від ділянки до контейнера.", "Traceability from plot to container.", "mt-1 text-body")}</div>
    <div class="tile border-t-[3px] border-stone pt-3">{E("h3", "h.w4.t", "Надійність", "Reliability", "font-slab font-bold")}{E("p", "h.w4.d", "153 виробники, десять років роботи.", "153 producers, ten years in business.", "mt-1 text-body")}</div>
  </div>
</section>
"""
    news = [("sklad-novyi", "12.11.2026", "Добудовано новий склад заморожених ягід", "New frozen-berry warehouse completed", "bg-berrydk"),
            ("sklad", "03.10.2026", "Сезон 2026: понад 800 т переробленої ягоди", "Season 2026: over 800 t of berries processed", "bg-orangetx"),
            ("sila-kooperatyviv", "18.09.2026", "«Файна поляна» — на форумі «Сила кооперативів»", "Faina Polyana at the “Power of Cooperatives” forum", "bg-leafdk")]
    cards = "".join(f'<article class="card overflow-hidden">{img(n, f"h.news{i}.alt", t_uk, t_en, "w-full h-52 object-cover", "(min-width: 768px) 33vw, 100vw")}<div class="p-6"><p class="inline-block {c} text-white text-xs font-bold rounded-full px-3 py-1 mb-3"><time datetime="{d[6:]}-{d[3:5]}-{d[:2]}">{d}</time></p>{E("h3", f"h.news{i}", t_uk, t_en, "font-slab font-bold text-lg leading-snug")}</div></article>'
                    for i, (n, d, t_uk, t_en, c) in enumerate(news))
    b += section(head("h.news", "Новини кооперативу", "Cooperative news", "Останні події", "Latest updates") + f'<div class="grid gap-8 md:grid-cols-3">{cards}</div>'
                 + E("p", "h.news.demo", "Новини в демо-версії — демонстраційні.", "News items in this demo are for demonstration only.", "text-sm text-muted mt-6"), "bg-cloud")
    return (page_head("index.html", "meta.home", "Файна поляна — ягідний кооператив із Тернопільщини", "Faina Polyana — berry cooperative from Ukraine",
                      "СК «Файна поляна»: 153 сімейні господарства, власне заморожування IQF, сортування A/B, сертифікати ISO 22000 і FSSC 22000 та прямий експорт ягід до Європи й Північної Америки.",
                      "Faina Polyana cooperative: 153 family farms, in-house IQF freezing, A/B grading, ISO 22000 and FSSC 22000 certification and direct berry exports to Europe and North America.")
            + header("index.html") + b + footer())


# ================================================================ PARTNERS
def page_partners():
    b = hero("p.hero", ("Для покупців, інвесторів і міжнародних програм", "For buyers, investors and international programmes"),
             ("Партнерство, побудоване на якості та прозорості", "A partnership built on quality and transparency"),
             ("«Файна поляна» — не трейдер і не посередник. Це 153 українські виробники, які самі вирощують, заморожують, сортують і продають свої ягоди.",
              "Faina Polyana is neither a trader nor a middleman. We are 153 Ukrainian growers who grow, freeze, sort and sell our own berries."),
             btn("contacts.html?type=buyer#form", "p.hero.b1", "Запросити пропозицію", "Request an offer") + btn("#investors", "p.hero.b2", "Інвесторам", "For investors", "btn-out"))
    who = [("Виробники харчової продукції", "Food manufacturers", "Йогурти, десерти, випічка, джеми, соки й снеки: ягода стабільного калібру та якості за вашою специфікацією, з повним пакетом документів.", "Yogurts, desserts, bakery, jams, juices and snacks: berries of consistent size and quality to your specification, with full documentation."),
           ("Дистриб'ютори та імпортери", "Distributors and importers", "Прямі контракти на сезон або кілька сезонів, стабільні обсяги й фасування під вашою торговою маркою.", "Direct contracts for one or several seasons, stable volumes and packing under your own brand."),
           ("Роздрібні мережі", "Retail chains", "Сертифікація FSSC 22000 відповідає вимогам GFSI, які висувають провідні мережі Європи та Північної Америки.", "FSSC 22000 certification meets the GFSI requirements of leading retailers in Europe and North America."),
           ("Переробні підприємства", "Processors", "Для глибокої переробки — продукція класу B: якісна сировина за доступною ціною.", "For further processing we offer class B product: quality raw material at an affordable price.")]
    colors = ["bg-berrydk", "bg-orangetx", "bg-leafdk", "bg-stone"]
    who_html = "".join(f'<div class="card p-7"><span class="num-circle {colors[i]} ring-black/5 mb-5" aria-hidden="true">{i + 1}</span>{E("h3", f"p.who{i}.t", tu, te, "font-slab font-bold text-xl mb-2")}{E("p", f"p.who{i}.d", du, de, "text-body leading-relaxed")}</div>' for i, (tu, te, du, de) in enumerate(who))
    b += section(head("p.who", "Кому ми корисні", "Who we serve", "З ким ми працюємо", "Who we work with", True) + f'<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">{who_html}</div>', "bg-cloud")
    ben = [("Пряме походження", "Direct origin", "Ви купуєте ягоду безпосередньо в тих, хто її виростив: без перекупників, зайвих націнок і втраченої інформації про походження.", "You buy berries directly from those who grew them: no resellers, no extra mark-ups and no lost information about origin."),
           ("Передбачувана якість", "Predictable quality", "Агрономічний супровід, приймання поблизу плантацій, IQF і сортування A/B: кожна партія відповідає погодженій специфікації.", "Agronomic support, intake close to the plantations, IQF and A/B grading: every lot meets the agreed specification."),
           ("Повна простежуваність", "Full traceability", "На запит надаємо дані про кожну партію: виробника, дату приймання, дату заморожування й номер партії.", "On request we provide data for every lot: grower, intake date, freezing date and lot number."),
           ("Гнучкі формати", "Flexible formats", "Коробки по 10 кг із харчовим вкладишем, роздрібне фасування 300 г – 1 кг, private label; мінімальна партія — від 20 т.", "10 kg cartons with food-grade liners, 300 g – 1 kg retail packs, private label; minimum order from 20 t."),
           ("Надійність поставок", "Reliable supply", "Сировинна база зі 153 господарств і холодильне зберігання на 300 т дозволяють планувати поставки на весь рік.", "A supply base of 153 farms and 300 t of cold storage let us plan deliveries all year round."),
           ("Документальна підтримка", "Documentation", "Сертифікат походження, фітосанітарний сертифікат, лабораторні протоколи та специфікація партії.", "Certificate of origin, phytosanitary certificate, laboratory reports and lot specification.")]
    dots = ["bg-berry", "bg-orange", "bg-leaf", "bg-rose", "bg-sprout", "bg-stone"]
    ben_html = "".join(f'<div class="flex gap-4"><span class="dot {dots[i]} mt-2" aria-hidden="true"></span><div>{E("h3", f"p.ben{i}.t", tu, te, "font-slab font-bold text-xl mb-1")}{E("p", f"p.ben{i}.d", du, de, "text-body leading-relaxed")}</div></div>' for i, (tu, te, du, de) in enumerate(ben))
    b += section(head("p.ben", "Переваги", "Benefits", "Що отримує партнер", "What partners get") + f'<div class="grid gap-10 md:grid-cols-2 lg:grid-cols-3">{ben_html}</div>', sid="benefits")
    inv = [("Інвестиції в потужності", "Capacity investment", "Співфінансування програми «Городище 2028»: другий тунель IQF, оптичне сортування, логістичний центр і склад на 1000 т.", "Co-financing the “Horodyshche 2028” programme: a second IQF tunnel, optical sorting, a logistics centre and 1,000 t of cold storage.", "bg-berry"),
           ("Кредити й лізинг обладнання", "Loans and equipment leasing", "Довгострокове фінансування холодильного, сортувального та пакувального обладнання від банків і фінансових інституцій розвитку.", "Long-term financing of cooling, sorting and packing equipment from banks and development finance institutions.", "bg-orange"),
           ("Гранти й технічна допомога", "Grants and technical assistance", "Спільні проєкти з донорськими програмами: розвиток кооперації, навчання виробників, енергонезалежність.", "Joint projects with donor programmes: cooperative development, grower training, energy independence.", "bg-leaf"),
           ("Тендери та закупівлі", "Tenders and procurement", "Участь у міжнародних тендерах на постачання замороженої ягоди з повним пакетом документів і сертифікатів.", "Taking part in international tenders for frozen berry supply with a full set of documents and certificates.", "bg-rose")]
    inv_html = "".join(f'<div class="card p-7 border-t-4 border-white"><span class="dot {c} mb-4" aria-hidden="true"></span>{E("h3", f"p.inv{i}.t", tu, te, "font-slab font-bold text-xl mb-2")}{E("p", f"p.inv{i}.d", du, de, "text-body leading-relaxed")}</div>' for i, (tu, te, du, de, c) in enumerate(inv))
    trust = [("Прозора звітність перед членами та ревізійна комісія", "Transparent reporting to members and an audit committee"),
             ("Сертифікований процес: ISO 22000 і FSSC 22000", "Certified process: ISO 22000 and FSSC 22000"),
             ("Десять років роботи й власні активи — хаб понад 3000 м²", "Ten years in business and own assets — a hub of over 3,000 m²"),
             ("Соціальний ефект: доходи 153 сімей у селах Західної України", "Social impact: income for 153 families in Western Ukrainian villages")]
    tr_html = "".join(f'<li class="flex gap-3"><span class="dot bg-sprout mt-2" aria-hidden="true"></span>{E("span", f"p.trust{i}", u, e)}</li>' for i, (u, e) in enumerate(trust))
    b += f'<section id="investors" class="bg-forest text-white"><div class="wrap py-20" data-aos="fade-up">' + head("p.inv", "Інвестиції", "Investment", "Інвесторам, фондам і донорським програмам", "For investors, funds and donor programmes", light=True,
                lead=("Партнерство з «Файною поляною» — це не лише закупівля ягоди. Ми відкриті до інвестицій, кредитування, грантів і тендерів від західних фінансових інституцій, фондів і програм розвитку.",
                      "Partnering with Faina Polyana is not only about buying berries. We are open to investment, lending, grants and tenders from Western financial institutions, funds and development programmes.")) \
         + f'<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4 text-graphite">{inv_html}</div>' \
         + f'<div class="mt-12 grid gap-8 lg:grid-cols-[1fr_auto] items-center"><div>{E("h3", "p.trust.t", "Чому кооператив — надійний партнер для інвестицій", "Why the cooperative is a reliable investment partner", "font-slab font-bold text-2xl mb-4")}<ul class="grid gap-2 text-lg text-[#E6E7E8] md:grid-cols-2">{tr_html}</ul></div>' \
         + btn("contacts.html?type=investor#form", "p.inv.btn", "Заявка для інвесторів", "Investor inquiry", "btn bg-white text-forest hover:bg-mint") + '</div></div></section>\n'
    figures = "".join(f'<li class="flex justify-between gap-4 border-b border-[#CFE3C2] py-2"><span data-i18n="{k}">{esc(u)}</span><b class="font-slab">{v}</b></li>' for k, u, v in
                      [("p.org.f1", "Виробники-учасники", "153"), ("p.org.f2", "Громади", "10"), ("p.org.f3", "Насадження, га", "100+"), ("p.org.f4", "Пункти приймання", "12"), ("p.org.f5", "Площа хабу, м²", "3000+")])
    for k, e in [("p.org.f1", "Member producers"), ("p.org.f2", "Communities"), ("p.org.f3", "Plantations, ha"), ("p.org.f4", "Collection points"), ("p.org.f5", "Hub area, m²")]:
        EN[k] = e
    b += split("sila-kooperatyviv", "p.org", ("Учасники форуму «Сила кооперативів»", "Participants of the “Power of Cooperatives” forum"),
               ("Як ми влаштовані", "How we are organised"), ("Кооператив як модель бізнесу", "The cooperative as a business model"),
               [("«Файна поляна» — сільськогосподарський кооператив, заснований у 2015 році за класичною європейською моделлю. Кожен член — власник своєї землі та співвласник спільних потужностей.",
                 "Faina Polyana is an agricultural cooperative founded in 2015 on the classic European model. Each member owns their land and co-owns the shared facilities."),
                ("Виробники зацікавлені в якості, бо отримують частку доданої вартості; рішення ухвалюються колективно й прозоро, а стабільність закладена в саму модель — кооператив не залежить від одного власника.",
                 "Growers care about quality because they share in the added value; decisions are made collectively and transparently, and stability is built into the model — the cooperative does not depend on a single owner.")],
               "bg-mint", extra=f'<ul class="mt-2">{figures}</ul>')
    team = [("ТА", "Тарас Андрійчук", "Taras Andriichuk", "Голова правління", "Chairman of the Board", "Стратегія розвитку, експортні напрями та робота з ключовими партнерами.", "Development strategy, export markets and key partner relations.", "bg-berrydk", False),
            ("ОК", "Олена Коваль", "Olena Koval", "Комерційний директор", "Commercial Director", "Переговори з іноземними покупцями, контракти та графіки поставок.", "Negotiations with foreign buyers, contracts and delivery schedules.", "bg-orangetx", True),
            ("ВМ", "Василь Мельник", "Vasyl Melnyk", "Головний агроном", "Chief Agronomist", "Супровід виробників: сорти, технології, захист рослин, терміни збору.", "Grower support: varieties, techniques, crop protection, harvest timing.", "bg-leafdk", True),
            ("ІС", "Ігор Савчук", "Ihor Savchuk", "Керівник виробництва", "Head of Production", "Заморожування, сортування, зберігання та система FSSC 22000.", "Freezing, sorting, storage and the FSSC 22000 system.", "bg-stone", True),
            ("МГ", "Марія Гнатюк", "Mariia Hnatiuk", "Менеджер з експорту", "Export Manager", "Документи, логістика й супровід кожної поставки.", "Documents, logistics and support for every shipment.", "bg-rose", True)]
    team_html = ""
    for i, ini_en in enumerate(["TA", "OK", "VM", "IS", "MH"]):
        EN[f"p.team{i}.ini"] = ini_en
    for i, (ini, nu, ne, ru, re, du, de, c, demo) in enumerate(team):
        team_html += (f'<div class="card p-6 text-center"><span class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full {c} text-white font-slab font-bold text-2xl" aria-hidden="true" data-i18n="p.team{i}.ini">{ini}</span>'
                      + E("h3", f"p.team{i}.n", nu, ne, "font-slab font-bold text-lg") + E("p", f"p.team{i}.r", ru, re, "text-leafdk font-medium mb-2")
                      + E("p", f"p.team{i}.d", du, de, "text-sm text-body leading-relaxed")
                      + (E("p", "p.team.demo", "демо", "demo", "mt-3 inline-block rounded-full bg-cloud px-2 py-0.5 text-xs text-muted") if demo else "") + "</div>")
    b += section(head("p.team", "Керівництво", "Leadership", "Команда, яка веде кооператив", "The team behind the cooperative", True) + f'<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-5">{team_html}</div>')
    struct = [("Загальні збори членів", "General meeting of members", "Найвищий орган: стратегія, плани розвитку, розподіл доходу.", "Highest body: strategy, development plans, profit distribution.", "border-berry"),
              ("Правління", "Board", "Щоденне управління, продажі, переговори з партнерами.", "Day-to-day management, sales, partner negotiations.", "border-orange"),
              ("Ревізійна комісія", "Audit committee", "Контроль фінансової діяльності, звіт перед зборами.", "Oversight of finances, reports to the general meeting.", "border-stone")]
    units = [("Агрономічна служба", "Agronomy"), ("Виробництво", "Production"), ("Логістика", "Logistics")]
    s_html = "".join(f'<div class="card p-6 border-t-4 {c}">{E("h3", f"p.st{i}.t", tu, te, "font-slab font-bold text-lg mb-1")}{E("p", f"p.st{i}.d", du, de, "text-body")}</div>' for i, (tu, te, du, de, c) in enumerate(struct))
    u_html = "".join(E("li", f"p.unit{i}", u, e, "chip") for i, (u, e) in enumerate(units))
    b += section(head("p.st", "Структура", "Structure", "Хто стоїть за кожною ягодою", "Who stands behind every berry")
                 + f'<div class="grid gap-6 md:grid-cols-3 mb-8">{s_html}</div><ul class="flex flex-wrap justify-center gap-3 mb-8">{u_html}</ul>'
                 + f'<p class="mx-auto max-w-xl rounded-full bg-leafdk text-white text-center font-slab font-bold text-lg px-6 py-4" data-i18n="p.st.base">{esc("153 виробники-учасники — основа кооперативу")}</p>', "bg-cloud")
    EN["p.st.base"] = "153 member producers — the foundation of the cooperative"
    countries = [("Швеція", "Sweden"), ("Німеччина", "Germany"), ("Франція", "France"), ("Канада", "Canada"), ("США", "USA")]
    chips = "".join(E("li", f"c.{e.lower()}", u, e, "chip") for u, e in countries)
    b += split("forum-shvetsiya", "p.geo", ("Презентація кооперативу на заході за підтримки Швеції", "Presenting the cooperative at an event supported by Sweden"),
               ("Географія поставок", "Where we ship"), ("Де вже працюють з нами", "Where partners already work with us"),
               [("Сьогодні наша продукція постачається партнерам у п'яти країнах. Ми прагнемо розширювати присутність у ЄС, Великій Британії та Північній Америці й відкриті до переговорів з партнерами з інших регіонів.",
                 "Today our products go to partners in five countries. We aim to grow our presence in the EU, the UK and North America and are open to talks with partners from other regions.")],
               "bg-peach", True, extra=f'<ul class="flex flex-wrap gap-2.5">{chips}</ul>')
    vals = [("Чесність", "Honesty", "Продаємо українську ягоду під її справжнім ім'ям і з відомим походженням.", "We sell Ukrainian berries under their real name and with known origin."),
            ("Відповідальність", "Responsibility", "За кожну партію відповідає кооператив загалом, а не анонімний постачальник.", "Every lot is the responsibility of the whole cooperative, not an anonymous supplier."),
            ("Громада", "Community", "Наш успіх — це доходи 153 сімей і робочі місця в селах Тернопільщини.", "Our success means income for 153 families and jobs in Ternopil villages."),
            ("Розвиток", "Growth", "Щороку інвестуємо в потужності, сертифікацію та навчання виробників.", "Every year we invest in facilities, certification and grower training.")]
    tops = ["border-berry", "border-leaf", "border-orange", "border-stone"]
    v_html = "".join(f'<div class="tile border-t-[3px] {tops[i]} pt-3">{E("h3", f"p.val{i}.t", tu, te, "font-slab font-bold text-lg")}{E("p", f"p.val{i}.d", du, de, "mt-1 text-body")}</div>' for i, (tu, te, du, de) in enumerate(vals))
    b += section(head("p.val", "Цінності", "Values", "На чому тримається наша робота", "What our work stands on", True) + f'<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">{v_html}</div>')
    return (page_head("partners.html", "meta.partners", "Партнерам — Файна поляна", "For partners — Faina Polyana",
                      "Співпраця з СК «Файна поляна»: пряме походження ягід, сортування A/B, private label, FSSC 22000, повна простежуваність партій і стабільні поставки.",
                      "Work with Faina Polyana: direct origin, A/B grading, private label, FSSC 22000, full lot traceability and stable supply.")
            + header("partners.html") + b + footer())


# ================================================================ PLANS
def page_plans():
    b = hero("pl.hero", ("Розвиток кооперативу", "Cooperative development"), ("Ростемо разом із нашими партнерами", "Growing together with our partners"),
             ("За десять років ми пройшли шлях від кількох сімейних господарств до одного з найбільших ягідних кооперативів Західної України — і щосезону інвестуємо в потужності, якість і нові ринки.",
              "In ten years we have grown from a few family farms into one of the largest berry cooperatives in Western Ukraine — and every season we invest in capacity, quality and new markets."))
    tl = [("2015", "Засновано кооператив за європейською моделлю кооперації.", "The cooperative is founded on the European cooperative model.", "bg-berry"),
          ("2016", "Перший сезон спільного збуту великими партіями.", "First season of joint sales in large lots.", "bg-orange"),
          ("2017", "Викуплено майданчик у Городищі під власний хаб.", "The Horodyshche site is bought for our own hub.", "bg-leaf"),
          ("2018", "Перший в Україні кооперативний цех шокового заморожування, 15 т/добу.", "Ukraine's first cooperative blast-freezing facility, 15 t/day.", "bg-berry"),
          ("2019", "Перші експортні поставки до країн ЄС.", "First exports to EU countries.", "bg-orange"),
          ("2020", "Перші чотири пункти приймання й власна логістика.", "The first four collection points and our own logistics.", "bg-leaf"),
          ("2021", "Сертифікат ISO 22000:2018.", "ISO 22000:2018 certification.", "bg-berry"),
          ("2022", "Сезон без зупинок попри повномасштабну війну.", "A season without stoppages despite the full-scale war.", "bg-orange"),
          ("2023", "Перші поставки до Канади та США.", "First shipments to Canada and the USA.", "bg-leaf"),
          ("2024", "Сертифікат FSSC 22000.", "FSSC 22000 certification.", "bg-berry"),
          ("2025", "Новий склад заморожених ягід понад 650 м².", "New frozen-berry warehouse of over 650 m².", "bg-orange"),
          ("2026", "153 виробники, понад 800 т за сезон, п'ять країн експорту.", "153 producers, over 800 t per season, five export countries.", "bg-leaf")]
    tl_items = [f'<li class="relative pl-10 pb-8"><span class="absolute left-0 top-1 h-5 w-5 rounded-full {c} ring-4 ring-white" aria-hidden="true"></span><p class="font-slab font-bold text-xl">{y}</p>{E("p", f"pl.tl.{y}", u, e, "text-body")}</li>' for y, u, e, c in tl]
    b += section(head("pl.tl", "Наш шлях", "Our journey", "Десять років розвитку", "Ten years of growth", True)
                 + f'<div class="mx-auto grid max-w-5xl gap-x-16 md:grid-cols-2">' + "".join(f'<ol class="relative border-l-2 border-dashed border-[#C9D8BC] [&>li]:-ml-[11px]"{" start=" + chr(34) + "7" + chr(34) if k else ""}>{"".join(tl_items[k * 6:(k + 1) * 6])}</ol>' for k in (0, 1)) + '</div>'
                 + E("p", "pl.tl.demo", "Частина дат у демо-версії орієнтовна.", "Some dates in this demo are approximate.", "text-center text-sm text-muted"), "bg-cloud")
    b += split("sklad-novyi", "pl.hub", ("Новий склад заморожених ягід у Городищі", "The new frozen-berry warehouse in Horodyshche"),
               ("Хаб у Городищі", "The Horodyshche hub"), ("Що є сьогодні і яким він буде", "What it is today and what it will become"),
               [("Колись тут була тракторна бригада, а сьогодні — понад 3000 м² виробничих приміщень: тунель шокового заморожування, лінія сортування, холодильні склади на 300 т і новий склад понад 650 м².",
                 "This used to be a tractor yard; today it is over 3,000 m² of production space: a blast-freezing tunnel, a sorting line, 300 t of cold storage and a new warehouse of over 650 m²."),
                ("Програма модернізації «Городище 2028» до 2028 року збільшить потужність заморожування до 30 т на добу, зберігання — до 1000 т, а переробку — до 1500 т за сезон.",
                 "The “Horodyshche 2028” modernisation programme will raise freezing capacity to 30 t per day, storage to 1,000 t and processing to 1,500 t per season by 2028.")])
    stages = [("Етап 1", "Stage 1", "Новий склад заморожених ягід, 650 м²", "New frozen-berry warehouse, 650 m²", "Завершено 2025", "Completed 2025", "bg-leafdk"),
              ("Етап 2", "Stage 2", "Другий тунель IQF і оптична лінія сортування", "Second IQF tunnel and optical sorting line", "Триває · до сезону 2027", "In progress · by season 2027", "bg-orangetx"),
              ("Етап 3", "Stage 3", "Логістичний центр на 700 т і цех фасування", "700 t logistics centre and packing workshop", "Заплановано 2028", "Planned 2028", "bg-stone")]
    st_html = "".join(f'<div class="card p-7">{E("p", f"pl.stg{i}.n", nu, ne, "label")}{E("h3", f"pl.stg{i}.t", tu, te, "font-slab font-bold text-xl mb-4")}{E("p", f"pl.stg{i}.s", su, se, f"inline-block rounded-full {c} px-3 py-1 text-sm font-bold text-white")}</div>' for i, (nu, ne, tu, te, su, se, c) in enumerate(stages))
    b += section(head("pl.stg", "Городище 2028", "Horodyshche 2028", "Три етапи модернізації", "Three stages of modernisation") + f'<div class="grid gap-6 md:grid-cols-3">{st_html}</div>'
                 + E("p", "pl.stg.3d", "Інтерактивну 3D-модель хабу додамо в наступній версії сайту.", "An interactive 3D model of the hub will be added in the next version of the site.", "mt-6 text-sm text-muted"))
    b += split("sklad", "pl.store", ("Холодильний склад зі стелажами готової продукції", "Cold store with racks of finished products"),
               ("Зберігання", "Storage"), ("Більше холоду — більше можливостей", "More cold storage, more possibilities"),
               [("До 2028 року розширюємо холодильне зберігання з 300 до 1000 т. Це дозволить постачати продукцію рівномірно протягом року, формувати великі партії під одну специфікацію та пропонувати стабільні ціни за довгостроковими контрактами.",
                 "By 2028 we are expanding cold storage from 300 to 1,000 t. This lets us supply evenly throughout the year, build large lots to a single specification and offer stable prices under long-term contracts.")],
               "bg-mint", True)
    b += section(head("pl.energy", "Енергонезалежність", "Energy independence", "Холод, який не залежить від мережі", "Cold that does not depend on the grid")
                 + E("p", "pl.energy.p", "У 2026–2027 роках встановлюємо сонячну електростанцію на 300 кВт і систему накопичення енергії. Разом із резервними генераторами це гарантує безперервність холодового ланцюга навіть під час відключень.", "In 2026–2027 we are installing a 300 kW solar plant and an energy storage system. Together with backup generators this keeps the cold chain running even during power outages.", "txt max-w-3xl"), "bg-peach")
    rows = [("Обсяг переробки за сезон", "Processing volume per season", "800+ т", "1500 т"), ("Потужність заморожування", "Freezing capacity", "15 т/добу", "30 т/добу"),
            ("Холодильне зберігання", "Cold storage", "300 т", "1000 т"), ("Виробники-учасники", "Member producers", "153", "250"), ("Країни експорту", "Export countries", "5", "8"),
            ("Частка продукції під маркою покупця", "Share of private-label products", "—", "20%")]
    unit_en = {"800+ т": "800+ t", "1500 т": "1,500 t", "15 т/добу": "15 t/day", "30 т/добу": "30 t/day", "300 т": "300 t", "1000 т": "1,000 t"}
    tr = "".join(f'<tr>{E("td", f"pl.g{i}", u, e)}{E("td", f"pl.g{i}a", a, unit_en.get(a, a))}{E("td", f"pl.g{i}c", c, unit_en.get(c, c), "font-bold text-leafdk")}</tr>' for i, (u, e, a, c) in enumerate(rows))
    b += section(head("pl.goals", "Економічні цілі", "Economic goals", "Цифри, до яких ми рухаємось", "The figures we are working towards", True)
                 + f'<div class="overflow-x-auto rounded-md border border-line"><table class="table-fp min-w-[560px]">{E("caption", "pl.goals.cap", "Показники кооперативу: 2026 рік і ціль на 2028 рік (демо-дані)", "Cooperative indicators: 2026 and the 2028 target (demo data)", "sr-only")}<thead><tr>{E("th", "pl.goals.c1", "Показник", "Indicator", "", ' scope="col"')}<th scope="col">2026</th>{E("th", "pl.goals.c3", "Ціль 2028", "2028 target", "", ' scope="col"')}</tr></thead><tbody>{tr}</tbody></table></div>'
                 + E("p", "pl.goals.p", "Наша стратегія — не лише збільшувати обсяги, а й нарощувати частку доданої вартості, яка залишається в Україні.", "Our strategy is not just to grow volumes but to increase the share of added value that stays in Ukraine.", "txt mt-6"))
    strat = [("Нові ринки", "New markets", "Велика Британія, Нідерланди, Японія; виставки Fruit Logistica і SIAL.", "UK, Netherlands, Japan; Fruit Logistica and SIAL trade fairs."),
             ("Якість", "Quality", "Підтримка FSSC 22000, підготовка до BRCGS та органічної лінії.", "Maintaining FSSC 22000, preparing for BRCGS and an organic line."),
             ("Нові продукти", "New products", "Ягідні суміші, малиновий crumble, ягідне пюре.", "Berry mixes, raspberry crumble, berry purée."),
             ("Виробники", "Growers", "Навчання, саджанці ремонтантних сортів, крапельне зрошення.", "Training, remontant variety seedlings, drip irrigation."),
             ("Громада", "Community", "Робочі місця та підтримка шкіл і медзакладів Козівської громади.", "Jobs and support for schools and clinics in the Kozova community.")]
    s_html = "".join(f'<div>{E("h3", f"pl.s{i}.t", tu, te, "font-slab font-bold text-lg mb-1")}{E("p", f"pl.s{i}.d", du, de, "text-body")}</div>' for i, (tu, te, du, de) in enumerate(strat))
    b += section(head("pl.strat", "Стратегія", "Strategy", "Куди ми рухаємось", "Where we are heading") + f'<div class="grid gap-8 md:grid-cols-3 lg:grid-cols-5">{s_html}</div>'
                 + f'<div class="mt-12 rounded-md bg-forest p-8 md:p-10 text-white">{E("h3", "pl.inv.t", "Відкриті до спільних проєктів", "Open to joint projects", "font-slab font-bold text-2xl mb-2")}{E("p", "pl.inv.p", "Довгострокові контракти з передоплатою, спільні проєкти розширення потужностей, програми міжнародної технічної допомоги.", "Long-term prepaid contracts, joint capacity expansion projects and international technical assistance programmes.", "text-[#E6E7E8] mb-6")}{btn("contacts.html#form", "pl.inv.b", "Обговорити співпрацю", "Discuss cooperation", "btn bg-white text-forest hover:bg-mint")}</div>', "bg-cloud")
    return (page_head("plans.html", "meta.plans", "Наші плани — Файна поляна", "Our plans — Faina Polyana",
                      "Розвиток СК «Файна поляна»: програма модернізації хабу «Городище 2028», розширення складу до 1000 т, сонячна станція та економічні цілі кооперативу.",
                      "Faina Polyana development: the “Horodyshche 2028” hub modernisation, cold storage expansion to 1,000 t, a solar plant and economic goals.")
            + header("plans.html") + b + footer())


# ================================================================ INTAKE
def page_intake():
    b = hero("i.hero", ("Для тих, хто вирощує ягоди", "For berry growers"), ("Здавайте ягоди у «Файну поляну»", "Sell your berries to Faina Polyana"),
             ("Чесна ціна, точне зважування й оплата без затримок. Приймаємо малину та інші ягоди на пунктах поруч із вашим домом.",
              "A fair price, accurate weighing and prompt payment. We accept raspberries and other berries at collection points close to your home."),
             btn("#calc", "i.hero.b1", "Розрахувати заробіток", "Calculate earnings") + btn("#points", "i.hero.b2", "Пункти приймання", "Collection points", "btn-out"))
    why = [("Поруч із домом", "Close to home", "Пункти в громадах, працюємо до 21:00.", "Points in your community, open until 21:00."),
           ("Чесні ваги", "Honest scales", "Повірені ваги, зважування при вас.", "Certified scales, weighing in front of you."),
           ("Прозорі ціни", "Transparent prices", "Актуальні ціни — на цій сторінці.", "Current prices are on this page."),
           ("Більше за довідку", "More with a certificate", "+5–10 грн/кг за довідку про дохід.", "+5–10 UAH/kg with an income certificate."),
           ("Премія 50%", "50% premium", "Для членів кооперативу в кінці сезону.", "For members, paid at the end of the season.")]
    circ = ["bg-berry ring-blush", "bg-orangetx ring-peach", "bg-leafdk ring-mint", "bg-rose ring-blush", "bg-leafdk ring-mint"]
    w_html = "".join(f'<div class="text-center"><span class="num-circle mx-auto mb-4 {circ[i]}" aria-hidden="true">{i + 1}</span>{E("h3", f"i.why{i}.t", tu, te, "font-slab font-bold text-lg mb-1")}{E("p", f"i.why{i}.d", du, de, "text-body")}</div>' for i, (tu, te, du, de) in enumerate(why))
    b += section(head("i.why", "Переваги", "Why us", "Чому з нами вигідно", "Why it pays to work with us", True) + f'<div class="grid gap-8 sm:grid-cols-2 lg:grid-cols-5">{w_html}</div>', "bg-cloud")
    # Ціни (рендер з data/data.json)
    b += section(head("i.prices", "Ціни", "Prices", "Ціни на ягоди · сезон 2026", "Berry prices · season 2026",
                      lead=("Ціна за кілограм при здачі на будь-якому пункті приймання. З довідкою про дохід — дорожче на 5–10 грн/кг.",
                            "Price per kilogram at any collection point. With an income certificate you get 5–10 UAH/kg more."))
                 + f'<div id="priceCards" class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{E("p", "i.prices.loading", "Завантажуємо ціни…", "Loading prices…", "text-muted")}</div>'
                 + '<div class="mt-8 text-center"><button type="button" id="priceMore" class="btn-out hidden" aria-expanded="false" aria-controls="priceCards" data-i18n="i.prices.more">Показати ще</button></div>'
                 + E("p", "i.prices.note", "Середні ціни приймання сезону 2026 (демо-дані). Ціни можуть змінюватися протягом сезону.", "Average intake prices for the 2026 season (demo data). Prices may change during the season.", "mt-6 text-sm text-muted text-center"), sid="prices")
    # Калькулятор
    calc = f"""<div class="grid gap-8 lg:grid-cols-2">
  <form id="calcForm" class="card-flat p-6 md:p-8" novalidate>
    <div class="mb-5">{E("label", "i.calc.berry", "Ягода", "Berry", "field-label", ' for="calcBerry"')}
      <select id="calcBerry" name="berry" class="field" aria-describedby="calcBerryErr">{E("option", "i.calc.choose", "Оберіть ягоду", "Choose a berry", "", ' value=""')}</select>
      <p id="calcBerryErr" class="field-error" aria-live="polite"></p></div>
    <div class="mb-5">{E("label", "i.calc.weight", "Вага, кг", "Weight, kg", "field-label", ' for="calcWeight"')}
      <input id="calcWeight" name="weight" type="text" inputmode="decimal" autocomplete="off" class="field" placeholder="12,5" aria-describedby="calcWeightHint calcWeightErr">
      {E("p", "i.calc.hint", "Від 1 до 500 кг за один раз. Можна з комою: 12,5", "From 1 to 500 kg per delivery. Decimals allowed: 12.5", "mt-1.5 text-sm text-muted", ' id="calcWeightHint"')}
      <p id="calcWeightErr" class="field-error" aria-live="polite"></p></div>
    <label class="flex items-start gap-3 mb-6 cursor-pointer"><input id="calcCert" name="cert" type="checkbox" class="mt-1 h-5 w-5 accent-leafdk">{E("span", "i.calc.cert", "За наявності довідки про дохід (+5–10 грн/кг)", "I have an income certificate (+5–10 UAH/kg)")}</label>
    {E("button", "i.calc.btn", "Розрахувати", "Calculate", "btn-red w-full", ' type="submit"')}
    <p id="calcError" class="field-error text-center" role="alert"></p>
  </form>
  <div id="calcResult" class="rounded-md bg-forest p-6 md:p-8 text-white" aria-live="polite">
    {E("p", "i.calc.res", "Ваш результат", "Your result", "label text-pink")}
    <dl class="divide-y divide-white/15">
      <div class="flex justify-between gap-4 py-4">{E("dt", "i.calc.price", "Ціна за кг", "Price per kg", "text-[#E6E7E8]")}<dd id="resPrice" class="font-slab text-xl">—</dd></div>
      <div class="flex justify-between gap-4 py-4">{E("dt", "i.calc.now", "Отримати зараз", "Get paid now", "text-[#E6E7E8]")}<dd id="resNow" class="font-slab text-2xl font-bold">—</dd></div>
      <div class="flex justify-between gap-4 py-4">{E("dt", "i.calc.season", "У кінці сезону (+50%, для членів)", "At season end (+50%, members)", "text-[#E6E7E8]")}<dd id="resSeason" class="font-slab text-2xl font-bold text-sprout">—</dd></div>
      <div class="flex justify-between gap-4 py-4">{E("dt", "i.calc.gain", "Ваша вигода", "Your extra gain", "text-[#E6E7E8]")}<dd id="resGain" class="font-slab text-xl text-pink">—</dd></div>
    </dl>
    {E("p", "i.calc.disclaimer", "Сума орієнтовна: остаточна оплата залежить від фактичної ваги та якості ягоди на прийманні. Оплата в кінці сезону доступна лише членам кооперативу.", "The amount is an estimate: final payment depends on the actual weight and quality of berries at intake. End-of-season payment is available to cooperative members only.", "mt-4 text-sm text-[#C5D3C0]")}
    {E("a", "i.calc.join", "Як стати членом кооперативу →", "How to become a member →", "mt-4 inline-block font-bold text-white underline underline-offset-4", ' href="#member"')}
  </div>
</div>"""
    b += section(head("i.calc", "Калькулятор", "Calculator", "Порахуйте, скільки ви заробите", "See how much you will earn", True,
                      lead=("Оберіть ягоду, вкажіть вагу — і побачите суму одразу.", "Choose a berry, enter the weight and see the amount instantly.")) + calc, "bg-mint", "calc")
    steps = [("Зберіть ягоду", "Pick the berries", "Зранку або ввечері, у чисту неглибоку тару.", "In the morning or evening, into clean shallow crates."),
             ("Привезіть на пункт", "Bring them to a point", "Під час першого візиту — паспорт та ідентифікаційний код.", "On your first visit bring your passport and tax ID."),
             ("Огляд і зважування", "Inspection and weighing", "При вас; ви отримуєте квитанцію з вагою й сумою.", "In front of you; you get a receipt with weight and amount."),
             ("Отримайте оплату", "Get paid", "На картку за 3 робочі дні або в кінці сезону з премією.", "To your card within 3 business days, or at season end with the premium.")]
    st = "".join(f'<div class="card p-6"><span class="num-circle {["bg-berry ring-blush", "bg-orangetx ring-peach", "bg-leafdk ring-mint", "bg-leafdk ring-mint"][i]} mb-4" aria-hidden="true">{i + 1}</span>{E("h3", f"i.st{i}.t", tu, te, "font-slab font-bold text-lg mb-1")}{E("p", f"i.st{i}.d", du, de, "text-body")}</div>' for i, (tu, te, du, de) in enumerate(steps))
    b += section(head("i.how", "Як здати ягоди", "How it works", "Як усе відбувається", "Step by step", True) + f'<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">{st}</div>')
    req = [("свіжа, зібрана не раніше ніж за 12 годин до здачі;", "fresh, picked no more than 12 hours before delivery;"), ("стигла, без гнилі, плісняви та пошкоджень шкідниками;", "ripe, free of rot, mould and pest damage;"),
           ("без листя, плодоніжок і сторонніх домішок;", "free of leaves, stems and foreign matter;"), ("не мита;", "unwashed;"), ("у чистій тарі, шаром не більше 10 см.", "in clean crates, no more than 10 cm deep.")]
    rl = "".join(f'<li class="flex gap-3"><span class="dot bg-berry mt-2" aria-hidden="true"></span>{E("span", f"i.req{i}", u, e)}</li>' for i, (u, e) in enumerate(req))
    b += split("malyna", "i.req", ("Заморожена малина в ящиках", "Frozen raspberries in crates"), ("Вимоги", "Requirements"), ("Яку ягоду ми приймаємо", "What berries we accept"),
               [("Наша ягода їде до Швеції, Німеччини, Франції, Канади та США — якість кожного кілограма впливає на репутацію й ціну для всіх учасників.",
                 "Our berries go to Sweden, Germany, France, Canada and the USA — the quality of every kilogram affects the reputation and price for all members.")],
               "bg-peach", extra=f'<ul class="grid gap-2 text-lg text-body">{rl}</ul>')
    b += section(head("i.pts", "Пункти приймання", "Collection points", "Де нас знайти", "Where to find us")
                 + f'<div class="grid gap-8 lg:grid-cols-[1.25fr_1fr] items-start"><div><div class="overflow-x-auto rounded-md border border-line"><table class="table-fp min-w-[520px]">{E("caption", "i.pts.cap", "Пункти приймання: адреса, години роботи в сезон (червень–жовтень), телефон", "Collection points: address, season opening hours (June–October), phone", "sr-only")}<thead><tr>{E("th", "i.pts.c1", "Пункт", "Point", "", ' scope="col"')}{E("th", "i.pts.c2", "Адреса", "Address", "", ' scope="col"')}{E("th", "i.pts.c3", "Години", "Hours", "", ' scope="col"')}{E("th", "i.pts.c4", "Телефон", "Phone", "", ' scope="col"')}</tr></thead>'
                 + f'<tbody id="pointsBody"><tr><td colspan="4" class="text-muted" data-i18n="i.prices.loading">{esc("Завантажуємо ціни…")}</td></tr></tbody></table></div><div class="mt-5 flex flex-wrap items-center justify-between gap-4"><button type="button" id="pointsMore" class="btn-out hidden" aria-expanded="false" aria-controls="pointsBody" data-i18n="i.pts.more">Показати всі пункти</button>{E("p", "i.pts.demo", "Адреси й телефони пунктів у демо-версії вигадані.", "Point addresses and phones in this demo are fictional.", "text-sm text-muted")}</div></div><div>{map_svg("map.i")}</div></div>', sid="points")
    b += split("sila-kooperatyviv", "i.mem", ("Учасники кооперативного форуму", "Participants of a cooperative forum"), ("Членство", "Membership"), ("Станьте частиною «Файної поляни»", "Become part of Faina Polyana"),
               [("Члени кооперативу — співвласники спільної справи. Крім премії 50% за оплату в кінці сезону, вони отримують безкоштовні агрономічні консультації, допомогу із саджанцями та пріоритетне приймання в пік сезону.",
                 "Members are co-owners of a shared business. Besides the 50% end-of-season premium, they get free agronomic advice, help with seedlings and priority intake at peak season."),
                ("Що потрібно: вирощувати ягоди на власній або орендованій ділянці, подати заяву, сплатити вступний пайовий внесок і дотримуватися стандартів якості.",
                 "What you need: grow berries on your own or rented land, apply, pay the entry share contribution and follow the quality standards.")],
               "bg-mint", True, extra=btn("contacts.html", "i.mem.btn", "Дізнатися про вступ", "Ask about membership", "btn-green self-start"), sid="member")
    faq = [("Яку довідку про дохід потрібно мати?", "Which income certificate do I need?", "Довідку, що підтверджує дохід від вирощування ягід (наприклад, як власника особистого селянського господарства). Деталі — на пункті приймання.", "A certificate confirming income from growing berries (for example, as a private household farm owner). Details at the collection point."),
           ("Коли триває сезон приймання?", "When is the intake season?", "Зазвичай з початку червня (полуниця) до кінця жовтня (ремонтантна малина, обліпиха, калина).", "Usually from early June (strawberries) to late October (remontant raspberries, sea buckthorn, viburnum)."),
           ("Чи можна здати невелику кількість?", "Can I deliver a small amount?", "Так, приймаємо від 1 кг.", "Yes, we accept from 1 kg."),
           ("Як і коли я отримаю оплату?", "How and when will I be paid?", "На картку протягом трьох робочих днів або в кінці сезону з премією 50% для членів кооперативу.", "To your card within three business days, or at season end with a 50% premium for members."),
           ("Чи приймаєте ягоди з городу?", "Do you accept berries from home gardens?", "Так — більшість наших учасників вирощують ягоди на присадибних ділянках.", "Yes — most of our members grow berries in their home gardens.")]
    fq = "".join(f'<details class="card group p-5"><summary class="cursor-pointer list-none flex justify-between gap-4 font-slab font-bold text-lg"><span data-i18n="i.faq{i}.q">{esc(qu)}</span><span class="text-leafdk transition-transform group-open:rotate-45" aria-hidden="true">+</span></summary>{E("p", f"i.faq{i}.a", au, ae, "mt-3 text-body leading-relaxed")}</details>' for i, (qu, qe, au, ae) in enumerate(faq))
    for i, (qu, qe, au, ae) in enumerate(faq):
        EN[f"i.faq{i}.q"] = qe
    b += section(head("i.faq", "FAQ", "FAQ", "Часті запитання", "Frequently asked questions", True) + f'<div class="mx-auto max-w-3xl grid gap-3">{fq}</div>', "bg-cloud")
    return (page_head("intake.html", "meta.intake", "Приймання ягід — Файна поляна", "Berry intake — Faina Polyana",
                      "Приймання малини та інших ягід на Тернопільщині: актуальні ціни сезону 2026, калькулятор заробітку, пункти приймання, умови членства в кооперативі.",
                      "Raspberry and berry intake in the Ternopil region: 2026 prices, an earnings calculator, collection points and membership terms.", ("calculator.js",))
            + header("intake.html") + b + footer())


# ================================================================ CONTACTS
def page_contacts():
    b = hero("c.hero", ("Співпраця", "Cooperation"), ("Почнімо розмову", "Let's start a conversation"),
             ("Купуєте заморожену ягоду чи шукаєте надійний об'єкт для інвестицій, гранту або тендеру — ми відповідаємо на кожен запит протягом одного робочого дня.",
              "Whether you buy frozen berries or are looking for a reliable partner for an investment, grant or tender, we answer every inquiry within one business day."),
             btn("?type=buyer#form", "c.hero.b1", "Я покупець", "I am a buyer") + btn("?type=investor#form", "c.hero.b2", "Я інвестор", "I am an investor", "btn-green"))
    steps = [("Запит", "Inquiry", "Форма або email: асортимент, обсяги, вимоги, терміни.", "Form or email: range, volumes, requirements, timing."),
             ("Пропозиція", "Offer", "Специфікації, сертифікати та комерційна пропозиція за 1 робочий день.", "Specifications, certificates and a commercial offer within 1 business day."),
             ("Зразки", "Samples", "1–2 кг кожної позиції безкоштовно; доставку оплачує покупець.", "1–2 kg of each item free of charge; the buyer pays for delivery."),
             ("Візит або аудит", "Visit or audit", "Огляд хабу й пунктів приймання — особисто чи онлайн.", "A tour of the hub and collection points — in person or online."),
             ("Контракт", "Contract", "Обсяги, графік, пакування, оплата; FCA Городище, DAP або CPT.", "Volumes, schedule, packing, payment; FCA Horodyshche, DAP or CPT."),
             ("Поставка", "Delivery", "Повний пакет документів і супровід до прибуття вантажу.", "Full document set and support until the cargo arrives.")]
    rc = ["bg-berry ring-blush", "bg-orangetx ring-peach", "bg-leafdk ring-mint", "bg-rose ring-blush", "bg-leafdk ring-mint", "bg-stone ring-cloud"]
    s = "".join(f'<div class="flex gap-5"><span class="num-circle {rc[i]}" aria-hidden="true">{i + 1:02d}</span><div>{E("h3", f"c.st{i}.t", tu, te, "font-slab font-bold text-lg mb-1")}{E("p", f"c.st{i}.d", du, de, "text-body")}</div></div>' for i, (tu, te, du, de) in enumerate(steps))
    b += section(head("c.st", "Як розпочати співпрацю", "How to start", "Від першого листа до першої поставки", "From the first email to the first delivery", True) + f'<div class="grid gap-10 md:grid-cols-2 lg:grid-cols-3">{s}</div>', "bg-cloud")
    formats = [("Разовий контракт", "Spot contract", "Партія за погодженою специфікацією, від ≈20 т.", "A lot to an agreed specification, from ≈20 t."),
               ("Сезонний контракт", "Season contract", "Фіксовані обсяги й графік на весь сезон.", "Fixed volumes and a schedule for the whole season."),
               ("Довгострокове партнерство", "Long-term partnership", "Планування обсягів і пріоритетний доступ до продукції.", "Volume planning and priority access to product."),
               ("Private label", "Private label", "Фасування під вашою маркою — від 300 г до 10 кг.", "Packing under your brand — from 300 g to 10 kg."),
               ("Інвестиційний проєкт", "Investment project", "Співфінансування «Городище 2028», кредити й лізинг обладнання.", "Co-financing “Horodyshche 2028”, loans and equipment leasing."),
               ("Гранти й тендери", "Grants and tenders", "Програми технічної допомоги, донорські проєкти, міжнародні тендери.", "Technical assistance, donor projects and international tenders.")]
    tops = ["border-berry", "border-orange", "border-leaf", "border-stone", "border-leafdk", "border-rose"]
    fm = "".join(f'<div class="tile border-t-[3px] {tops[i]} pt-3">{E("h3", f"c.fm{i}.t", tu, te, "font-slab font-bold text-lg")}{E("p", f"c.fm{i}.d", du, de, "mt-1 text-body")}</div>' for i, (tu, te, du, de) in enumerate(formats))
    b += section(head("c.fm", "Формати", "Formats", "Як ми можемо працювати разом", "How we can work together") + f'<div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">{fm}</div>')

    def field(fid, key, uk, en, inp, hint=None, req=True):
        # Зірочка обов'язкового поля — через CSS (.req::after), щоб її не стирав перемикач мови
        if req:
            inp = inp.replace(' class="field"', ' aria-required="true" class="field"', 1)
        h = E("p", f"{key}.hint", hint[0], hint[1], "mt-1 text-sm text-muted", f' id="{fid}Hint"') if hint else ""
        return f'<div>{E("label", key, uk, en, "field-label req" if req else "field-label", f' for="{fid}"')}{inp}{h}<p id="{fid}Err" class="field-error" aria-live="polite"></p></div>'
    desc = lambda fid, hint=False: f'aria-describedby="{fid}Hint {fid}Err"' if hint else f'aria-describedby="{fid}Err"'
    countries = [("", "Оберіть країну", "Choose a country"), ("UA", "Україна", "Ukraine"), ("SE", "Швеція", "Sweden"), ("DE", "Німеччина", "Germany"), ("FR", "Франція", "France"),
                 ("PL", "Польща", "Poland"), ("NL", "Нідерланди", "Netherlands"), ("GB", "Велика Британія", "United Kingdom"), ("CA", "Канада", "Canada"), ("US", "США", "USA"), ("OTHER", "Інша країна", "Other country")]
    copts = "".join(f'<option value="{v}" data-i18n="c.cn.{v or "none"}">{esc(u)}</option>' for v, u, e in countries)
    for v, u, e in countries:
        EN[f"c.cn.{v or 'none'}"] = e
    types = [("", "Оберіть тип", "Choose a type"), ("food", "Виробник харчової продукції", "Food manufacturer"), ("dist", "Дистриб'ютор / імпортер", "Distributor / importer"),
             ("retail", "Роздрібна мережа", "Retail chain"), ("proc", "Переробне підприємство", "Processor"), ("other", "Інше", "Other")]
    topts = "".join(f'<option value="{v}" data-i18n="c.ty.{v or "none"}">{esc(u)}</option>' for v, u, e in types)
    for v, u, e in types:
        EN[f"c.ty.{v or 'none'}"] = e
    prods = [("raspberry", "Малина", "Raspberry"), ("blueberry", "Лохина", "Blueberry"), ("blackberry", "Ожина", "Blackberry"), ("strawberry", "Полуниця", "Strawberry"), ("currant", "Смородина", "Currant"), ("mix", "Інші / суміші", "Other / mixes")]
    pch = "".join(f'<label class="chip cursor-pointer font-medium"><input type="checkbox" name="products" value="{v}" class="h-4 w-4 accent-leafdk">{E("span", f"c.pr.{v}", u, e)}</label>' for v, u, e in prods)
    orgs = [("", "Оберіть тип", "Choose a type"), ("fund", "Інвестиційний фонд", "Investment fund"), ("dfi", "Банк або фінансова установа розвитку", "Bank or development finance institution"),
            ("donor", "Донорська або грантова програма", "Donor or grant programme"), ("tender", "Тендерна / закупівельна організація", "Tender / procurement organisation"),
            ("private", "Приватний інвестор", "Private investor"), ("other", "Інше", "Other")]
    oopts = "".join(f'<option value="{v}" data-i18n="c.org.{v or "none"}">{esc(u)}</option>' for v, u, e in orgs)
    for v, u, e in orgs:
        EN[f"c.org.{v or 'none'}"] = e
    projects = [("", "Ще не визначено", "Not decided yet"), ("iqf", "«Городище 2028»: тунель IQF і оптичне сортування", "“Horodyshche 2028”: IQF tunnel and optical sorting"),
                ("logistics", "Логістичний центр і цех фасування", "Logistics centre and packing workshop"), ("storage", "Розширення складу до 1000 т", "Cold storage expansion to 1,000 t"),
                ("solar", "Сонячна станція 300 кВт", "300 kW solar plant"), ("growers", "Розвиток виробників-учасників", "Development of member growers")]
    popts = "".join(f'<option value="{v}" data-i18n="c.prj.{v or "none"}">{esc(u)}</option>' for v, u, e in projects)
    for v, u, e in projects:
        EN[f"c.prj.{v or 'none'}"] = e
    budgets = [("", "Оберіть діапазон", "Choose a range"), ("s", "до €100 тис.", "up to €100k"), ("m", "€100–500 тис.", "€100–500k"), ("l", "€0,5–2 млн", "€0.5–2M"), ("xl", "понад €2 млн", "over €2M"), ("tbd", "Обговоримо", "To be discussed")]
    bopts = "".join(f'<option value="{v}" data-i18n="c.bud.{v or "none"}">{esc(u)}</option>' for v, u, e in budgets)
    for v, u, e in budgets:
        EN[f"c.bud.{v or 'none'}"] = e
    ints = [("invest", "Інвестиції в потужності", "Capacity investment"), ("loan", "Кредит / лізинг обладнання", "Loan / equipment leasing"), ("grant", "Грант / технічна допомога", "Grant / technical assistance"), ("tender", "Тендер / закупівля", "Tender / procurement")]
    ich = "".join(f'<label class="chip cursor-pointer font-medium"><input type="checkbox" name="interest" value="{v}" class="h-4 w-4 accent-leafdk">{E("span", f"c.int.{v}", u, e)}</label>' for v, u, e in ints)
    mode = lambda v, key, uk, en, sub_uk, sub_en, checked: (
        f'<label class="mode-card"><input type="radio" name="ptype" value="{v}" class="sr-only peer"{" checked" if checked else ""}>'
        f'<span class="block rounded-md border-2 border-line bg-white p-4 transition-colors peer-checked:border-leafdk peer-checked:bg-mint peer-focus-visible:ring-2 peer-focus-visible:ring-leafdk">'
        + E("span", key, uk, en, "block font-slab font-bold text-lg") + E("span", key + ".s", sub_uk, sub_en, "block text-sm text-muted") + "</span></label>")
    form = f"""<form id="partnerForm" class="card-flat p-6 md:p-8 grid gap-5" novalidate>
  <fieldset>{E("legend", "c.f.mode", "Я звертаюсь як", "I am contacting you as", "field-label")}
    <div class="grid gap-3 sm:grid-cols-2">{mode("buyer", "c.f.buyer", "Покупець продукції", "Product buyer", "закупівля замороженої ягоди", "buying frozen berries", True)}{mode("investor", "c.f.investor", "Інвестор, фонд або донор", "Investor, fund or donor", "інвестиції, кредити, гранти, тендери", "investment, loans, grants, tenders", False)}</div>
  </fieldset>
  {E("p", "c.form.req", "Поля з * обов'язкові.", "Fields marked * are required.", "text-sm text-muted")}
  <div class="hidden" aria-hidden="true"><label for="website">Website</label><input id="website" name="website" type="text" tabindex="-1" autocomplete="off"></div>
  <div class="grid gap-5 md:grid-cols-2">
    {field("company", "c.f.company", "Назва компанії або організації", "Company or organisation", f'<input id="company" name="company" type="text" autocomplete="organization" maxlength="80" class="field" {desc("company")}>')}
    {field("person", "c.f.person", "Контактна особа", "Contact person", f'<input id="person" name="person" type="text" autocomplete="name" maxlength="60" class="field" {desc("person")}>')}
    {field("position", "c.f.position", "Посада", "Position", f'<input id="position" name="position" type="text" autocomplete="organization-title" maxlength="60" class="field" {desc("position")}>', req=False)}
    {field("country", "c.f.country", "Країна", "Country", f'<select id="country" name="country" autocomplete="country" class="field" {desc("country")}>{copts}</select>')}
    {field("email", "c.f.email", "Email", "Email", f'<input id="email" name="email" type="email" autocomplete="email" maxlength="100" class="field" placeholder="name@company.com" {desc("email")}>')}
    {field("phone", "c.f.phone", "Телефон", "Phone", f'<input id="phone" name="phone" type="tel" autocomplete="tel" maxlength="20" class="field" placeholder="+46 70 123 45 67" {desc("phone", True)}>', ("У міжнародному форматі: + код країни і номер", "International format: + country code and number"))}
  </div>
  <fieldset id="buyerFields" class="grid gap-5">{E("legend", "c.f.buyerLeg", "Дані покупця", "Buyer details", "sr-only")}
    <div class="grid gap-5 md:grid-cols-2">
      {field("ctype", "c.f.type", "Тип компанії", "Company type", f'<select id="ctype" name="ctype" class="field" {desc("ctype")}>{topts}</select>', req=False)}
      {field("volume", "c.f.volume", "Орієнтовний обсяг, т/рік", "Estimated volume, t/year", f'<input id="volume" name="volume" type="text" inputmode="numeric" maxlength="6" class="field" placeholder="100" {desc("volume")}>', req=False)}
    </div>
    <fieldset>{E("legend", "c.f.products", "Цікавить продукція", "Products of interest", "field-label")}<div class="flex flex-wrap gap-2.5">{pch}</div></fieldset>
  </fieldset>
  <fieldset id="investorFields" class="grid gap-5" hidden disabled>{E("legend", "c.f.invLeg", "Дані інвестора", "Investor details", "sr-only")}
    <div class="grid gap-5 md:grid-cols-2">
      {field("orgType", "c.f.org", "Тип організації", "Organisation type", f'<select id="orgType" name="orgType" class="field" {desc("orgType")}>{oopts}</select>')}
      {field("budget", "c.f.budget", "Орієнтовний обсяг фінансування", "Indicative financing amount", f'<select id="budget" name="budget" class="field" {desc("budget")}>{bopts}</select>', req=False)}
    </div>
    {field("project", "c.f.project", "Проєкт, що цікавить", "Project of interest", f'<select id="project" name="project" class="field" {desc("project")}>{popts}</select>', req=False)}
    <fieldset>{E("legend", "c.f.interest", "Формат співпраці", "Type of cooperation", "field-label")}<div class="flex flex-wrap gap-2.5">{ich}</div></fieldset>
  </fieldset>
  {field("message", "c.f.message", "Повідомлення", "Message", f'<textarea id="message" name="message" rows="5" maxlength="1000" class="field" {desc("message", True)}></textarea>', ("До 1000 символів", "Up to 1,000 characters"), req=False)}
  <div><label class="flex items-start gap-3 cursor-pointer"><input id="consent" name="consent" type="checkbox" class="mt-1 h-5 w-5 accent-leafdk" aria-describedby="consentErr">{E("span", "c.f.consent", "Я погоджуюсь на обробку персональних даних для відповіді на мій запит *", "I agree to the processing of my personal data to answer my inquiry *")}</label><p id="consentErr" class="field-error" aria-live="polite"></p></div>
  {E("button", "c.f.submit", "Надіслати запит", "Send inquiry", "btn-red w-full md:w-auto md:justify-self-start", ' type="submit" id="formSubmit"')}
  {E("p", "c.f.demo", "Демо-версія: форма перевіряє дані, але нікуди їх не надсилає й ніде не зберігає.", "Demo version: the form validates your data but does not send or store it anywhere.", "text-sm text-muted")}
</form>"""
    contacts = f"""<div class="grid gap-5">
  <div class="card p-6">{E("h3", "c.k.sales", "Відділ продажів і експорту", "Sales and export", "font-slab font-bold text-lg mb-2")}<p>{E("span", "c.k.sales.n", "Олена Коваль, комерційний директор", "Olena Koval, Commercial Director")}<br>sales@fainapolyana.com.ua<br>+380&nbsp;67&nbsp;000&nbsp;00&nbsp;00 (WhatsApp, Viber)</p>{E("p", "c.k.lang", "Мови: українська, англійська, польська", "Languages: Ukrainian, English, Polish", "mt-2 text-sm text-muted")}</div>
  <div class="card p-6">{E("h3", "c.k.inv", "Інвестиції, гранти й тендери", "Investment, grants and tenders", "font-slab font-bold text-lg mb-2")}<p>{E("span", "c.k.inv.n", "Тарас Андрійчук, голова правління", "Taras Andriichuk, Chairman of the Board")}<br>invest@fainapolyana.com.ua</p></div>
  <div class="card p-6">{E("h3", "c.k.intake", "Приймання ягід", "Berry intake", "font-slab font-bold text-lg mb-2")}<p>+380&nbsp;67&nbsp;000&nbsp;00&nbsp;06<br>berries@fainapolyana.com.ua</p></div>
  <div class="card p-6">{E("h3", "c.k.office", "Офіс і адреса", "Office and address", "font-slab font-bold text-lg mb-2")}{E("p", "c.k.addr", "вул. Тернопільська, 2д, с. Городище, Козівська громада, Тернопільська обл., 47633", "2d Ternopilska St, Horodyshche, Kozova community, Ternopil Oblast, 47633, Ukraine")}<p class="mt-2">info@fainapolyana.com.ua</p>{E("p", "c.k.hours", "Пн–Пт, 9:00–18:00 (за київським часом)", "Mon–Fri, 9:00–18:00 (Kyiv time, UTC+2)", "mt-2 text-sm text-muted")}</div>
  {E("p", "c.k.demo", "Контакти в демо-версії вигадані.", "Contact details in this demo are fictional.", "text-sm text-muted")}
</div>"""
    b += f'<section id="form" class="bg-mint"><div class="wrap py-20 grid gap-10 lg:grid-cols-[1.5fr_1fr]" data-aos="fade-up"><div>{head("c.form", "Форма заявки", "Inquiry form", "Надіслати запит", "Send an inquiry")}{form}</div><div>{head("c.k", "Контакти", "Contacts", "Наші контакти", "Get in touch")}{contacts}</div></div></section>\n'
    b += section(head("c.map", "Як доїхати", "Getting here", "Хаб у Городищі", "The Horodyshche hub", True)
                 + f'<div class="grid gap-8 lg:grid-cols-[1.3fr_1fr] items-center"><div>{map_svg("map.c")}</div><div>{E("p", "c.map.p1", "Хаб розташований у селі Городище, близько 35 км від Тернополя. Рухайтеся автошляхом у напрямку Козови — поворот на Городище позначений вказівником.", "The hub is in the village of Horodyshche, about 35 km from Ternopil. Take the road towards Kozova — the turn to Horodyshche is signposted.", "txt")}{E("p", "c.map.p2", "Найближчий міжнародний аеропорт — Львів (≈140 км).", "The nearest international airport is Lviv (≈140 km).", "txt")}</div></div>')
    b += """<dialog id="formDialog" class="rounded-md p-0 shadow-2xl backdrop:bg-graphite/50 max-w-md w-[calc(100%-2rem)]" aria-labelledby="dlgTitle">
  <div class="p-8 text-center"><span class="num-circle mx-auto mb-4 bg-leafdk ring-mint" aria-hidden="true">✓</span>""" + E("h2", "c.dlg.t", "Дякуємо! Запит отримано", "Thank you! Inquiry received", "font-slab font-bold text-2xl mb-2", ' id="dlgTitle"') + E("p", "c.dlg.p", "Ми зв'яжемося з вами протягом одного робочого дня. (Демо: дані нікуди не надіслано.)", "We will contact you within one business day. (Demo: no data was sent.)", "text-body mb-6") + """
  <form method="dialog">""" + E("button", "c.dlg.b", "Закрити", "Close", "btn-green", ' type="submit"') + """</form></div>
</dialog>
"""
    return (page_head("contacts.html", "meta.contacts", "Контакти та співпраця — Файна поляна", "Contacts and cooperation — Faina Polyana",
                      "Як почати співпрацю з СК «Файна поляна»: етапи, формати контрактів, форма заявки для партнерів, контакти відділу експорту та дорога до хабу в Городищі.",
                      "How to start working with Faina Polyana: steps, contract formats, partner inquiry form, export contacts and directions to the Horodyshche hub.", ("contact-form.js",))
            + header("contacts.html") + b + footer(cta=False))


# ================================================================ JS strings (переклади повідомлень скриптів)
JS_EN = {
    "js.menu.open": "Open menu", "js.menu.close": "Close menu",
    "js.calc.errBerry": "Choose a berry from the list.", "js.calc.errEmpty": "Enter the weight in kilograms.",
    "js.calc.errNaN": "Weight must be a number, e.g. 12.5", "js.calc.errMin": "Enter a weight of at least 1 kg.",
    "js.calc.errMax": "We accept up to 500 kg per delivery. For larger lots, please call us.",
    "js.calc.errLoad": "Could not load prices. Please refresh the page.", "js.calc.perKg": "UAH/kg", "js.calc.uah": "UAH",
    "js.prices.main": "Main crop", "js.prices.withCert": "With income certificate", "js.prices.calc": "Calculate",
    "js.prices.more": "Show the full range", "i.prices.more": "Show more", "js.prices.less": "Collapse the range",
    "js.points.more": "Show all points", "js.points.less": "Collapse the list", "i.pts.more": "Show all points",
    "js.form.required": "This field is required.", "js.form.company": "Use 2–80 characters: letters, digits, spaces and & . , ' \" ( ) -",
    "js.form.person": "At least 2 letters; apostrophes, hyphens and spaces allowed.", "js.form.email": "Check the format: name@company.com",
    "js.form.phone": "International format: + country code and 8–15 digits, e.g. +46701234567",
    "js.form.country": "Choose a country.", "js.form.volume": "Whole number from 1 to 100,000.", "js.form.message": "Please write at least 10 characters or leave the field empty.",
    "js.form.consent": "Please confirm your consent.", "js.form.fix": "Please correct the highlighted fields.", "js.form.sending": "Checking…",
    "js.form.phoneNote": "We removed spaces, brackets and dashes.", "js.form.org": "Choose an organisation type."
}


def main():
    pages = {"index.html": page_index, "partners.html": page_partners, "plans.html": page_plans, "intake.html": page_intake, "contacts.html": page_contacts}
    for name, fn in pages.items():
        (ROOT / name).write_text(fn(), encoding="utf-8")
    EN.update(JS_EN)
    (ROOT / "i18n").mkdir(exist_ok=True)
    (ROOT / "i18n" / "en.json").write_text(json.dumps(dict(sorted(EN.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {len(pages)} сторінок, {len(EN)} рядків перекладу → i18n/en.json")


if __name__ == "__main__":
    main()
