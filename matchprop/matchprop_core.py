# -*- coding: utf-8 -*-
"""Core MATCHPROP logic: copy attributes and visual style between features.

This module is intentionally framework-light: it relies only on the public
PyQGIS object protocol (duck typing) so it can be unit tested with lightweight
mocks. The only hard QGIS imports are guarded so the module can be imported in
a plain Python environment for testing.
"""

# Field names that are always treated as auto-managed keys and never copied.
DEFAULT_SKIP_FIELDS = {"fid", "id", "ogc_fid", "objectid", "gid"}


class MatchPropResult(object):
    """Outcome of a MATCHPROP operation."""

    def __init__(self):
        self.success = False
        self.targets_updated = 0
        self.attributes_copied = 0
        self.fields_skipped = []
        self.style_action = "none"
        self.warnings = []
        self.error = None

    def __repr__(self):  # pragma: no cover - debugging helper
        return (
            "MatchPropResult(success=%r, targets_updated=%r, "
            "attributes_copied=%r, style_action=%r, warnings=%r, error=%r)"
            % (
                self.success,
                self.targets_updated,
                self.attributes_copied,
                self.style_action,
                self.warnings,
                self.error,
            )
        )


def select_source_and_targets(features):
    """Split selected features into (source, [targets]).

    The source is the feature with the smallest feature id (the "first"
    selected feature), per the agreed rule. The remaining features become
    targets.

    :param features: iterable of QgsFeature-like objects exposing ``id()``.
    :returns: tuple (source_feature, list_of_target_features).
    :raises ValueError: when fewer than 2 features are supplied.
    """
    feats = list(features)
    if len(feats) < 2:
        raise ValueError("Need at least 2 selected features (1 source + 1 target).")
    ordered = sorted(feats, key=lambda f: f.id())
    return ordered[0], ordered[1:]


def _editable_field_indexes(layer):
    """Return the list of field indexes that should be copied.

    Skips:
      * primary key / auto-increment columns reported by the provider
      * well known key field names (fid, id, ...)
      * fields the layer reports as non-editable, when that info exists
    """
    fields = layer.fields()
    field_count = len(fields)

    pk_indexes = set()
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
        if name is not None and name.lower() in DEFAULT_SKIP_FIELDS:
            continue
        # Respect provider-level editability when the API is available.
        try:
            if hasattr(layer, "isEditCommandActive"):
                pass
            if hasattr(layer, "fieldIsReadOnly") and layer.fieldIsReadOnly(idx):
                continue
        except Exception:
            pass
        indexes.append(idx)
    return indexes


def copy_attributes(layer, source_feature, target_features, result=None):
    """Copy editable attribute values from source to each target feature.

    Wrapped in ``beginEditCommand``/``endEditCommand`` so the whole operation
    is a single Undo step. Incompatible fields fail silently and are recorded
    as warnings instead of aborting the operation.

    :returns: MatchPropResult
    """
    if result is None:
        result = MatchPropResult()

    indexes = _editable_field_indexes(layer)
    fields = layer.fields()

    layer.beginEditCommand("MatchProp: copy attributes")
    copied = 0
    try:
        for target in target_features:
            target_id = target.id()
            for idx in indexes:
                try:
                    value = source_feature.attribute(idx)
                except Exception:
                    try:
                        value = source_feature[idx]
                    except Exception:
                        continue
                ok = False
                try:
                    ok = layer.changeAttributeValue(target_id, idx, value)
                except Exception as exc:  # pragma: no cover - defensive
                    ok = False
                    try:
                        name = fields.at(idx).name()
                    except Exception:
                        name = str(idx)
                    msg = "Field '%s': %s" % (name, exc)
                    if msg not in result.warnings:
                        result.warnings.append(msg)
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

    result.attributes_copied = copied
    result.targets_updated = len(list(target_features))
    result.success = True
    return result


def _renderer_kind(renderer):
    """Best-effort classification of a QGIS renderer into a simple string."""
    if renderer is None:
        return "none"
    # Prefer the public type() string when available.
    try:
        rtype = renderer.type()
        if rtype:
            return str(rtype)
    except Exception:
        pass
    return type(renderer).__name__


def copy_style(layer, source_feature, target_features, result=None):
    """Copy the visual style from source to targets according to renderer type.

    * Single symbol: nothing to do, the symbol is shared by the whole layer.
    * Categorized / Graduated: the symbol is driven by the value of the
      classification attribute, so we copy that attribute value (which the
      attribute-copy step already handles, but we ensure it explicitly).
    * Rule-based / unknown: copying attributes is the safest portable action;
      the rule expressions then re-evaluate the symbol for the targets.

    The layer is repainted at the end.

    :returns: MatchPropResult
    """
    if result is None:
        result = MatchPropResult()

    renderer = None
    try:
        renderer = layer.renderer()
    except Exception:
        renderer = None

    kind = _renderer_kind(renderer)

    class_attr = None
    if "categor" in kind.lower() or "graduated" in kind.lower():
        try:
            class_attr = renderer.classAttribute()
        except Exception:
            class_attr = None

    if kind in ("singleSymbol", "RuleRenderer", "none") and not class_attr:
        # singleSymbol -> shared symbol, nothing to do.
        result.style_action = "single-symbol-no-op" if kind == "singleSymbol" else kind
    if class_attr:
        fields = layer.fields()
        try:
            idx = fields.indexFromName(class_attr)
        except Exception:
            idx = -1
        if idx is not None and idx >= 0:
            try:
                value = source_feature.attribute(idx)
            except Exception:
                value = None
            layer.beginEditCommand("MatchProp: copy style class")
            try:
                for target in target_features:
                    try:
                        layer.changeAttributeValue(target.id(), idx, value)
                    except Exception:
                        continue
                layer.endEditCommand()
                result.style_action = "classified:%s" % class_attr
            except Exception as exc:
                try:
                    layer.destroyEditCommand()
                except Exception:
                    pass
                result.warnings.append("Style copy failed: %s" % exc)
        else:
            result.style_action = "classified-field-missing"

    try:
        layer.triggerRepaint()
    except Exception:
        pass

    return result


def match_properties(layer, copy_attrs=True, copy_visual=True):
    """High level entry: read the selection, copy attributes and/or style.

    :param layer: a QgsVectorLayer-like object.
    :returns: MatchPropResult describing the outcome.
    """
    result = MatchPropResult()

    try:
        selected = list(layer.selectedFeatures())
    except Exception as exc:
        result.error = "Cannot read selection: %s" % exc
        return result

    try:
        source, targets = select_source_and_targets(selected)
    except ValueError as exc:
        result.error = str(exc)
        return result

    if copy_attrs:
        copy_attributes(layer, source, targets, result)
        if result.error:
            return result

    if copy_visual:
        copy_style(layer, source, targets, result)

    result.targets_updated = len(targets)
    result.success = result.error is None
    return result
