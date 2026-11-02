"""Apply SEO metadata to the static site. Safe to re-run (idempotent).

Usage: python3 tools/seo.py <site_dir>   (run after tools/mirror.py and tools/patch_forms.py)

- unique <title>, meta description, Open Graph / Twitter tags, absolute canonical
- noindex on utility pages (checkout, search, password, ...)
- JSON-LD: Organization + WebSite (home), FAQPage (faq), BreadcrumbList (detail pages)
- alt text on product main images
- sitemap.xml and robots.txt
"""
import datetime
import glob
import html
import json
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://gatex.info"
BRAND = "GATEX"
START, END = "<!-- seo:start -->", "<!-- seo:end -->"

NOINDEX = {"/401", "/404", "/checkout", "/paypal-checkout", "/order-confirmation", "/search", "/request-email"}

PAGES = {
    "/": ("GATEX | Fiberglass Reinforcement Mesh Manufacturer for ETICS",
          "GATEX manufactures ETA-assessed, CE-marked fiberglass reinforcement mesh, corner profiles and ETICS accessories in Kosovo, supplying distributors in 21+ countries across Europe."),
    "/about-us": ("About GATEX | Fiberglass Mesh Manufacturer in Kosovo",
                  "GATEX is a fiberglass reinforcement mesh manufacturer from Kaçanik, Kosovo, with ETA-assessed and CE-marked products for ETICS, active in 21+ European countries."),
    "/our-products": ("Fiberglass Mesh, Corner Profiles & ETICS Products | GATEX",
                      "Explore GATEX alkali-resistant fiberglass mesh (75–160 g/m²), corner bead profiles and joint tape for ETICS, façade and wall reinforcement. Datasheets available."),
    "/our-history": ("Our History | GATEX Fiberglass Mesh Production since Kaçanik",
                     "How GATEX grew from its first coating line in Kaçanik, Kosovo into a full fiberglass mesh manufacturer with warping, weaving, coating and finishing in-house."),
    "/services": ("Services: Mesh Manufacturing, OEM & Logistics | GATEX",
                  "GATEX services: fiberglass mesh manufacturing, private label & OEM production, color-coded mesh, ETICS systems, technical documentation and consolidated delivery."),
    "/our-partners": ("Partners & Distributors Across Europe | GATEX",
                      "GATEX works with distributors, construction specialists and system manufacturers across Europe. See our partners and what clients say about our reinforcement mesh."),
    "/faq": ("FAQ: Fiberglass Mesh & ETICS Questions | GATEX",
             "Answers about GATEX fiberglass reinforcement mesh, ETICS applications, certifications (ETA, CE), ordering, private label and delivery."),
    "/contact-us": ("Contact GATEX | Fiberglass Mesh Supplier in Kaçanik, Kosovo",
                    "Contact GATEX for fiberglass mesh quotes, samples and technical support. Email sales@gatex.info, call +383 48 266 366, or visit us on National Road Kaçanik – Ferizaj km 14."),
    "/sustainability": ("Sustainability & Climate Responsibility | GATEX",
                        "How GATEX reduces resource use, improves energy efficiency and protects worker safety in fiberglass reinforcement mesh manufacturing."),
    "/catalogues-center": ("Product Catalogues | GATEX Fiberglass Mesh",
                           "Download GATEX product catalogues for fiberglass reinforcement mesh, corner profiles and ETICS accessories."),
    "/download-center-page": ("Download Center: Datasheets & Certificates | GATEX",
                              "Download GATEX technical datasheets, product catalogues, ISO certificates and CE / ETA documents for fiberglass reinforcement mesh."),
    "/imprint": ("Imprint / Legal Notice | GATEX SH.P.K.",
                 "Legal notice, company information and copyright for GATEX SH.P.K., fiberglass reinforcement mesh manufacturer in Kaçanik, Kosovo."),
    "/request-email": ("Request Documents | GATEX", "Request GATEX documents with your registered email address or client ID code."),
    "/category/fiberglass-products": ("Fiberglass Reinforcement Mesh for ETICS (75–160 g/m²) | GATEX",
                                      "GATEX alkali-resistant fiberglass reinforcement mesh from 75 to 160 g/m² for ETICS and façades: Standard, Classic and PRO grades, ETA-assessed and CE-marked."),
    "/category/corner-bead-products": ("Corner Beads, Window Profiles & Joint Tape for ETICS | GATEX",
                                       "PVC corner beads with integrated fiberglass mesh, drip-edge profiles, window connection profiles and fiberglass joint tape for ETICS façades by GATEX."),
    "/401": ("Protected Page | GATEX", "This page is password protected."),
    "/404": ("Page Not Found | GATEX", "The page you are looking for could not be found."),
    "/checkout": ("Checkout | GATEX", "Checkout."),
    "/paypal-checkout": ("Checkout (PayPal) | GATEX", "Checkout with PayPal."),
    "/order-confirmation": ("Order Confirmation | GATEX", "Order confirmation."),
    "/search": ("Search Results | GATEX", "Search results on gatex.info."),
}

# What each non-mesh product is, for its title.
PRODUCT_KIND = {
    "gatex-g-2010": "Window Connection Profile",
    "gatex-g-2020": "Window Connection Profile",
    "gatex-g-2030": "Window Connection Profile with Mesh",
    "gatex-g-2040": "PVC Corner Bead with Fiberglass Mesh",
    "gatex-g-2050": "PVC Corner Bead with Drip Edge",
    "gatex-g-5090": "Fiberglass Joint Tape",
}

ORG = {
    "@type": "Organization",
    "@id": SITE + "/#organization",
    "name": "GATEX SH.P.K.",
    "alternateName": "GATEX Fiberglass",
    "url": SITE + "/",
    "email": "sales@gatex.info",
    "telephone": "+38348266366",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "National Road Kaçanik – Ferizaj km 14",
        "addressLocality": "Kaçanik",
        "postalCode": "71000",
        "addressCountry": "XK",
    },
    "sameAs": [
        "https://www.facebook.com/gatexshpk",
        "https://www.linkedin.com/company/gatex-shpk/",
        "https://www.youtube.com/@GatexFiberglass",
    ],
}


def text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def clip(s, n=158):
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0].rstrip(",;:—–- ")
    return cut + "…"


def esc(s):
    return html.escape(s, quote=True)


def url_path(file):
    rel = os.path.relpath(file, ROOT).replace(os.sep, "/")
    if rel == "index.html":
        return "/"
    if rel == "404.html":
        return "/404"
    return "/" + rel[: -len("/index.html")]


def first_paragraph(body):
    """First substantial paragraph after the page's H1."""
    h1 = body.find("<h1")
    for p in re.findall(r"<p[^>]*>(.*?)</p>", body[max(h1, 0):], re.S):
        t = text(p)
        if len(t) > 80:
            # Product pages start with a bolded tagline; drop it if it runs into the text.
            t = re.sub(r"^ETA-Assessed and CE-Marked [^.]*?Applications\s+", "", t)
            return t
    return ""


def h1_text(body):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    return text(m.group(1)) if m else ""


def meta_for(path, body):
    if path in PAGES:
        return PAGES[path]
    name = h1_text(body)
    desc = first_paragraph(body)
    section = path.split("/")[1]
    if section == "product":
        kind = PRODUCT_KIND.get(path.split("/")[-1], "Fiberglass Mesh for ETICS")
        title = f"{name} {kind}"
        desc = f"{name}: {desc}" if desc else f"{name} {kind} by GATEX, ETA-assessed and CE-marked."
    elif section == "category":
        title = f"{name} for ETICS | {BRAND}"
    elif section == "services":
        title = f"{name} | {BRAND} Services"
    else:
        title = f"{name or 'Page'} | {BRAND}"
    return title, clip(desc)


def breadcrumbs(path, name):
    section = path.split("/")[1]
    parent = {"product": ("Our Products", "/our-products"),
              "category": ("Our Products", "/our-products"),
              "services": ("Services", "/services")}.get(section)
    if not parent or path.count("/") < 2:
        return None
    items = [("Home", "/"), parent, (name, path)]
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
            for i, (n, u) in enumerate(items)
        ],
    }


def faq_schema(body):
    qa = re.findall(r'class="accordion-title"[^>]*>(.*?)</h5>.*?class="accordion-list-content"[^>]*>(.*?)</p>', body, re.S)
    if not qa:
        return None
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": text(q),
             "acceptedAnswer": {"@type": "Answer", "text": text(a)}}
            for q, a in qa
        ],
    }


STRIP = [
    r"<title>.*?</title>",
    r'<meta content="[^"]*" name="description"/>',
    r'<meta content="[^"]*" property="og:(?:title|description|url)"/>',
    r'<meta content="[^"]*" name="twitter:(?:title|description)"/>',
    r'<meta property="og:url" content="[^"]*"/>',
    r'<link href="[^"]*" rel="canonical"/>',
    r'<meta name="robots" content="[^"]*"/>',
    re.escape(START) + r".*?" + re.escape(END),
]


def process(file):
    page = open(file, encoding="utf-8").read()
    path = url_path(file)
    head_end = page.find("</head>")
    head, rest = page[:head_end], page[head_end:]
    body = rest[rest.find("<body"):]
    title, desc = meta_for(path, body)
    url = SITE + ("/" if path == "/" else path)

    for pat in STRIP:
        head = re.sub(pat, "", head, flags=re.S)

    tags = [
        START,
        f"<title>{esc(title)}</title>",
        f'<meta content="{esc(desc)}" name="description"/>',
        f'<meta content="{esc(title)}" property="og:title"/>',
        f'<meta content="{esc(desc)}" property="og:description"/>',
        f'<meta content="{esc(url)}" property="og:url"/>',
        f'<meta content="{esc(title)}" name="twitter:title"/>',
        f'<meta content="{esc(desc)}" name="twitter:description"/>',
    ]
    if path in NOINDEX:
        tags.append('<meta name="robots" content="noindex, follow"/>')
    else:
        tags.append(f'<link href="{esc(url)}" rel="canonical"/>')

    graph = []
    if path == "/":
        logo = re.search(r'<img src="([^"]*GATEX_LOGO[^"]*)"', body)
        org = dict(ORG)
        if logo:
            org["logo"] = SITE + logo.group(1)
        graph += [org, {"@type": "WebSite", "@id": SITE + "/#website", "url": SITE + "/",
                        "name": "GATEX", "publisher": {"@id": SITE + "/#organization"}}]
    if path == "/faq":
        faq = faq_schema(body)
        if faq:
            graph.append(faq)
    crumbs = breadcrumbs(path, h1_text(body))
    if crumbs:
        graph.append(crumbs)
    if graph:
        data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
        data = data.replace("</", "<\\/")
        tags.append('<script type="application/ld+json">' + data + "</script>")
    tags.append(END)

    head = head.replace('<meta charset="utf-8"/>', '<meta charset="utf-8"/>' + "".join(tags), 1)

    # Product pages: give the main product image (same as og:image) a descriptive alt.
    if path.startswith("/product/"):
        og = re.search(r'<meta content="([^"]+)" property="og:image"/>', head)
        name = h1_text(body)
        if og and name:
            src = og.group(1).replace(SITE, "")
            rest = re.sub(r'(<img src="' + re.escape(src) + r'"[^>]*?)alt="[^"]*"',
                          lambda m: m.group(1) + f'alt="{esc(name)}"', rest)

    new = head + rest
    if new != page:
        open(file, "w", encoding="utf-8").write(new)
    return path


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "**", "index.html"), recursive=True))
    files.append(os.path.join(ROOT, "404.html"))
    paths = [process(f) for f in files if "/assets/" not in f and "/tools/" not in f]

    today = datetime.date.today().isoformat()
    def prio(p):
        if p == "/":
            return "1.0"
        if p in ("/our-products", "/about-us", "/contact-us", "/services") or p.startswith("/category/"):
            return "0.9"
        if p.startswith("/product/"):
            return "0.8"
        return "0.6"
    urls = [p for p in paths if p not in NOINDEX]
    urls.sort(key=lambda p: (-float(prio(p)), p))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in urls:
        loc = SITE + ("/" if p == "/" else p)
        lines.append(f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>{prio(p)}</priority></url>")
    lines.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(lines) + "\n")

    # Utility pages carry a noindex tag instead of a Disallow, so crawlers can see it.
    open(os.path.join(ROOT, "robots.txt"), "w").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"processed {len(paths)} pages, sitemap has {len(urls)} URLs")


if __name__ == "__main__":
    main()
