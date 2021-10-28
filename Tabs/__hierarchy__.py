"""
KatanaWindow
    |- LayoutWidget --> (QT4Panels.PanelLayout --> QWidget)
        |- LayoutFrame --> (QT4Panels.PanelFrame --> QTabWidget)
        |- QStackedWidget
        |- TabWithTimeline --> (QWidget)

Layouts | bin/python/UI4/app/Layouts.py
    LayoutWidget
    LayoutFrame
QT4Panels | bin/python/UI4/software_python/QT4Panels.py
    PanelLayout
    PanelFrame
"""