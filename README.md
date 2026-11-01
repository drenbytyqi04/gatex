# GATEX — gatex.info

Static copy of the Webflow site **Gatex Shpk** (gatex.info), exported from the published site.

- Every page lives in `<slug>/index.html` (home is `index.html`, 404 is `404.html`).
- All CSS, JS, images, videos and PDFs from the Webflow CDN are stored locally in `assets/`.

## Run locally

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Deploy

Any static host works (Netlify, Vercel, GitHub Pages, Cloudflare Pages) — publish the repository root, no build step.

## Re-sync from Webflow

```bash
python3 tools/mirror.py .
```

## Limitations outside Webflow

- Forms (contact, request email) post to Webflow's form backend and will not submit on another host; connect them to a form service (Netlify Forms, Formspree, etc.).
- Webflow Ecommerce (cart, checkout) and site search need Webflow hosting.
