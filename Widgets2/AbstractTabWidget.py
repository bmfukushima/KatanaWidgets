"""
TODO:
    Multi Display mode:
        clicking on tabs will append them to the operation and ADD
        them to the layout.  So that you can look at multiple tabs at the
        same time...
            - QStackedLayout vs HBox vs VBox?
            - Potentially Layout needs to be subclassed?
    Default Widget Type:
        instead of every label having its own widget.  Creating one
        base class to always populate from, and dynamically
        creating the widget on each update.

"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QBoxLayout, QStackedLayout
)
from PyQt5.QtCore import Qt


from Utils2.colors import (
    MAYBE_HOVER_COLOR_RGBA,
    KATANA_LOCAL_YELLOW
)

from Utils2 import getWidgetAncestor


class AbstractTabWidget(QWidget):
    """
    This is the designing portion of this editor.  This is where the TD
    will design a custom UI/hooks/handlers for the tool for the end user,
    which will be displayed in the ViewWidget

    Args:
        direction (Class Attr): Determines where the tab bar should be placed.
            The default value is NORTH

    Essentially this is a custom tab widget.  Where the name
        label: refers to the small part at the top for selecting selctions
        bar: refers to the bar at the top containing all of the afformentioned tabs
        widget: refers to the area that displays the GUI for each tab

    """
    NORTH = 'north'
    SOUTH = 'south'
    EAST = 'east'
    WEST = 'west'
    OUTLINE_COLOR = MAYBE_HOVER_COLOR_RGBA
    OUTLINE_WIDTH = 1
    SELECTED_COLOR = KATANA_LOCAL_YELLOW

    def __init__(self, parent=None, direction=NORTH):
        super(AbstractTabWidget, self).__init__(parent)
        QBoxLayout(QBoxLayout.LeftToRight, self)
        self.layout().setSpacing(0)

        # create widgets
        self.tab_label_bar_widget = TabLabelBarWidget(self)
        self.tab_widget_layout = QStackedLayout()

        # add widgets to layout
        self.layout().addWidget(self.tab_label_bar_widget)
        self.layout().addLayout(self.tab_widget_layout)

        self.setTabPosition(direction)

    def setTabPosition(self, direction):
        """
        Sets position of the tab label bar.
        """
        self.direction = direction

        if direction == AbstractTabWidget.NORTH:
            self.layout().setDirection(QBoxLayout.TopToBottom)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.LeftToRight)
        elif direction == AbstractTabWidget.SOUTH:
            self.layout().setDirection(QBoxLayout.BottomToTop)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.LeftToRight)
        elif direction == AbstractTabWidget.EAST:
            self.layout().setDirection(QBoxLayout.RightToLeft)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.TopToBottom)
        elif direction == AbstractTabWidget.WEST:
            self.layout().setDirection(QBoxLayout.LeftToRight)
            self.tab_label_bar_widget.layout().setDirection(QBoxLayout.TopToBottom)
        self.tab_label_bar_widget.updateStyleSheets()

    def insertTab(self, index, widget, name, tab_label=None):
        """
        Creates a new tab at  the specified index

        Args:
            index (int): index to insert widget at
            widget (QWidget): widget to be displayed at that index
            name (str): name of widget
            tab_label (widget): If provided this will use the widget
                provided as a label, as opposed to the default one.
        """
        # insert tab widget
        self.tab_widget_layout.insertWidget(index, widget)
        # widget.setStyleSheet("""border: 1px solid rgba(0,0,0,255)""")
        # create tab label widget
        if not tab_label:
            tab_label = TabLabelWidget(self, name, index)
        tab_label.tab_widget = widget

        self.tab_label_bar_widget.insertWidget(index, tab_label)

        # update all label index
        self.__updateAllTabLabelIndexs()

    def removeTab(self, index):
        self.tab_label_bar_widget.itemAt(index).widget().setParent(None)
        self.tab_widget_layout.itemAt(index).widget().setParent(None)
        self.__updateAllTabLabelIndexs()

    def __updateAllTabLabelIndexs(self):
        """
        Sets the tab labels index to properly update to its current
        position in the Tab Widget.
        """
        for index, label in enumerate(self.tab_label_bar_widget.getAllLabels()):
            label.index = index

    """ PROPERTIES """
    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, direction):
        self._direction = direction


class TabLabelBarWidget(QWidget):
    """
    The top bar of the Two Faced Design Widget containing all of the tabs
    """
    def __init__(self, parent=None):
        super(TabLabelBarWidget, self).__init__(parent)
        QBoxLayout(QBoxLayout.LeftToRight, self)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def insertWidget(self, index, widget):
        self.layout().insertWidget(index, widget)

    def clearSelectedTab(self):
        """
        Removes the current tab from being selected
        """
        for index in range(self.layout().count()):
            tab = self.layout().itemAt(index).widget()
            tab.is_selected = False

    def getAllLabels(self):
        """
        Gets all of the Tab Labels in this bar

        returns (list): of TabLabelWidget
        """
        _all_labels = []
        for index in range(self.layout().count()):
            label = self.layout().itemAt(index).widget()
            _all_labels.append(label)

        return _all_labels

    def updateStyleSheets(self):
        labels = self.getAllLabels()
        for label in labels:
            label.setupStyleSheet()


class TabLabelWidget(QLabel):
    """
    This is the tab's tab.

    Attributes:
        is_selected (bool): Determines if this label is currently selected
        tab_widget (widget): The widget that this label correlates to.

    TODO:
        *   Update Font Size dynamically:
                if prefKey == PrefNames.APPLICATION_FONTSIZE
                prefChanged
                self.setFixedHeight(self.height() * 2)
    """
    def __init__(self, parent, text, index):
        super(TabLabelWidget, self).__init__(parent)
        # set up attrs
        self.setText(text)
        self.index = index

        # set up display
        self.setAlignment(Qt.AlignCenter)
        self.is_selected = False
        self.setupStyleSheet()
        self.setMinimumSize(35, 35)

    def setupStyleSheet(self):
        """
        Sets the style sheet for the outline based off of the direction of the parent.

        """
        tab_widget = getWidgetAncestor(self, AbstractTabWidget)
        direction = tab_widget.direction
        style_sheet_args = [
            repr(AbstractTabWidget.OUTLINE_COLOR),
            repr(AbstractTabWidget.SELECTED_COLOR),
            AbstractTabWidget.OUTLINE_WIDTH
        ]
        if direction == AbstractTabWidget.NORTH:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-top: None;
                border-left: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-left: None;
                border-bottom: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        elif direction == AbstractTabWidget.SOUTH:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-left: None;
                border-bottom: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-left: None;
                border-top: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        elif direction == AbstractTabWidget.EAST:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-top: None;
                border-right: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-top: None;
                border-left: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        elif direction == AbstractTabWidget.WEST:
            style_sheet = """
            QLabel:hover{{color: rgba{0}}}
            QLabel[is_selected=false]{{
                border: {2}px solid rgba{0};
                border-top: None;
                border-left: None;
            }}
            QLabel[is_selected=true]{{
                border: {2}px solid rgba{0} ;
                border-top: None;
                border-right: None;
                color: rgba{1};
            }}
            """.format(*style_sheet_args)
        self.setStyleSheet(style_sheet)

    def mousePressEvent(self, event):
        main_widget = getWidgetAncestor(self, AbstractTabWidget)
        main_widget.tab_widget_layout.setCurrentIndex(self.index)

        # reset all other tabs to not current
        self.parent().clearSelectedTab()

        # set this to current
        self.is_selected = True

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

    @property
    def tab_widget(self):
        return self._tab_widget

    @tab_widget.setter
    def tab_widget(self, tab_widget):
        self._tab_widget = tab_widget


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QCursor
    app = QApplication(sys.argv)

    w = AbstractTabWidget()
    for x in range(3):
        nw = QLabel(str(x))
        w.insertTab(0, nw, str(x))

    w.show()
    w.move(QCursor.pos())
    sys.exit(app.exec_())
