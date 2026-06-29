# MatchProp — QGIS 3 plugin

Copy **attributes + visual style** from one feature to one or more features
**within the same layer**, inspired by AutoCAD's `MATCHPROP` command.

![icon](matchprop/icon.png)

## What it does

1. Select **1 source feature** + **1 or more target features** in the same
   editable vector layer (use the native QGIS selection tool).
2. Click the **MatchProp** button on the toolbar (or *Plugins ▸ MatchProp*).
3. The plugin copies the source's attributes and visual style to the targets.

- **Source feature** = the selected feature with the **smallest `fid`**
  (the first one selected), as agreed.
- **Attributes**: copies every editable field, **skipping** primary-key /
  auto-increment columns (`fid`, `id`, …) and read-only fields.
- **Style**: behaviour depends on the layer renderer:
  - *Single Symbol* → nothing to do (the symbol is shared by the whole layer).
  - *Categorized / Graduated* → copies the classification attribute value, so
    the target inherits the source symbol.
  - *Rule-based / other* → copying attributes lets the rules re-evaluate.
- **Fault tolerant**: incompatible fields are skipped silently (reported as a
  warning), the rest keep copying.
- **Undo/Redo**: changes are wrapped in `beginEditCommand`/`endEditCommand`,
  so a single `Ctrl+Z` reverts the whole operation.
- Works with **point, line and polygon** layers.

## Validations & feedback (QGIS message bar)

| Situation | Message | Level |
|-----------|---------|-------|
| Success | `Properties copied to N feature(s)` | Success (green) |
| Layer not in edit mode | `Layer is not in edit mode…` | Warning (yellow) |
| Fewer than 2 features selected | `Select at least 2 features…` | Warning |
| Write error | `Error: …` | Critical (red) |

## Project layout

```
matchprop/
├── __init__.py            # classFactory entry point
├── matchprop.py           # plugin class: toolbar button, menu, validation
├── matchprop_core.py      # pure copy logic (attributes + style)
├── metadata.txt           # name, version 0.1.0, QGIS >= 3.22, Qt6 supported
├── icon.png               # toolbar icon (brush + layers + copy arrow)
└── resources.qrc          # icon resource (optional; icon also loaded by path)
```

## Installation

### From ZIP (recommended)
1. Build the zip (see below) or download `matchprop.zip`.
2. In QGIS: *Plugins ▸ Manage and Install Plugins… ▸ Install from ZIP*.
3. Select the zip and click **Install Plugin**.

### Manual
Copy the `matchprop/` folder into your QGIS plugins directory:
- Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
- Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
- macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

Then enable **MatchProp** in the Plugin Manager.

## Compatibility

- QGIS **3.22+** (tested target **3.34 LTR**), Qt5 **and** Qt6
  (`supportsQt6=True`). The code imports Qt through `qgis.PyQt`, so it works on
  both Qt bindings. The icon is loaded from disk (`icon.png`), so there is no
  `pyrcc` compilation step required.

## Development

```bash
# Optional packaging helper
pip install pb-tool

# Reload while developing: install the "Plugin Reloader" plugin in QGIS.
```

### Build the distributable ZIP
From the repository root:
```bash
zip -r matchprop.zip matchprop -x '*.pyc' -x '*__pycache__*'
```
or with pb_tool from inside `matchprop/` (after adding a `pb_tool.cfg`):
```bash
pb_tool zip
```

## Tests

The core logic is decoupled from QGIS and unit-tested with lightweight mocks
(`tests/mock_qgis.py`) — no QGIS install required:

```bash
python3 -m pytest tests/ -v
```

Covered: source selection (min `fid`), attribute copy, primary-key/read-only
skipping, silent skip of incompatible fields, Undo command bracketing, and
style copy for Single / Categorized / Graduated renderers.

## Roadmap

- Copy across different layers with field mapping
- Options dialog (attributes only / style only / both) + per-field checkboxes
- Configurable keyboard shortcut
- Translations (PT-BR, EN, ES)
- Submission to plugins.qgis.org
