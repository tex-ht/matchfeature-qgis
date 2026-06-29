# MatchProp — QGIS 3 Plugin (PRD)

## Problem statement
QGIS 3 desktop plugin that copies attributes + visual style from one source
feature to one or more target features within the SAME layer (AutoCAD MATCHPROP
style). Python + PyQGIS + Qt. Not a web/mobile app.

## User choices (confirmed)
- Style scope: BOTH attributes + renderer-aware style logic.
- Delivery: BOTH full plugin source + standalone mocked unit tests + .zip.
- Target: QGIS 3.34+, Qt6 compatible (also Qt5 via qgis.PyQt).
- Source feature rule: smallest fid (first selected).
- Icon: auto-generated (brush + layers + copy arrow).

## Architecture
```
matchprop/
├── __init__.py          # classFactory
├── matchprop.py         # plugin class: toolbar btn, Plugins menu, validation, msg bar
├── matchprop_core.py    # pure logic: select_source_and_targets, copy_attributes, copy_style, match_properties
├── metadata.txt         # v0.1.0, qgisMin 3.22, supportsQt6=True
├── icon.png             # 96x96 toolbar icon
└── resources.qrc        # icon resource (icon also loaded by file path)
tests/
├── mock_qgis.py             # PyQGIS mocks (layer/feature/renderers/edit commands)
└── test_matchprop_core.py   # 14 unit tests
matchprop.zip            # installable bundle
README.md                # install + usage + dev docs
```

## What's implemented (2026-06-29)
- Toolbar button + Plugins menu entry with tooltip; QgisInterface wiring.
- Validation: active vector layer, has geometry, edit mode on, >=2 selected.
- Source = min fid; remaining = targets.
- copy_attributes: skips PK (primaryKeyAttributes) + key names (fid/id/...) +
  read-only fields; wrapped in beginEditCommand/endEditCommand (Undo);
  incompatible writes skipped silently and reported as warnings.
- copy_style: Single=no-op, Categorized/Graduated=copy class attribute value,
  Rule-based/other=attribute copy; triggerRepaint.
- Message bar feedback: Success / Warning / Critical.
- 14/14 unit tests pass (python3 -m pytest tests/).

## Testing status
- Core logic fully unit-tested with mocks (no QGIS needed). PASSED.
- NOT tested inside a live QGIS install (no QGIS in this environment); the
  matchprop.py GUI layer relies on PyQGIS at runtime and was syntax-validated only.

## Backlog (future)
- P1: Cross-layer copy with field mapping.
- P1: Options dialog (attrs only / style only / both) + per-field checkboxes.
- P2: Configurable keyboard shortcut.
- P2: i18n (PT-BR, EN, ES).
- P2: Submit to plugins.qgis.org; add pb_tool.cfg for `pb_tool zip`.
