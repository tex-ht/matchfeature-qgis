# -*- coding: utf-8 -*-
"""Lightweight PyQGIS mocks for unit testing matchprop_core without QGIS.

These mocks reproduce just enough of the QgsVectorLayer / QgsFeature protocol
used by matchprop_core: fields, selection, edit-command bracketing,
changeAttributeValue, primaryKeyAttributes and renderer classification.
"""


class MockField(object):
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class MockFields(object):
    def __init__(self, names):
        self._fields = [MockField(n) for n in names]

    def __len__(self):
        return len(self._fields)

    def __getitem__(self, idx):
        return self._fields[idx]

    def at(self, idx):
        return self._fields[idx]

    def indexFromName(self, name):
        for i, f in enumerate(self._fields):
            if f.name() == name:
                return i
        return -1


class MockFeature(object):
    def __init__(self, fid, attributes):
        self._id = fid
        self._attrs = list(attributes)

    def id(self):
        return self._id

    def attribute(self, idx):
        return self._attrs[idx]

    def __getitem__(self, idx):
        return self._attrs[idx]

    def setAttribute(self, idx, value):
        self._attrs[idx] = value


class MockSingleSymbolRenderer(object):
    def type(self):
        return "singleSymbol"


class MockCategorizedRenderer(object):
    def __init__(self, class_attribute):
        self._attr = class_attribute

    def type(self):
        return "categorizedSymbol"

    def classAttribute(self):
        return self._attr


class MockGraduatedRenderer(object):
    def __init__(self, class_attribute):
        self._attr = class_attribute

    def type(self):
        return "graduatedSymbol"

    def classAttribute(self):
        return self._attr


class MockVectorLayer(object):
    def __init__(self, field_names, features, renderer=None,
                 pk_indexes=None, editable=True, read_only_indexes=None,
                 reject_write_indexes=None):
        self._fields = MockFields(field_names)
        self._features = {f.id(): f for f in features}
        self._selected = list(features)
        self._renderer = renderer or MockSingleSymbolRenderer()
        self._pk = pk_indexes or []
        self._editable = editable
        self._read_only = set(read_only_indexes or [])
        # Fields that are editable in the form but reject writes at runtime
        # (e.g. type-incompatible value coming from another field).
        self._reject_write = set(reject_write_indexes or [])

        # instrumentation
        self.edit_commands = []          # list of begun command labels
        self.committed_commands = 0
        self.destroyed_commands = 0
        self.repaint_count = 0
        self.change_calls = []           # (fid, idx, value, ok)
        self._open_command = False

    # --- fields / selection
    def fields(self):
        return self._fields

    def primaryKeyAttributes(self):
        return self._pk

    def fieldIsReadOnly(self, idx):
        return idx in self._read_only

    def isEditable(self):
        return self._editable

    def selectedFeatures(self):
        return list(self._selected)

    def selectedFeatureCount(self):
        return len(self._selected)

    def setSelected(self, features):
        self._selected = list(features)

    # --- renderer
    def renderer(self):
        return self._renderer

    def triggerRepaint(self):
        self.repaint_count += 1

    # --- editing
    def beginEditCommand(self, label):
        self.edit_commands.append(label)
        self._open_command = True

    def endEditCommand(self):
        self._open_command = False
        self.committed_commands += 1

    def destroyEditCommand(self):
        self._open_command = False
        self.destroyed_commands += 1

    def changeAttributeValue(self, fid, idx, value):
        # Simulate an incompatible field rejection at write time.
        if idx in self._reject_write:
            self.change_calls.append((fid, idx, value, False))
            return False
        feat = self._features.get(fid)
        if feat is None:
            self.change_calls.append((fid, idx, value, False))
            return False
        feat.setAttribute(idx, value)
        self.change_calls.append((fid, idx, value, True))
        return True
