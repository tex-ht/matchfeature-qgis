# Publishing MatchFeature to the QGIS community

## A. Requirements checklist (plugins.qgis.org)
- [x] Open-source license compatible with GPL (we ship **GPL v2+**, file `matchfeature/LICENSE`).
- [x] Original code and original icon (no Autodesk assets).
- [x] Trademark-safe name: **MatchFeature** (no "MATCHPROP"/"AutoCAD" in the name).
- [x] `metadata.txt` complete: name, version, description, about, author, email,
      qgisMinimumVersion, tags, changelog, `experimental=False`.
- [ ] Create the GitHub repo **matchfeature-qgis** and confirm the URLs in `metadata.txt`.
- [ ] At least one screenshot / short GIF showing the 2-step workflow.

## B. Get a plugins.qgis.org account
1. Create an OSGeo userID at https://www.osgeo.org/community/getting-started-osgeo/
   (or sign in if you already have one).
2. Log in at https://plugins.qgis.org/ with that OSGeo account.

## C. Upload the plugin
1. Build the zip: from the repo root run
   `zip -r matchfeature.zip matchfeature -x '*.pyc' -x '*__pycache__*'`
   (or right-click the `matchfeature` folder in Windows → "Compress to ZIP").
   The zip MUST contain the top-level `matchfeature/` folder with `metadata.txt`.
2. On plugins.qgis.org click **"Upload a plugin"** and select `matchfeature.zip`.
3. The site validates `metadata.txt`. Fix any reported field and re-upload.
4. After approval it appears in QGIS → *Plugins ▸ Manage and Install Plugins* for
   everyone (no "Install from ZIP" needed by users).

## D. Repository/tracker URLs (already set in metadata.txt)
```
homepage=https://github.com/tex-ht/matchfeature-qgis
repository=https://github.com/tex-ht/matchfeature-qgis
tracker=https://github.com/tex-ht/matchfeature-qgis/issues
```

## E. Alternative / faster sharing (no review needed)
- **GitHub Release:** tag the repo and attach `matchfeature.zip` as a release asset.
  Users install via *Install from ZIP*.
- **QGIS community channels:** QGIS users mailing list, r/QGIS, GIS StackExchange,
  LinkedIn/Twitter with a short demo GIF.

## F. Announcement draft (PT-PT)
> 🧰 Novo plugin para QGIS: **MatchFeature** — copia atributos e estilo de uma
> feição para outras na mesma camada, em 2 passos (inspirado no MATCHPROP do
> AutoCAD). Ignora campos identificadores automaticamente, respeita o Anular
> (Ctrl+Z) e funciona com pontos, linhas e polígonos. Ideia e conceção: Hugo P.
> Teixeira. Gratuito e de código aberto (GPL v2+). O vosso feedback é bem-vindo! 🙏
