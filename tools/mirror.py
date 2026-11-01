import re, os, sys, urllib.request, urllib.parse, hashlib, html
OUT = sys.argv[1]
BASE = "https://gatex.info"
CDN_HOSTS = ("cdn.prod.website-files.com", "assets.website-files.com", "uploads-ssl.webflow.com", "d3e54v103j8qbb.cloudfront.net")
seeds = ["/", "/request-email","/catalogues-center","/download-center-page","/imprint","/sustainability",
         "/our-history","/our-products","/about-us","/services","/our-partners","/faq","/search","/contact-us","/404","/401",
         "/checkout","/paypal-checkout","/order-confirmation"]
UA = {"User-Agent": "Mozilla/5.0"}
def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()
assets = {}  # url -> local path (relative to OUT, starting with assets/)
def asset_local(url):
    u = html.unescape(url)
    if u in assets: return assets[u]
    p = urllib.parse.urlparse(u)
    name = urllib.parse.unquote(p.path.rsplit("/",1)[-1]) or "file"
    name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    sub = "assets/" + ("js" if name.endswith(".js") else "css" if name.endswith(".css") else "media")
    if p.query: name = hashlib.md5(p.query.encode()).hexdigest()[:8] + "_" + name
    local = f"{sub}/{name}"
    assets[u] = local
    return local
asset_re = re.compile(r'https?://(?:%s)/(?:[^\s"\'()<>,]|\(\d+\))+' % "|".join(re.escape(h) for h in CDN_HOSTS))
def localize(text, depth_prefix):
    def rep(m):
        url = m.group(0)
        suffix = ""
        if "&quot;" in url: url, suffix = url.split("&quot;", 1)[0], "&quot;"
        return "/" + asset_local(url) + suffix
    return asset_re.sub(rep, text)
pages = {}
queue = list(seeds); seen=set()
while queue:
    path = queue.pop(0)
    path = path.split("#")[0].split("?")[0].rstrip("/") or "/"
    if path in seen: continue
    seen.add(path)
    try:
        data = fetch(BASE + path).decode("utf-8")
    except Exception as e:
        print("FAIL", path, e); continue
    pages[path] = data
    for href in re.findall(r'href="([^"]+)"', data):
        h = html.unescape(href)
        if h.startswith("https://gatex.info") or h.startswith("https://www.gatex.info"):
            h = urllib.parse.urlparse(h).path
        if h.startswith("/") and not h.startswith("//"):
            if re.search(r'\.(pdf|jpg|png|svg|zip)$', h, re.I): continue
            queue.append(h)
print("pages:", len(pages))
for path, data in pages.items():
    data = re.sub(r'\s+integrity="[^"]*"', '', data)
    data = localize(data, "")
    data = data.replace('href="https://gatex.info/', 'href="/').replace('href="https://www.gatex.info/', 'href="/')
    dest = os.path.join(OUT, "index.html") if path == "/" else (os.path.join(OUT, "404.html") if path=="/404" else os.path.join(OUT, path.lstrip("/"), "index.html"))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w").write(data)
done=set()
while True:
    todo=[u for u in assets if u not in done]
    if not todo: break
    for u in todo:
        done.add(u); local=assets[u]; dest=os.path.join(OUT, local)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try: b = fetch(u.replace(" ", "%20"))
        except Exception as e: print("ASSET FAIL", u, e); continue
        if local.endswith(".css") or local.endswith(".js"):
            t = b.decode("utf-8", "replace")
            t = localize(t, "")
            b = t.encode()
        open(dest,"wb").write(b)
print("assets:", len(assets))
