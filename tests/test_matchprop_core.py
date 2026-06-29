# -*- coding: utf-8 -*-
"""Unit tests for matchprop_core using PyQGIS mocks (no QGIS required)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matchprop.matchprop_core import (  # noqa: E402
    editable_field_indexes,
    capture_source,
    apply_source,
)
from mock_qgis import (  # noqa: E402
    MockVectorLayer,
    MockFeature,
    MockCategorizedRenderer,
)


def make_layer(**kwargs):
    # fields: fid (pk), name, type, value
    f_src = MockFeature(5, [5, "ROAD", "primary", 10])     # the SOURCE
    f_t1 = MockFeature(2, [2, "", "", 0])                  # empty target (small fid!)
    f_t2 = MockFeature(9, [9, "", "", 0])
    layer = MockVectorLayer(
        field_names=["fid", "name", "type", "value"],
        features=[f_src, f_t1, f_t2],
        pk_indexes=[0],
        **kwargs,
    )
    return layer, f_src, f_t1, f_t2


class TestEditableFields(unittest.TestCase):
    def test_skips_primary_key_and_key_names(self):
        layer, _, _, _ = make_layer()
        idxs = editable_field_indexes(layer)
        self.assertEqual(idxs, [1, 2, 3])  # fid (idx 0) excluded

    def test_skips_read_only(self):
        layer, _, _, _ = make_layer(read_only_indexes=[2])
        self.assertEqual(editable_field_indexes(layer), [1, 3])

    def test_skips_identifier_like_fields(self):
        # id1 / gid / cod_id are identifiers -> excluded; idade/nome kept
        feats = [MockFeature(1, [1, 100, 9, 50, "ROAD", 7])]
        layer = MockVectorLayer(
            field_names=["fid", "id1", "gid", "idade", "nome", "cod_id"],
            features=feats,
        )
        idxs = editable_field_indexes(layer)
        # keep idade (3) and nome (4); drop fid(0), id1(1), gid(2), cod_id(5)
        self.assertEqual(idxs, [3, 4])


class TestCaptureSource(unittest.TestCase):
    def test_snapshot_values(self):
        layer, f_src, _, _ = make_layer()
        snap = capture_source(layer, f_src)
        self.assertEqual(snap, {1: "ROAD", 2: "primary", 3: 10})
        # fid must never be captured
        self.assertNotIn(0, snap)


class TestApplySource(unittest.TestCase):
    def test_applies_to_targets_not_source(self):
        # The bug scenario: source has bigger fid than the empty target.
        layer, f_src, f_t1, f_t2 = make_layer()
        snap = capture_source(layer, f_src)
        result = apply_source(layer, snap, [f_t1, f_t2])
        self.assertTrue(result.success)
        self.assertEqual(result.targets_updated, 2)
        # targets receive the SOURCE values
        self.assertEqual(f_t1.attribute(1), "ROAD")
        self.assertEqual(f_t1.attribute(3), 10)
        self.assertEqual(f_t2.attribute(2), "primary")
        # source stays intact, never overwritten with empties
        self.assertEqual(f_src.attribute(1), "ROAD")
        self.assertEqual(f_src.attribute(3), 10)

    def test_primary_key_preserved_on_targets(self):
        layer, f_src, f_t1, _ = make_layer()
        snap = capture_source(layer, f_src)
        apply_source(layer, snap, [f_t1])
        self.assertEqual(f_t1.attribute(0), 2)  # fid untouched

    def test_undo_command_bracketing(self):
        layer, f_src, f_t1, _ = make_layer()
        snap = capture_source(layer, f_src)
        apply_source(layer, snap, [f_t1])
        self.assertEqual(layer.edit_commands, ["MatchProp: apply properties"])
        self.assertEqual(layer.committed_commands, 1)
        self.assertEqual(layer.destroyed_commands, 0)
        self.assertEqual(layer.repaint_count, 1)

    def test_incompatible_field_skipped_silently(self):
        layer, f_src, f_t1, _ = make_layer(reject_write_indexes=[2])
        snap = capture_source(layer, f_src)
        result = apply_source(layer, snap, [f_t1])
        self.assertTrue(result.success)
        self.assertIn("type", result.fields_skipped)
        self.assertEqual(f_t1.attribute(1), "ROAD")  # others still applied

    def test_style_attribute_drives_categorized_symbol(self):
        # For categorized renderers, copying the class attribute (here "type")
        # is what makes the target inherit the source symbol.
        layer, f_src, f_t1, _ = make_layer(
            renderer=MockCategorizedRenderer("type")
        )
        snap = capture_source(layer, f_src)
        apply_source(layer, snap, [f_t1])
        self.assertEqual(f_t1.attribute(2), "primary")  # class attr copied
        self.assertEqual(layer.repaint_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
