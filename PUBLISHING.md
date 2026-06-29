# Publishing MatchProp to the QGIS community

## A. Requirements checklist (plugins.qgis.org)
- [x] Open-source license compatible with GPL (we ship **GPL v2+**, file `matchprop/LICENSE`).
- [x] Original code and original icon (no Autodesk assets).
- [x] `metadata.txt` complete: name, version, description, about, author, email,
      qgisMinimumVersion, tags, changelog, `experimental=False`.
- [ ] Choose a final, trademark-safe plugin **name** (avoid "MATCHPROP"/"AutoCAD").
- [ ] A public source repository URL (GitHub) in `repository=` and `tracker=`.
- [ ] A homepage URL (can be the GitHub repo).
- [ ] At least one screenshot / short GIF showing the 2-step workflow.

## B. Get a plugins.qgis.org account
1. Create an OSGeo userID at https://www.osgeo.org/community/getting-started-osgeo/
   (or sign in if you already have one).
2. Log in at https://plugins.qgis.org/ with that OSGeo account.

## C. Upload the plugin
1. Build the zip: from the repo root run
   `zip -r matchprop.zip matchprop -x '*.pyc' -x '*__pycache__*'`
   (or right-click the `matchprop` folder in Windows → "Compress to ZIP").
   The zip MUST contain the top-level `matchprop/` folder with `metadata.txt`.
2. On plugins.qgis.org click **"Upload a plugin"** and select `matchprop.zip`.
3. The site validates `metadata.txt`. Fix any reported field and re-upload.
4. After approval it appears in QGIS → *Plugins ▸ Manage and Install Plugins* for
   everyone (no "Install from ZIP" needed by users).

## D. Update the repository/tracker URLs before publishing
Edit `matchprop/metadata.txt`:
```
homepage=https://github.com/<your-user>/matchprop-qgis
repository=https://github.com/<your-user>/matchprop-qgis
tracker=https://github.com/<your-user>/matchprop-qgis/issues
```

## E. Alternative / faster sharing (no review needed)
- **GitHub Release:** tag the repo and attach `matchprop.zip` as a release asset.
  Users install via *Install from ZIP*.
- **QGIS community channels:** post on the QGIS users mailing list, r/QGIS,
  GIS StackExchange, LinkedIn/Twitter with a short demo GIF.

## F. Suggested announcement (PT) — draft
> 🧰 Novo plugin para QGIS: **<NOME>** — copia atributos e estilo de uma feição
> para outras na mesma camada, em 2 passos (à la MATCHPROP do AutoCAD).
> Ignora campos-chave automaticamente, respeita o Undo (Ctrl+Z) e funciona com
> pontos, linhas e polígonos. Ideia & design: Hugo P. Teixeira. Grátis e open
> source (GPL v2+). Feedback é bem-vindo! 🙏
