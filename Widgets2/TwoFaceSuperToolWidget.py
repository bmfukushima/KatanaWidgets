from PyQt5.QtWidgets import (
    QWidget, QStackedWidget, QTabWidget, QVBoxLayout, QLabel,
    QStackedLayout, QHBoxLayout, QMenu
)
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QPixmap

try:
    from Katana import UI4
except ModuleNotFoundError:
    pass
# local import... because PYTHONPATH is not registered yet
from .AbstractSuperToolEditor import AbstractSuperToolEditor

from Utils2 import getWidgetAncestor

from Utils2.colors import (
    MAYBE_HOVER_COLOR_RGBA,
    KATANA_LOCAL_YELLOW,
    TEXT_COLOR
)




class TwoFacedSuperToolWidget(AbstractSuperToolEditor):
    """
    This is the top level layout that encompasses all of the super tools
    in the which will have two faces, design, and use.  The design portion
    of the layout can have more faces as well ( custom tab ).  The design
    portion at a bare minimum should always have the tab for creating a GUI
    for the user.


    TwoFacedWidget
    VBox
        |-- QStackedWidget
        |       |-- ViewWidget ( QWidget )
        |       |-- DesignWidget ( CustomTab )
        |               |-- TwoFacedTabBarWidget ( This can flop around... )
                                NOTE: If only 1 node is being edited... then...
                                    this will display at the top of the params?
        |               |-- tab_content_layout ( StackedLayout )
        |                   |-- User Params ( Create GUI)
        |                   |-- Triggers ( Setup Signals )
        |                   |-- Node Edit ( Nodegraph / params )
        |-- Resizer

    TODO:
        *   Get toggle button into wrench icon
                --> Edit user parameters toggle?
        *   Wrench Icon | Publish/Edit modes?
                NodeActionDelegate.UpdateWrenchMenuWithDelegates(menu, node, hints)
    """
    def __init__(self, parent, node):

        super(TwoFacedSuperToolWidget, self).__init__(parent, node)
        QVBoxLayout(self)

        self.main_widget = QStackedWidget(self)
        self._design_widget = TwoFacedDesignWidget(self)
        self._view_widget = TwoFacedViewWidget(self)
        resize_widget = UI4.Widgets.VBoxLayoutResizer(self)

        self.main_widget.addWidget(self._design_widget)
        self.main_widget.addWidget(self._view_widget)

        self.layout().addWidget(self.main_widget)
        self.layout().addWidget(resize_widget)
        #
        # self.bebop_button = TwoFacedMenuButton(self)
        #
        # from UI4.Widgets import PanelScrollArea
        # panel_scroll_area = getWidgetAncestor(self, PanelScrollArea)
        #
        # layout = panel_scroll_area.widget().layout()
        # widget = layout.itemAt(0).widget()
        # rightf = widget.getRightControlFWidgets()
        # rightf.layout().insertWidget(0, self.bebop_button)

    """ PROPERTIES ( WIDGET )"""
    def getDesignWidget(self):
        return self._design_widget

    def setDesignWidget(self, design_widget):
        self._design_widget = design_widget

    def getViewWidget(self):
        return self._view_widget

    def setViewWidget(self, view_widget):
        self._view_widget = view_widget


class TwoFacedDesignWidget(QWidget):
    """
    This is the designing portion of this editor.  This is where the TD
    will design a custom UI/hooks/handlers for the tool for the end user,
    which will be displayed in the ViewWidget

    Essentially this is a custom tab widget.  Where the name
        tab: refers to the small part at the top for selecting selctions
        tab_bar: refers to the bar at the top containing all of the afformentioned tabs

    """
    def __init__(self, parent=None):
        super(TwoFacedDesignWidget, self).__init__(parent)
        QVBoxLayout(self)

        # create widgets
        self.tab_bar_widget = TwoFacedTabBarWidget(self)
        self.tab_content_layout = QStackedLayout()

        # add widgets to layout
        self.layout().addWidget(self.tab_bar_widget)
        self.layout().addLayout(self.tab_content_layout)

    def insertTab(self, index, widget, name):
        """
        Creates a new tab at  the specified index

        Args:
            index (int): index to insert widget at
            widget (QWidget): widget to be displayed at that index
            name (str): name of widget
        TODO:
            make this more modular... the indexes need to shift for
            the rest of the widgets if something is moved... Otherwise it will
            break =(

        """
        # insert tab content widget
        self.tab_content_layout.insertWidget(index, widget)

        # create tab tab widget
        tab = TwoFacedTabTabWidget(self, name, index)
        self.tab_bar_widget.insertWidget(index, tab)


class TwoFacedTabBarWidget(QWidget):
    """
    The top bar of the Two Faced Design Widget containing all of the tabs
    """
    def __init__(self, parent=None):
        super(TwoFacedTabBarWidget, self).__init__(parent)
        QHBoxLayout(self)
        self.layout().setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)

    def insertWidget(self, index, widget):
        self.layout().insertWidget(index, widget)

    def clearSelectedTab(self):
        for index in range(self.layout().count()):
            tab = self.layout().itemAt(index).widget()
            tab.is_selected = False


class TwoFacedTabTabWidget(QLabel):
    """
    This is the tab's tab.

    TODO:
        *   Update Font Size dynamically:
                if prefKey == PrefNames.APPLICATION_FONTSIZE
                prefChanged
                self.setFixedHeight(self.height() * 2)
    """
    def __init__(self, parent, text, index):
        super(TwoFacedTabTabWidget, self).__init__(parent)
        self.setText(text)
        self.index = index

        self.setAlignment(Qt.AlignCenter)
        style_sheet = """
        QLabel:hover{color: rgba%s}
        QLabel[is_selected=false]{
            border: 2px solid rgba%s;
            border-top: None;
            border-left: None;
            color: rgba%s;
        }
        QLabel[is_selected=true]{
            border: 2px solid rgba%s ;
            border-left: None;
            border-bottom: None;
            color: rgba%s;
        }
        """%(
            repr(MAYBE_HOVER_COLOR_RGBA),
            repr(MAYBE_HOVER_COLOR_RGBA),
            repr(TEXT_COLOR),
            repr(MAYBE_HOVER_COLOR_RGBA),
            repr(KATANA_LOCAL_YELLOW)
        )
        self.setStyleSheet(style_sheet)


    def mousePressEvent(self, event):
        self.parent().parent().tab_content_layout.setCurrentIndex(self.index)

        # reset all other tabs to not current
        self.parent().clearSelectedTab()

        # set this to current
        self.is_selected = True
        # self.style().unpolish(self)
        # self.style().polish(self)
        # self.update()
        # udpate style sheets?

    """ PROPERTIES """
    @property
    def is_selected(self):
        return self._is_selected

    @is_selected.setter
    def is_selected(self, is_selected):
        self.setProperty('is_selected', is_selected)
        self._is_selected = is_selected
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index


class TwoFacedViewWidget(QWidget):
    """
    This is the main display for the user.  This should be dynamically populated
    from the UI created in the Design Widget
    """
    def __init__(self, parent=None):
        super(TwoFacedViewWidget, self).__init__(parent)
        QVBoxLayout(self)
        self.layout().addWidget(QLabel('View Widget'))

