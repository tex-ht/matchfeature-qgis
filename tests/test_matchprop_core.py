# -*- coding: utf-8 -*-
"""Unit tests for matchprop_core using PyQGIS mocks (no QGIS required)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from matchprop.matchprop_core import (  # noqa: E402
    select_source_and_targets,
    copy_attributes,
    copy_style,
    match_properties,
)
from mock_qgis import (  # noqa: E402
    MockVectorLayer,
    MockFeature,
    MockSingleSymbolRenderer,
    MockCategorizedRenderer,
    MockGraduatedRenderer,
)


def make_layer(**kwargs):
    # fields: fid (pk), name, type, value
    f_src = MockFeature(5, [5, "ROAD", "primary", 10])
    f_t1 = MockFeature(2, [2, "", "", 0])
    f_t2 = MockFeature(9, [9, "", "", 0])
    layer = MockVectorLayer(
        field_names=["fid", "name", "type", "value"],
        features=[f_src, f_t1, f_t2],
        pk_indexes=[0],
        **kwargs,
    )
    return layer, f_src, f_t1, f_t2


class TestSourceSelection(unittest.TestCase):
    def test_source_is_min_fid(self):
        _, f_src, f_t1, f_t2 = make_layer()
        # f_t1 has fid 2 (smallest) -> it becomes the source
        source, targets = select_source_and_targets([f_src, f_t1, f_t2])
        self.assertEqual(source.id(), 2)
        self.assertEqual(sorted(t.id() for t in targets), [5, 9])

    def test_requires_two_features(self):
        f = MockFeature(1, [1])
        with self.assertRaises(ValueError):
            select_source_and_targets([f])


class TestCopyAttributes(unittest.TestCase):
    def test_copies_non_key_fields(self):
        layer, f_src, f_t1, f_t2 = make_layer()
        # Force a known source explicitly (highest fid) and two targets.
        result = copy_attributes(layer, f_src, [f_t1, f_t2])
        self.assertTrue(result.success)
        # name/type/value copied to both targets -> 3 fields * 2 targets = 6
        self.assertEqual(result.attributes_copied, 6)
        self.assertEqual(f_t1.attribute(1), "ROAD")
        self.assertEqual(f_t1.attribute(2), "primary")
        self.assertEqual(f_t1.attribute(3), 10)
        self.assertEqual(f_t2.attribute(1), "ROAD")

    def test_skips_primary_key_field(self):
        layer, f_src, f_t1, f_t2 = make_layer()
        copy_attributes(layer, f_src, [f_t1])
        # fid (idx 0) must NOT be changed
        self.assertEqual(f_t1.attribute(0), 2)
        # ensure changeAttributeValue never called with idx 0
        self.assertFalse(any(c[1] == 0 for c in layer.change_calls))

    def test_undo_command_bracketing(self):
        layer, f_src, f_t1, _ = make_layer()
        copy_attributes(layer, f_src, [f_t1])
        self.assertEqual(layer.edit_commands, ["MatchProp: copy attributes"])
        self.assertEqual(layer.committed_commands, 1)
        self.assertEqual(layer.destroyed_commands, 0)

    def test_read_only_field_excluded(self):
        # field idx 2 ("type") is read-only -> never even attempted
        layer, f_src, f_t1, _ = make_layer(read_only_indexes=[2])
        result = copy_attributes(layer, f_src, [f_t1])
        self.assertTrue(result.success)
        self.assertFalse(any(c[1] == 2 for c in layer.change_calls))
        self.assertEqual(f_t1.attribute(2), "")  # unchanged

    def test_incompatible_field_skipped_silently(self):
        # field idx 2 ("type") rejects the write at runtime -> recorded, no abort
        layer, f_src, f_t1, _ = make_layer(reject_write_indexes=[2])
        result = copy_attributes(layer, f_src, [f_t1])
        self.assertTrue(result.success)
        self.assertIn("type", result.fields_skipped)
        # other fields still copied
        self.assertEqual(f_t1.attribute(1), "ROAD")


class TestCopyStyle(unittest.TestCase):
    def test_single_symbol_no_op(self):
        layer, f_src, f_t1, _ = make_layer(renderer=MockSingleSymbolRenderer())
        result = copy_style(layer, f_src, [f_t1])
        self.assertEqual(result.style_action, "single-symbol-no-op")
        self.assertEqual(layer.repaint_count, 1)

    def test_categorized_copies_class_attribute(self):
        layer, f_src, f_t1, f_t2 = make_layer(
            renderer=MockCategorizedRenderer("type")
        )
        result = copy_style(layer, f_src, [f_t1, f_t2])
        self.assertEqual(result.style_action, "classified:type")
        # class attribute "type" (idx 2) copied from source value "primary"
        self.assertEqual(f_t1.attribute(2), "primary")
        self.assertEqual(f_t2.attribute(2), "primary")
        self.assertEqual(layer.repaint_count, 1)

    def test_graduated_copies_class_attribute(self):
        layer, f_src, f_t1, _ = make_layer(
            renderer=MockGraduatedRenderer("value")
        )
        result = copy_style(layer, f_src, [f_t1])
        self.assertEqual(result.style_action, "classified:value")
        self.assertEqual(f_t1.attribute(3), 10)

    def test_classified_missing_field(self):
        layer, f_src, f_t1, _ = make_layer(
            renderer=MockCategorizedRenderer("does_not_exist")
        )
        result = copy_style(layer, f_src, [f_t1])
        self.assertEqual(result.style_action, "classified-field-missing")


class TestMatchProperties(unittest.TestCase):
    def test_full_flow_single_symbol(self):
        layer, f_src, f_t1, f_t2 = make_layer()
        result = match_properties(layer)
        self.assertTrue(result.success)
        # source is min fid (2) -> targets are fid 5 and 9
        self.assertEqual(result.targets_updated, 2)
        # targets inherit the source (fid 2) values: name "" type "" value 0
        self.assertEqual(f_src.attribute(1), "")  # untouched (it's the source)

    def test_full_flow_categorized(self):
        layer, f_src, f_t1, f_t2 = make_layer(
            renderer=MockCategorizedRenderer("type")
        )
        result = match_properties(layer)
        self.assertTrue(result.success)
        self.assertTrue(result.style_action.startswith("classified"))

    def test_error_when_single_feature(self):
        f = MockFeature(1, [1, "x", "y", 0])
        layer = MockVectorLayer(
            field_names=["fid", "name", "type", "value"],
            features=[f],
            pk_indexes=[0],
        )
        layer.setSelected([f])
        result = match_properties(layer)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
