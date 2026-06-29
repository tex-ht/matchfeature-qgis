# -*- coding: utf-8 -*-
"""MATCHPROP QGIS plugin entry point.

Copies attributes + visual style from one source feature to one or more
target features within the same layer, inspired by AutoCAD's MATCHPROP.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pragma: no cover - QGIS runtime hook
    """Load MatchProp class.

    :param iface: A QGIS interface instance (QgisInterface).
    """
    from .matchprop import MatchProp
    return MatchProp(iface)
