# -*- coding: utf-8 -*-
"""Core MatchFeature logic: capture a source feature's properties and apply
them to target features (two-step "copy then paste" workflow).

This module is framework-light: it relies only on the public PyQGIS object
protocol (duck typing) so it can be unit tested with lightweight mocks.
"""

import re

# Field names that are always treated as auto-managed keys and never copied.
DEFAULT_SKIP_FIELDS = {"fid", "id", "ogc_fid", "objectid", "gid"}

# Identifier-like field names that should not be copied (id, id1, gid,
# objectid, uid, uuid, pk, anything ending in _id / _fid). Carefully crafted
# so legitimate words like "idade" or "identificacao" are NOT matched.
_KEY_NAME_RE = re.compile(
    r"^(?:f?id|gid|oid|objectid|uid|uuid|pk)\d*$|_f?id\d*$"
)


def is_key_field_name(name):
    """Return True if ``name`` looks like an auto-managed identifier field."""
    if not name:
        return False
    n = name.strip().lower()
    if n in DEFAULT_SKIP_FIELDS:
        return True
    return bool(_KEY_NAME_RE.search(n))


class MatchFeatureResult(object):
    """Outcome of an apply operation."""

    def __init__(self):
        self.success = False
        self.targets_updated = 0
        self.attributes_copied = 0
        self.fields_skipped = []
        self.warnings = []
        self.error = None

    def __repr__(self):  # pragma: no cover - debugging helper
        return (
            "MatchFeatureResult(success=%r, targets_updated=%r, "
            "attributes_copied=%r, fields_skipped=%r, error=%r)"
            % (
                self.success,
                self.targets_updated,
                self.attributes_copied,
                self.fields_skipped,
                self.error,
            )
        )


def editable_field_indexes(layer):
    """Return the list of field indexes that should be copied.

    Skips primary key / auto-increment columns, well known key field names
    (fid, id, ...) and read-only fields when that info is available.
    """
    fields = layer.fields()
    field_count = len(fields)

    try:
        pk_indexes = set(layer.primaryKeyAttributes() or [])
    except Exception:
        pk_indexes = set()

    indexes = []
    for idx in range(field_count):
        if idx in pk_indexes:
            continue
        try:
            field = fields.at(idx)
        except Exception:
            field = fields[idx]
        name = field.name()
        if is_key_field_name(name):
            continue
        try:
            if hasattr(layer, "fieldIsReadOnly") and layer.fieldIsReadOnly(idx):
                continue
        except Exception:
            pass
        indexes.append(idx)
    return indexes


def capture_source(layer, source_feature):
    """Snapshot the copyable attribute values of the source feature.

    :returns: dict {field_index: value}
    """
    snapshot = {}
    for idx in editable_field_indexes(layer):
        try:
            snapshot[idx] = source_feature.attribute(idx)
        except Exception:
            try:
                snapshot[idx] = source_feature[idx]
            except Exception:
                continue
    return snapshot


def apply_source(layer, snapshot, target_features, result=None):
    """Apply a captured snapshot to each target feature.

    Wrapped in ``beginEditCommand``/``endEditCommand`` so the whole operation
    is a single Undo step. Incompatible fields fail silently and are recorded
    as warnings instead of aborting. The layer is repainted at the end so any
    categorized / graduated style driven by a copied attribute updates too.

    :returns: MatchFeatureResult
    """
    if result is None:
        result = MatchFeatureResult()

    targets = list(target_features)
    fields = layer.fields()

    layer.beginEditCommand("MatchFeature: apply properties")
    copied = 0
    try:
        for target in targets:
            target_id = target.id()
            for idx, value in snapshot.items():
                ok = False
                try:
                    ok = layer.changeAttributeValue(target_id, idx, value)
                except Exception as exc:  # pragma: no cover - defensive
                    ok = False
                    result.warnings.append("idx %s: %s" % (idx, exc))
                if ok:
                    copied += 1
                else:
                    try:
                        name = fields.at(idx).name()
                    except Exception:
                        name = str(idx)
                    if name not in result.fields_skipped:
                        result.fields_skipped.append(name)
        layer.endEditCommand()
    except Exception as exc:
        try:
            layer.destroyEditCommand()
        except Exception:
            pass
        result.error = str(exc)
        result.success = False
        return result

    try:
        layer.triggerRepaint()
    except Exception:
        pass

    result.attributes_copied = copied
    result.targets_updated = len(targets)
    result.success = True
    return result
