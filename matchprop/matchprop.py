# -*- coding: utf-8 -*-
"""MATCHPROP plugin main class.

Two-step workflow (AutoCAD MATCHPROP style):
  1. Select exactly 1 source feature and click the button -> properties are
     COPIED (stored).
  2. Select 1 or more target features and click the button again -> properties
     are APPLIED to the targets. The source is then cleared.
"""

import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import Qgis, QgsWkbTypes

from .matchprop_core import capture_source, apply_source


class MatchProp(object):
    """QGIS plugin implementation registering the MATCHPROP action."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "&MatchProp"
        self.toolbar = None
        self.action = None

        # State for the two-step copy/paste workflow.
        self._source = None            # dict {field_index: value}
        self._source_layer_id = None   # layer the source was copied from
        self._source_fid = None        # feature id of the source

    # ------------------------------------------------------------------ utils
    @staticmethod
    def tr(message):
        return QCoreApplication.translate("MatchProp", message)

    def _icon(self):
        path = os.path.join(self.plugin_dir, "icon.png")
        if os.path.exists(path):
            return QIcon(path)
        return QIcon(":/plugins/matchprop/icon.png")

    def _reset_source(self):
        self._source = None
        self._source_layer_id = None
        self._source_fid = None

    # ----------------------------------------------------------------- gui api
    def initGui(self):
        self.toolbar = self.iface.addToolBar("MatchProp")
        self.toolbar.setObjectName("MatchPropToolbar")

        self.action = QAction(self._icon(), self.tr("MatchProp"), self.iface.mainWindow())
        self.action.setObjectName("MatchPropAction")
        self.action.setToolTip(
            self.tr(
                "MatchProp (2 steps): 1) select the SOURCE feature and click to "
                "copy; 2) select the TARGET feature(s) and click again to apply."
            )
        )
        self.action.setStatusTip(self.action.toolTip())
        self.action.triggered.connect(self.run)

        self.toolbar.addAction(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
        if self.toolbar is not None:
            del self.toolbar
            self.toolbar = None
        self.actions = []
        self._reset_source()

    # ------------------------------------------------------------- validation
    def _validate_layer(self, layer):
        """Return (ok, level, message)."""
        if layer is None or not hasattr(layer, "selectedFeatures"):
            return False, Qgis.Warning, self.tr("Select an active vector layer first.")
        try:
            if layer.geometryType() == QgsWkbTypes.NullGeometry:
                return False, Qgis.Warning, self.tr("This layer has no geometry.")
        except Exception:
            pass
        if not layer.isEditable():
            return (
                False,
                Qgis.Warning,
                self.tr("Layer is not in edit mode. Toggle editing and try again."),
            )
        return True, Qgis.Info, ""

    # -------------------------------------------------------------------- run
    def run(self):
        bar = self.iface.messageBar()
        layer = self.iface.activeLayer()

        ok, level, message = self._validate_layer(layer)
        if not ok:
            bar.pushMessage(self.tr("MatchProp"), message, level=level, duration=6)
            return

        selected = list(layer.selectedFeatures())

        # If the armed source belongs to a different layer, drop it.
        if self._source is not None and self._source_layer_id != layer.id():
            self._reset_source()

        if self._source is None:
            self._do_copy(layer, selected, bar)
        else:
            self._do_apply(layer, selected, bar)

    # ----------------------------------------------------------- step 1: copy
    def _do_copy(self, layer, selected, bar):
        if len(selected) != 1:
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr(
                    "Step 1: select exactly 1 SOURCE feature, then click to copy "
                    "its properties."
                ),
                level=Qgis.Warning,
                duration=6,
            )
            return

        source = selected[0]
        self._source = capture_source(layer, source)
        self._source_layer_id = layer.id()
        self._source_fid = source.id()
        bar.pushMessage(
            self.tr("MatchProp"),
            self.tr(
                "Source copied (%d field(s)). Now select the target feature(s) "
                "and click MatchProp again to apply."
            )
            % len(self._source),
            level=Qgis.Success,
            duration=6,
        )

    # ---------------------------------------------------------- step 2: apply
    def _do_apply(self, layer, selected, bar):
        # Targets = current selection, excluding the source feature itself.
        targets = [f for f in selected if f.id() != self._source_fid]

        if not targets:
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr(
                    "Source is copied. Step 2: select at least 1 TARGET feature "
                    "(different from the source) and click again."
                ),
                level=Qgis.Warning,
                duration=6,
            )
            return

        result = apply_source(layer, self._source, targets)

        if not result.success or result.error:
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr("Error: ") + (result.error or self.tr("unknown error")),
                level=Qgis.Critical,
                duration=8,
            )
            return

        # Done -> clear the armed source.
        self._reset_source()

        if result.fields_skipped:
            detail = self.tr(" (skipped: ") + ", ".join(result.fields_skipped) + ")"
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr("Properties applied to %d feature(s)") % result.targets_updated
                + detail,
                level=Qgis.Warning,
                duration=7,
            )
        else:
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr("Properties applied to %d feature(s)") % result.targets_updated,
                level=Qgis.Success,
                duration=5,
            )
