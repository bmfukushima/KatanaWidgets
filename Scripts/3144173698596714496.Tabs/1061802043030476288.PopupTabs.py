from qtpy.QtWidgets import QPushButton, QWidget, QVBoxLayout, QHBoxLayout
from qtpy.QtGui import QFont, QCursor, QPainter, QPen, QColor
from qtpy.QtCore import QPoint, Qt

from cgwidgets.utils import centerWidgetOnCursor, getWidgetAncestor
from cgwidgets.settings import iColor
from cgwidgets.widgets import ButtonInputWidget

from Utils2 import getFontSize

from Katana import UI4


class TabDisplayLabelWidget(ButtonInputWidget):
    """ One single button/widget that shows the top"""
    def __init__(self, parent=None, panel=None):
        super(TabDisplayLabelWidget, self).__init__(parent)
        self._panel = panel
        self.setText(panel.objectName().replace('Tab', ''))

        self.setUserClickedEvent(self.raiseTab)
        self.setFixedHeight(getFontSize() * 5)
        font = QFont()
        font.setPointSize(100)
        self.setFont(font)
        self.default_style_sheet = self.styleSheet()

    def getPanel(self):
        return self._panel
  
    def setPanel(self, panel):
        self._panel = panel
    """ UTILS """
    def raiseTab(self, widget):
        UI4.App.Tabs.RaiseTab(self.getPanel())
        getWidgetAncestor(self, TabSwitcherWidget).close()
        getWidgetAncestor(self, TabSwitcherWidget).deleteLater()

    """ EVENTS """
    # def enterEvent(self, *args, **kwargs):
    #     style_sheet = """
    #         border-style: inset;
    #         border-width: 2px;
    #         border-radius: 1px;
    #         border-color: rgba{RGBA_SELECTED}; """.format(
    #         RGBA_SELECTED=iColor["rgba_selected_hover_2"]
    #     )
    #     self.setStyleSheet(style_sheet)
    #     return QWidget.enterEvent(self, *args, **kwargs)
    #
    # def leaveEvent(self, *args, **kwargs):
    #     self.setStyleSheet(self.default_style_sheet)
    #     return QPushButton.leaveEvent(self, *args, **kwargs)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            getWidgetAncestor(self, TabSwitcherWidget).close()
        return QWidget.keyPressEvent(self, event)


class TabSwitcherWidget(QWidget):
    def __init__(self, parent=None):
        super(TabSwitcherWidget, self).__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        QVBoxLayout(self)
        self.current_tab = None
        self.setMouseTracking(True)
        # self.createAllBoxes()
        self.createAllPanels()
        self.setAcceptDrops(True)

    @staticmethod
    def getTabSiblings(tab):
        """ Returns a list of all of the siblings of the Tab provided

        Args:
            tab (KatanaTab): tab to get all siblings of

        Returns (list): of KatanaTabs"""
        topMostPanel = tab.parentWidget().parentWidget()
        panel_list = [x.getWidget() for x in topMostPanel.children() if hasattr(x, 'getWidget')]
        return panel_list

    @staticmethod
    def getAllVisibleTabs():
        """ Gets all of the current top level tabs

        Returns (list): of KatanaTabs """
        tabs = UI4.App.Tabs.GetAllTabs()
        visible_tab_list = []
        for tab in tabs:
            if hasattr(tab, 'isVisible'):
                if tab.isVisible():
                    visible_tab_list.append(tab)
        return visible_tab_list

    @staticmethod
    def getTabUnderCursor():
        """ Returns the current tab that is under the cursor

        Note:
            Doing a positional check, as when suing the ScriptEditor,
            the PopupDisplay will block the underCursor from registering.
        Returns (KatanaTab)"""
        for tab in TabSwitcherWidget.getAllVisibleTabs():
            tab_xpos = tab.parent().mapToGlobal(tab.pos()).x()
            tab_ypos = tab.parent().mapToGlobal(tab.pos()).y()
            tab_w = tab.width()
            tab_h = tab.height()

            cursor_pos = QCursor.pos()
            cursor_xpos = cursor_pos.x()
            cursor_ypos = cursor_pos.y()

            # check ypos
            if (tab_ypos < cursor_ypos < tab_ypos + tab_h
                and tab_xpos < cursor_xpos < tab_xpos + tab_w
            ):
                return tab

            # if tab.underMouse():
            #     return tab

        return None

    def createAllPanels(self):
        """ Creates buttons for each sibling Tab """
        current_tab = TabSwitcherWidget.getTabUnderCursor()
        if current_tab:
            for panel in TabSwitcherWidget.getTabSiblings(current_tab):
                if panel != current_tab:
                    display_widget = TabDisplayLabelWidget(self, panel=panel)
                    self.layout().addWidget(display_widget)

    def enterEvent(self, event):
        self.setFocus()
        return QWidget.enterEvent(self, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return QWidget.keyPressEvent(self, event)

    def paintEvent(self, event=None):
        """ Set transparency """
        painter = QPainter(self)
        painter.setOpacity(0.75)
        bg_color = QColor(32, 32, 32, 255)
        painter.setBrush(bg_color)
        painter.setPen(QPen(bg_color))

        # ellipse
        painter.drawRect(self.rect())
    # OLD just leaving this incase I want to revisit it sometime
    # def createAllBoxes(self):
    #     allVisibleTabs = TabSwitcherWidget.getAllVisibleTabs()
    #     widget_list = []
    #
    #     # get current tab position
    #     current_tab = TabSwitcherWidget.getTabUnderCursor()
    #     current_pos = current_tab.mapToGlobal(current_tab.rect().topLeft())
    #     allVisibleTabs.remove(current_tab)
    #     for tab in allVisibleTabs:
    #         #print tab.objectName()
    #         is_left = False
    #         is_right = False
    #         is_top = False
    #         is_bottom = False
    #         global_pos = tab.mapToGlobal(tab.rect().topLeft())
    #         #print current_pos.x() , global_pos.x()
    #         #print current_pos.y() , global_pos.y()
    #         if current_pos.x() < global_pos.x():
    #             is_left = True
    #         elif current_pos.x() > global_pos.x():
    #             is_right = True
    #         if current_pos.y() < global_pos.y():
    #             is_top = True
    #         elif current_pos.y() > global_pos.y():
    #             is_bottom = True
    #
    #         if tab.underMouse() == False:       #this line is redundant due to previous call to find the true one
    #
    #             spacing = 5
    #             ## main widget per tab
    #             ## main_widget --> widget -->layout --> buttons
    #             rect = tab.rect()
    #             left = tab.mapToGlobal(rect.topLeft()).x()
    #             top = tab.mapToGlobal(rect.topLeft()).y()
    #             width = tab.geometry().getRect()[2]
    #             height = tab.geometry().getRect()[3]
    #
    #             #widget = QWidget(main_widget)
    #             widget = TabDisplayWidget(self)
    #             widget.setGeometry(left,top,width,height)
    #             widget.setAcceptDrops(True)
    #             widget_list.append(widget)
    #             #widget.setStyleSheet('background-color: rgb(255,200,0);')
    #             layout = QHBoxLayout(widget)
    #
    #             all_panels = TabSwitcherWidget.getTabSiblings(tab)
    #             #needs to be smart enough to determine the panels orientation to the current cursor
    #             #has to be a hotkey enable, release hotkey to activate
    #             # buttons wont work as it will require a click.. and the assumption is that it is a clickless interface
    #             # hot key doesnt register during drag... has to be automated by mouse move =(
    #             usable_width = width - ((len(all_panels)+1) * spacing)
    #             panel_width = usable_width / len(all_panels)
    #
    #             for count, panel in enumerate(all_panels):
    #                 button = TabDisplayWidget(widget, panel=panel, widget_list=widget_list)
    #                 button.setObjectName(panel.objectName())
    #                 button.setFixedHeight(height)
    #                 button.setFixedWidth(panel_width)
    #
    #                 layout.addWidget(button)
    #             widget.show()


parent = UI4.App.MainWindow.CurrentMainWindow()
main_widget = TabSwitcherWidget(parent)
main_widget.show()
centerWidgetOnCursor(main_widget)

    
    
    
