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
```

## Limitations outside Webflow

## Forms

The Contact, CTA ("Let's Reinforce Your Next Project") and Request Email forms are sent by
`assets/js/gatex-forms.js` through [FormSubmit](https://formsubmit.co) to **sales@gatex.info**,
and show Webflow's original "Thank you" / "Oops" messages. It works on any host.

**One-time activation:** the first submission sends an email from FormSubmit to
sales@gatex.info — click **Activate Form** in it. After that, every submission arrives in
that inbox (reply goes straight to the sender). To change the address, edit
`FORM_ENDPOINT` at the top of `assets/js/gatex-forms.js`.

- Webflow Ecommerce (cart, checkout) and site search need Webflow hosting.
