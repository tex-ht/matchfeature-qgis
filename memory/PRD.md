# MatchFeature — QGIS 3 Plugin (PRD)

## Problem statement
QGIS 3 desktop plugin that copies attributes + visual style from one source
feature to one or more target features within the SAME layer (AutoCAD MATCHPROP
idea). Python + PyQGIS + Qt. Not a web/mobile app.

## Final decisions (confirmed with user Hugo P. Teixeira)
- Plugin name: **MatchFeature** (trademark-safe; avoid "MATCHPROP"/"AutoCAD" in name).
- Package/folder: `matchfeature/`. Class `MatchFeature`, `MatchFeatureResult`.
- Workflow: TWO-STEP (copy then apply) — source is NOT inferred from fid.
  Step 1: select 1 source, click -> capture. Step 2: select targets, click -> apply.
- Skips identifier fields: fid, id, id1, gid, objectid, oid, uid, uuid, pk, *_id
  (regex), plus provider primary keys and read-only fields. Keeps e.g. "idade".
- Style: Categorized/Graduated -> copies classification attribute so symbol is
  inherited; Single symbol = layer-level no-op.
- Undo: single beginEditCommand/endEditCommand ("MatchFeature: apply properties").
- i18n: European Portuguese (PT-PT) UI when QGIS locale starts with "pt", else EN.
  ALL Portuguese text must be PT-PT (European), never PT-BR.
- Icon: original (brush + layers + copy arrow), trimmed to fill toolbar button.
- License: GPL v2 (file matchfeature/LICENSE). Author = "Hugo P. Teixeira & Emergent",
  email texfap@gmail.com.
- GitHub repo (public): https://github.com/tex-ht/matchfeature-qgis

## Architecture
```
matchfeature/
├── __init__.py            # classFactory -> MatchFeature
├── matchfeature.py        # toolbar btn, Plugins menu, validation, msg bar, PT-PT tr()
├── matchfeature_core.py   # editable_field_indexes, is_key_field_name, capture_source, apply_source
├── metadata.txt           # name MatchFeature, v0.4.0, qgisMin 3.22, supportsQt6=True, GPL v2+
├── icon.png               # 256x256, content fills canvas
├── resources.qrc          # prefix /plugins/matchfeature
└── LICENSE                # GPL v2
tests/
├── mock_qgis.py               # PyQGIS mocks
└── test_matchfeature_core.py  # 9 unit tests (all pass)
assets/
├── matchfeature_demo.gif      # 2-step animated demo (PT-PT labels)
├── matchfeature_banner.png
├── matchfeature_steps.png
└── announcement_linkedin.md   # PT-PT LinkedIn post (placeholder <LINK_PLUGINS_QGIS>)
scripts/make_demo_gif.py        # regenerates the demo GIF
matchfeature.zip                # installable bundle (~104 KB, <20MB)
README.md, PUBLISHING.md
```

## Status (2026-06-30)
- Plugin complete; installed & validated by user in real QGIS. Works great.
- 9/9 unit tests pass (python3 -m pytest tests/). GUI layer syntax-validated only
  (no QGIS in this environment).
- Repo public on GitHub. LinkedIn announcement + demo GIF ready.

## Publishing to plugins.qgis.org — IN PROGRESS
- 2026 process requires an OSGeo "mantra" (verification code) requested by email
  to mantra-request@osgeo.org. User SENT the request; WAITING for the mantra.
- Validator checks: homepage/repository/tracker must be live public URLs (not zip)
  -> all point to github.com/tex-ht/matchfeature-qgis (OK). Zip <20MB, no binaries,
  English code comments, GPLv2 -> all satisfied.

## NEXT STEPS (resume here when user has the mantra)
1. id.osgeo.org/ldap/create -> enter mantra -> set username/password/MFA.
2. Login at plugins.qgis.org -> "Share/Upload a plugin".
3. Fresh zip: GitHub Download ZIP -> compress the `matchfeature` folder (to include
   latest metadata.txt with license line). Upload matchfeature.zip. Submit.
4. After approval: give user the catalog URL to fill <LINK_PLUGINS_QGIS> and post
   the LinkedIn announcement with the GIF.

## Backlog (future)
- P1: Options dialog (attrs only / style only / both) + per-field checkboxes.
- P1: Cross-layer copy with field mapping.
- P2: Interactive map tool (click source then click each target on canvas).
- P2: Configurable keyboard shortcut. Translations PT-BR/ES. .ts/.qm via lrelease.
