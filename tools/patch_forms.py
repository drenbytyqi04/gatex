"""Wire the Webflow forms to assets/js/gatex-forms.js. Safe to re-run.

Usage: python3 tools/patch_forms.py <site_dir>   (run after tools/mirror.py)
"""
import glob, os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
TAG = '<script src="/assets/js/gatex-forms.js" type="text/javascript"></script>'
form_re = re.compile(r'<form id="email-form"([^>]*?) data-turnstile-sitekey="[^"]*"([^>]*)>')
changed = 0
for path in glob.glob(os.path.join(root, "**", "*.html"), recursive=True):
    html = open(path, encoding="utf-8").read()
    new = form_re.sub(r'<form id="email-form" data-gatex-form=""\1\2>', html)
    if "data-gatex-form" in new and TAG not in new:
        new = new.replace("</body>", TAG + "</body>", 1)
    if new != html:
        open(path, "w", encoding="utf-8").write(new)
        changed += 1
print("patched", changed, "pages")
