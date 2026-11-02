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
python3 tools/patch_forms.py .
python3 tools/seo.py .
```

## Forms

The Contact, CTA ("Let's Reinforce Your Next Project") and Request Email forms are sent by
`assets/js/gatex-forms.js` through [Web3Forms](https://web3forms.com) to **sales@gatex.info**,
and show Webflow's original "Thank you" / "Oops" messages. It works on any host.

The Web3Forms access key (`ACCESS_KEY` in that file) is public by design; it only
lets the site send mail to sales@gatex.info. Manage it, or change the recipient, at web3forms.com.

## SEO

`tools/seo.py` sets a unique title, meta description, Open Graph tags and an absolute
canonical URL on every page, marks utility pages (checkout, search, password, request-email)
as `noindex`, adds JSON-LD (Organization, WebSite, FAQPage, breadcrumbs), and writes
`sitemap.xml` and `robots.txt`. Edit the `PAGES` table in that script to change the text for a page.
`vercel.json` serves URLs without a trailing slash and caches static assets.

## Limitations outside Webflow

- Webflow Ecommerce (cart, checkout) and site search need Webflow hosting.
