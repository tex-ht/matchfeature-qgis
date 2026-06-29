# -*- coding: utf-8 -*-
"""MATCHPROP plugin main class: toolbar button, menu entry and validation."""

import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from qgis.core import Qgis, QgsWkbTypes

from .matchprop_core import match_properties


class MatchProp(object):
    """QGIS plugin implementation registering the MATCHPROP action."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = "&MatchProp"
        self.toolbar = None
        self.action = None

    # ------------------------------------------------------------------ utils
    @staticmethod
    def tr(message):
        return QCoreApplication.translate("MatchProp", message)

    def _icon(self):
        path = os.path.join(self.plugin_dir, "icon.png")
        if os.path.exists(path):
            return QIcon(path)
        return QIcon(":/plugins/matchprop/icon.png")

    # ----------------------------------------------------------------- gui api
    def initGui(self):
        self.toolbar = self.iface.addToolBar("MatchProp")
        self.toolbar.setObjectName("MatchPropToolbar")

        self.action = QAction(self._icon(), self.tr("MatchProp"), self.iface.mainWindow())
        self.action.setObjectName("MatchPropAction")
        self.action.setToolTip(
            self.tr(
                "MatchProp: select the source feature + target features "
                "(same layer, edit mode), then click here to copy attributes "
                "and style."
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

    # ------------------------------------------------------------- validation
    def _validate(self, layer):
        """Return (ok, level, message). level is a Qgis.MessageLevel."""
        if layer is None or not hasattr(layer, "selectedFeatures"):
            return False, Qgis.Warning, self.tr("Select an active vector layer first.")

        try:
            geom_type = layer.geometryType()
        except Exception:
            geom_type = None
        if geom_type == QgsWkbTypes.NullGeometry:
            return False, Qgis.Warning, self.tr("This layer has no geometry.")

        if not layer.isEditable():
            return (
                False,
                Qgis.Warning,
                self.tr("Layer is not in edit mode. Toggle editing and try again."),
            )

        count = layer.selectedFeatureCount()
        if count < 2:
            return (
                False,
                Qgis.Warning,
                self.tr(
                    "Select at least 2 features in the same layer: "
                    "1 source + 1 or more targets."
                ),
            )
        return True, Qgis.Info, ""

    # -------------------------------------------------------------------- run
    def run(self):
        layer = self.iface.activeLayer()
        ok, level, message = self._validate(layer)
        bar = self.iface.messageBar()
        if not ok:
            bar.pushMessage(self.tr("MatchProp"), message, level=level, duration=6)
            return

        result = match_properties(layer, copy_attrs=True, copy_visual=True)

        if not result.success or result.error:
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr("Error: ") + (result.error or self.tr("unknown error")),
                level=Qgis.Critical,
                duration=8,
            )
            return

        if result.fields_skipped or result.warnings:
            detail = ""
            if result.fields_skipped:
                detail = self.tr(" (skipped: ") + ", ".join(result.fields_skipped) + ")"
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr("Properties copied to %d feature(s)") % result.targets_updated
                + detail,
                level=Qgis.Warning,
                duration=7,
            )
        else:
            bar.pushMessage(
                self.tr("MatchProp"),
                self.tr("Properties copied to %d feature(s)") % result.targets_updated,
                level=Qgis.Success,
                duration=5,
            )
