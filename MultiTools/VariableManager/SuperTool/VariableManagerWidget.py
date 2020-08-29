"""
TODO:
    * Add redo / undo display updates...
        - Need to check to make sure this all works...
    *   Expand / Collapse
            - Default states seem bjorked...
            - Add menu / hotkey options
                    - RMB Menu
                    - Arrow keys or WASD?
    *   Auto create handler needs to go in init function
            - Check to see if the variable exists, if it does bypass.
                If it does not, create the pattern as the last item in the group...
    *   Node Type Change
            - needs to honor current hierarchy.
            - recursive search through tree, update all pattern nodes?
"""

import os
import math

from PyQt5.QtWidgets import (
    qApp, QWidget,  QVBoxLayout, QHBoxLayout,
    QScrollArea, QSplitter, QPushButton, QLineEdit, QTreeWidget,
    QComboBox, QHeaderView, QAbstractItemView,
    QMenu, QTreeWidgetItem
)
from PyQt5.QtCore import (
    Qt
)

from PyQt5.QtGui import (
    QColor, QPixmap, QIcon, QStandardItemModel, QStandardItem, QCursor,
    QBrush
)


try:
    from Katana import UI4, QT4Widgets, QT4FormWidgets
    from Katana import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
    from Katana import UniqueName, FormMaster, Utils, Decorators
except ImportError:
    import UI4, QT4Widgets, QT4FormWidgets
    import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
    import UniqueName, FormMaster, Utils


from .ItemTypes import (
    MASTER_ITEM,
    PATTERN_ITEM,
    BLOCK_ITEM,
    BLOCK_PUBLISH_GROUP,
)

from .Settings import (
    PATTERN_PREFIX,
    BLOCK_PREFIX,
    GRID_COLOR,
    TEXT_COLOR,
    SPLITTER_STYLE_SHEET,
    SPLITTER_STYLE_SHEET_HIDE,
    SPLITTER_HANDLE_WIDTH,
    ACCEPT_COLOR_RGBA,
    MAYBE_COLOR_RGBA,
    ACCEPT_HOVER_COLOR_RGBA,
    MAYBE_HOVER_COLOR_RGBA,
    PUBLISH_DIR
    )

from .Utils import (
    checkBesterestVersion,
    connectInsideGroup,
    convertStringBoolToBool,
    createNodeReference,
    disconnectNode,
    goToNode,
    getNextVersion,
    mkdirRecursive,
    updateNodeName,
)

from Utils2 import (
    getMainWidget,
    makeUndoozable
)

from Widgets2 import(
    AbstractComboBox,
    AbstractFileBrowser
)

from Widgets2.AbstractSuperToolEditor import iParameter


class VariableManagerWidget(QWidget):
    """
    The main display widget for modifying the GSV stack.
    This widget will display by default and is at index 0 of
    the main layout.

    Widgets:
        variable_menu (AbstractComboBox): QCombobox that contains an
            editable list of GSVs that the user can change to.
        node_type_menu (AbstractComboBox): QCombobox that contains an
            editable list of Node Types that the user can change to.
        publish_dir (Katana Widget): str value that returns the current root
            directory for publishing.By default this is set to
                $HOME/.katana/VariableManager

            This is set in the settings file, potentially will change this to
                $HOME/.katana/<node_name>
        params_widget (QWidget): An internal parameters display window for this
            node.  If the node_type is set to a Katana node type, it will automagically
            set this to display that nodes parameters.  If it is set to Group a special
            hotkey will need to be hit to display the parameters in this window,
            by default it is Alt+W
    """
    def __init__(self, parent=None, node=None):
        super(VariableManagerWidget, self).__init__(parent)

        # main layout
        self.main_widget = getMainWidget(self)
        self.node = node
        self.initGUI()
        self.setObjectName("Variable Manager Widget")

    def __name__(self):
        return "Variable Manager Widget"

    def initGUI(self):

        QVBoxLayout(self)
        # row 1
        self.r1_widget = QWidget()
        self.r1_hbox = QHBoxLayout(self.r1_widget)

        self.variable_menu = VariableManagerGSVMenu(self)
        #self.publish_dir = self.createValueParam('publish_dir')
        # TODO Register as custom widget type

        self.publish_dir = PublishDirWidget(self)

        self.node_type_menu = VariableManagerNodeMenu(self)

        self.r1_hbox.addWidget(self.variable_menu)
        self.r1_hbox.addWidget(self.node_type_menu)

        # row 2
        self.r2_widget = QWidget()

        self.r2_hbox = QHBoxLayout(self.r2_widget)
        self.r2_hbox.addWidget(self.publish_dir)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setObjectName('main_splitter')
        self.splitter.setStyleSheet(SPLITTER_STYLE_SHEET)

        # row 2.1
        self.variable_stack = self.createVariableStack()

        # row 2.2
        self.params_widget = self.createParamsWidget()
        self.splitter.addWidget(self.variable_stack)
        self.splitter.addWidget(self.params_scroll)
        self.splitter.setSizes([200, 600])

        # setup layout
        self.layout().addWidget(self.r1_widget)
        self.layout().addWidget(self.r2_widget)
        self.layout().addWidget(self.splitter)

        self.r1_widget.setObjectName('r1 widget')
        self.r2_widget.setObjectName('r2 widget')

    def createVariableStack(self):
        """
        Creates the GSV manipulation area.  This includes the embedded
        Nodegraph, Variable Browser (Tree Widget), and eventually a text
        box for adding new GSV's.
        """
        def createVariableManagerBrowserStack():
            """
            Create variable browser widget
            """
            variable_browser_widget = QWidget()
            variable_browser_vbox = QVBoxLayout()
            variable_browser_widget.setLayout(variable_browser_vbox)

            self.variable_browser = VariableManagerBrowser(self, variable=self.parent().getVariable())

            # item creation widget
            item_create_widget = VariableManagerCreateNewItemWidget(self)
            variable_browser_vbox.addWidget(self.variable_browser)
            variable_browser_vbox.addWidget(item_create_widget)

            return variable_browser_widget

        # creates widget for the Variable Browser | Node Graph
        widget = QWidget()
        vbox = QVBoxLayout()
        widget.setLayout(vbox)

        # Create Widgets
        self.variable_splitter = QSplitter()
        self.variable_splitter.setStyleSheet(SPLITTER_STYLE_SHEET)
        self.variable_splitter.setHandleWidth(
            SPLITTER_HANDLE_WIDTH
        )

        self.variable_browser_widget = createVariableManagerBrowserStack()
        self.variable_browser_widget.setObjectName("Variable Browser Widget")
        self.nodegraph_widget = self.createNodeGraphWidget()

        # Setup Layouts
        self.variable_splitter.addWidget(self.variable_browser_widget)
        self.variable_splitter.addWidget(self.nodegraph_widget)
        vbox.addWidget(self.variable_splitter)

        return widget

    def createNodeGraphWidget(self):
        """
        Creates the internal node graph for this widget.
        This is essentially a mini nodegraph that is embedded
        inside of the parameters.
        """
        nodegraph_widget = QWidget()
        layout = QVBoxLayout(nodegraph_widget)
        tab_with_timeline = UI4.App.Tabs.CreateTab('Node Graph', None)

        self.nodegraph_tab = tab_with_timeline.getWidget()
        ngw_menu_bar = self.nodegraph_tab.getMenuBar()
        ngw_menu_bar.setParent(None)

        self.nodegraph_tab.layout().itemAt(0).widget().hide()
        layout.addWidget(self.nodegraph_tab)

        return nodegraph_widget

    def createParamsWidget(self):
        """
        Creates the widget that will display the parameters
        back to the user when a node is selected in the mini nodegraph.
        """
        params_widget = QWidget()
        params_widget.setObjectName("params widget")
        self.params_layout = QVBoxLayout()
        self.params_layout.setAlignment(Qt.AlignTop)

        params_widget.setLayout(self.params_layout)
        self.params_scroll = QScrollArea()
        self.params_scroll.setWidget(params_widget)
        self.params_scroll.setWidgetResizable(True)
        return params_widget

    def createValueParam(self, name):
        """
        Create a katana param
        """
        factory = UI4.FormMaster.KatanaFactory.ParameterWidgetFactory
        locationPolicy = UI4.FormMaster.CreateParameterPolicy(None, self.node.getParameter(name))
        w = factory.buildWidget(self, locationPolicy)
        return w

    @staticmethod
    def toggleFullView(splitter):
        """
        Toggles between the full view of either the parameters
        or the creation portion of this widget.  This is to help
        to try and provide more screen real estate to this widget
        which already does not have enough
        """
        def getSplitterIndexOfWidget(widget, splitter):
            """
            Recursive function to find the index of this widget's parent widget
            that is a child of the main splitter, and then return that widgets index
            under the main splitter.

            Args:
                widget (QWidget): Widget to set searching from, this is set
                    to the current widget under the cursor
            Returns (int):
                if returns None, then bypass everything.
            """
            if widget.parent():
                if widget.parent() == splitter:
                    return splitter.indexOf(widget)
                    return widget.parent()
                else:
                    return getSplitterIndexOfWidget(widget.parent(), splitter)
            else:
                return None

        # do checks
        pos1 = QCursor.pos()
        widget = qApp.widgetAt(pos1)
        current_index = getSplitterIndexOfWidget(widget, splitter)

        if current_index is not None:
            unused_index = math.fabs(current_index - 1)
            unused_widget = splitter.widget(unused_index)

            # Return to default view
            if unused_widget.isHidden() is True:
                unused_widget.show()
                splitter.parent().r1_widget.show()
                splitter.parent().r2_widget.show()

            # Make full screen
            elif unused_widget.isHidden() is False:
                # hide unused widget
                splitter.widget(unused_index).hide()
                splitter.parent().r1_widget.hide()
                splitter.parent().r2_widget.hide()

        # reset focus
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        resolved_pos = QCursor.pos()
        new_widget = qApp.widgetAt(resolved_pos)
        new_widget.setFocus()

    def keyPressEvent(self, event):
        if event.key() == 96:
            VariableManagerWidget.toggleFullView(self.splitter)


class VariableManagerCreateNewItemWidget(QWidget):
    """
    Lives at the bottom of the variable stack, this widget
    is in charge of creating new items for the user.  This
    could be a block or pattern depending on the selection
    chosen by the user.

    Attributes:
        node_type (ITEM_TYPE): the type of item to create
        spacing (int): how much space is between the buttons
            and the user input.
    Widgets:
        item_type_button (QPushButton): Toggles what type
            of item the user will be creating.
        item_text_field (QLineEdit): Text of the new item to
            be created.
        enter_button (QPushButton): If the user is incapable of
            understanding that you can hit enter/return to accept
            something.  This is a really big, pretty much pointless
            button.
    """

    def __init__(self, parent=None):
        super(VariableManagerCreateNewItemWidget, self).__init__(parent)
        self.spacing = 5
        self.initGUI()
        self.item_type = PATTERN_ITEM
        self.main_widget = getMainWidget(self)

    def initGUI(self):
        # create widgets
        QHBoxLayout(self)
        self.item_type_button = QPushButton()
        self.item_text_field = VariableManagerCreateNewItemTextWidget()
        self.enter_button = QPushButton(":)")

        # connect signals to buttons
        self.item_type_button.clicked.connect(self.toggleItemType)
        self.enter_button.clicked.connect(self.accepted)

        # add widgets to layout
        self.layout().addWidget(self.item_type_button)
        self.layout().addWidget(self.item_text_field)
        self.layout().addWidget(self.enter_button)

        # set up widget styles
        # remove all spacing
        self.setStyleSheet("""
            margin: 0px;
        """)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

        # set buttons as flat
        self.item_type_button.setFlat(True)
        self.enter_button.setFlat(True)

        # set stylesheets
        self.item_text_field.setStyleSheet("""
                    {style_sheet}
                    border: None;
        """.format(style_sheet=self.item_text_field.styleSheet()))

        self.item_type_button.setStyleSheet("""
            outline: None;
            border-right: {spacing}px solid rgba{grid_color};
        """.format(
            spacing=str(self.spacing),
            grid_color=GRID_COLOR
        ))

        self.enter_button.setStyleSheet("""
            outline: None;
            border-left: {spacing}px solid rgba{grid_color};
        """.format(
            spacing=str(self.spacing),
            grid_color=GRID_COLOR
        ))
    """ EVENTS """
    def toggleItemType(self):
        """
        Switches the item type that is going to be created
        between Patterns and Blocks
        """
        if self.item_type == PATTERN_ITEM:
            self.item_type = BLOCK_ITEM
        elif self.item_type == BLOCK_ITEM:
            self.item_type = PATTERN_ITEM

    def accepted(self):
        """
        Wrapper for creating new item and placing it in the undo stack
        """
        # get current item
        item = self.main_widget.getWorkingItem()
        current_text = str(self.item_text_field.text())
        # browser_widget = self.main_widget.variable_manager_widget.variable_browser
        if item:
            if current_text:
                if self.main_widget.variable:
                    item_type = self.item_type.TYPE
                    makeUndoozable(
                        self.createNewItem,
                        self.main_widget,
                        str(self.item_text_field.text()),
                        'Create New {item_type}'.format(item_type=item_type)
                    )

    def createNewItem(self):
        """
        Creates a new item based off of what type of item is
        set in the item_type_button.
        """

        # create item
        current_text = str(self.item_text_field.text())
        browser_widget = self.main_widget.variable_manager_widget.variable_browser
        browser_widget.createNewBrowserItem(self.item_type, item_text=current_text)

        # check parameters if pattern
        if self.item_type == PATTERN_ITEM:
            self.createNewPattern()

        # reset text
        self.item_text_field.setText('')

    def resizeEvent(self, event):
        height = self.height()
        self.item_type_button.setFixedWidth(height+self.spacing)
        self.enter_button.setFixedWidth(height)
        QWidget.resizeEvent(self, event)

    """ UTILS"""
    def createNewPattern(self):
        """
        Creates a new pattern item for this widget.  If that pattern
        does not exist for the current graph state variable, it will
        create the new pattern aswell
        """
        # get attributes
        variable = self.main_widget.variable
        new_variable = str(self.item_text_field.text())

        # get variables list
        variables_list_parm = NodegraphAPI.GetRootNode().getParameter(
            'variables.{variable}.options'.format(variable=variable)
        )
        variables_list = [child.getName() for child in variables_list_parm.getChildren()]
        # TODO
        # Pattern Create
        """
        TODO:
            print(variables_list)
            print(self.main_widget.getOptionsList())
    
            variables list ['i0', 'i1', 'i2', 'i3', 'i4', 'i5', 'i6', 'i7', 'i8', 'i9', 'i10', 'i11', 'i12', 'i13']
            options list ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'asdf', 'sfsfs', 'asfas', 'asfasf']
        """

        # suppress callback...
        # create new variable if doesn't exist
        if new_variable not in variables_list:
            num_children = variables_list_parm.getNumChildren()
            variables_list_parm.resizeArray(num_children + 1)
            variables_list_parm.getChildByIndex(num_children).setValue(new_variable, 0)

    def __updateItemTypeButton(self):
        """
        Updates the look for the Node Type button.  This will
        eventually change colors as well.
        """
        style_sheet = self.item_type_button.styleSheet()
        # setup pattern
        if self.item_type == PATTERN_ITEM:
            self.item_type_button.setText('P')
            color = repr(PATTERN_ITEM.COLOR)
        # set up block
        elif self.item_type == BLOCK_ITEM:
            self.item_type_button.setText('B')
            color = repr(BLOCK_ITEM.COLOR)

        # set up style sheet
        self.item_type_button.setStyleSheet("""
                {style_sheet}
                color: rgba{rgba};
            """.format(
                style_sheet=style_sheet,
                rgba=color
            )
        )

    """ PROPERTIES """
    @property
    def item_type(self):
        return self._item_type

    @item_type.setter
    def item_type(self, item_type):
        self._item_type = item_type
        self.__updateItemTypeButton()

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, spacing):
        self._spacing = spacing


class VariableManagerCreateNewItemTextWidget(QLineEdit):
    """
    Text widget for the user to type in the new name of either
    a new Pattern or Block.

    Pressing CTRL+SHIFT will toggle the creation type between
    blocks and patterns.  This will only register while the keys are
    pressed, and will revert back to the original one upon key release.
    """
    def __init__(self, parent=None):
        super(VariableManagerCreateNewItemTextWidget, self).__init__(parent)
        self.is_toggled = False

    """ EVENTS """
    def keyPressEvent(self, event):
        # toggle
        modifiers = event.modifiers()
        if modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            if self.is_toggled is False:
                self.parent().toggleItemType()
                self.is_toggled = True

        # accept event
        if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
            self.parent().accepted()

        return QLineEdit.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        # release toggle
        modifiers = event.modifiers()
        if modifiers != (Qt.ControlModifier | Qt.ShiftModifier):
            if self.is_toggled is True:
                self.parent().toggleItemType()
                self.is_toggled = False

        return QLineEdit.keyReleaseEvent(self, event)

    @property
    def is_toggled(self):
        return self._is_toggled

    @is_toggled.setter
    def is_toggled(self, is_toggled):
        self._is_toggled = is_toggled


class VariableManagerGSVMenu(AbstractComboBox):
    """
    Drop down menu with autocomplete for the user to select
    what GSV that they wish for the Variable Manager to control
    """
    def __init__(self, parent=None):
        """
        @exists: flag used to determine whether or not the popup menu for the GSV change
                            should register or not (specific to copy/paste of a node)
        """
        super(VariableManagerGSVMenu, self).__init__(parent)
        # setup attrs
        self.main_widget = getMainWidget(self)
        self.previous_text = self.main_widget.node.getVariable()

        # setup signals
        self.currentIndexChanged.connect(self.indexChanged)
        self.setCleanItemsFunction(self.__getAllVariables)

        # populate
        self.populate(self.getCleanItems())
        self.setCurrentIndexToText(self.previous_text)

    """ UTILS """
    @staticmethod
    def __getAllVariables():
        """
        Gets all of the current graph state variables available

        returns (list): list of variable names as strings
        """
        variables = NodegraphAPI.GetNode('rootNode').getParameter('variables').getChildren()
        variable_list = [x.getName() for x in variables]
        return variable_list

    def checkUserInput(self):
        """
        Checks the user input to determine if it is a valid option
        in the current model.  If it is not this will create a brand
        spanking new GSV for the user.
        """
        variables_list = self.__getAllVariables()
        variable = self.currentText()
        if variable not in variables_list:
            self.setExistsFlag(False)
            self.createNewGSV(str(self.currentText()))
            self.setExistsFlag(True)
            return

    def gsvChanged(self):
        """
        When the user changes the GSV and accepts the change,
        this function will be triggered.
        """

        # check to make sure variable exists... if not, create it
        self.checkUserInput()

        # get attributes
        variable_browser = self.main_widget.variable_manager_widget.variable_browser
        variable = str(self.currentText())
        node = self.main_widget.getNode()

        # update variables
        self.main_widget.setVariable(variable)
        node.getParameter('variable').setValue(variable, 0)

        # if node type is not set yet, then return
        if self.main_widget.variable_manager_widget.node_type_menu.currentText() == '':
            return

        # reset item selection to root
        item = variable_browser.topLevelItem(0)
        variable_browser.setCurrentItem(item)
        self.main_widget.setWorkingItem(item)
        item.setText(0, str(self.currentText()))

        # update
        checkBesterestVersion(self.main_widget)
        variable_browser.reset()
        self.main_widget.setVariable(variable)

        # TODO do I need this?
        if self.main_widget.node_type == 'Group':
            variable_browser.showMiniNodeGraph()

    def accepted(self):
        makeUndoozable(
            self.gsvChanged,
            self.main_widget,
            str(self.currentText()),
            'Change GSV'
        )

    def cancelled(self):
        self.setCurrentIndexToText(self.main_widget.getVariable())
        self.main_widget.variable_manager_widget.variable_browser.topLevelItem(0).setText(0, self.main_widget.variable)

    def createNewGSV(self, gsv):
        """
        Creates a new GSV in the project settings.

        Args:
            gsv (str) the name of the GSV to add
        """
        variables_group = NodegraphAPI.GetRootNode().getParameter('variables')
        variable_param = variables_group.createChildGroup(gsv)
        variable_param.createChildNumber('enable', 1)
        variable_param.createChildString('value', '')
        variable_param.createChildStringArray('options', 0)
        return variable_param.getName()

    """ EVENTS """
    def mousePressEvent(self, *args, **kwargs):
        self.setExistsFlag(False)
        self.update()
        self.setExistsFlag(True)
        return AbstractComboBox.mousePressEvent(self, *args, **kwargs)

    def indexChanged(self, event):
        """
        When the user changes the value in the GSV dropdown menu,
        this event is run.  It will first ask the user if they wish to proceed,
        as doing so will essentially reinstantiate this node back to an initial setting.
        """
        # pop up warning box to ask user if they wish to change the variable
        if self.getExistsFlag() is True:
            if hasattr(self.main_widget.variable_manager_widget, 'variable_browser'):
                warning_text = "Changing the GSV will delete all of your unsaved work..."
                detailed_warning_text = """
Publish your work if you want to save it, either in a file save,
or with the internal publishing mechanism on this node.  If you
continue from here, all unsaved work will be deleted...

If you choose to accept you will change the GSV:

{old_variable} ==> {new_variable}
""".format(
                    old_variable=self.main_widget.getVariable(),
                    new_variable=str(self.currentText())
                )
                self.main_widget.showWarningBox(
                    warning_text, self.accepted, self.cancelled, detailed_warning_text
                )
        # TODO do I need this?
        # elif self.getExistsFlag() is False:
        #     self.setCurrentIndexToText(self.main_widget.getVariable())


class VariableManagerNodeMenu(AbstractComboBox):
    """
    Drop down menu with autocomplete for the user to select
    what Node Type that they wish for the Variable Manager to control
    """
    def __init__(self, parent=None):
        super(VariableManagerNodeMenu, self).__init__(parent)
        self.main_widget = getMainWidget(self)
        self.previous_text = self.main_widget.node.getNodeType()

        # setup signals
        self.currentIndexChanged.connect(self.indexChanged)
        self.setCleanItemsFunction(self.__getAllNodes)

        # populate
        self.populate(self.getCleanItems())
        self.setCurrentIndexToText(self.previous_text)

    @staticmethod
    def __getAllNodes():
        return NodegraphAPI.GetNodeTypes()

    def checkUserInput(self):
        """
        Checks the user input to determine if it is a valid option
        in the current model.  If it is not this will reset the menu
        back to the previous option
        """
        does_node_variable_exist = self.isUserInputValid()
        if does_node_variable_exist is False:
            node_type = self.main_widget.node.getParameter('node_type').getValue(0)
            self.setCurrentIndexToText(node_type)
            return

    def accepted(self):
        makeUndoozable(
            self.changeNodeType,
            self.main_widget,
            str(self.currentText()),
            'Change Node Type'
        )

    def changeNodeType(self):
        """
        Changes the node type of this node.  This will update also update everything
        including node creation, and UI updates.
        """
        if hasattr(self.main_widget.variable_manager_widget, 'variable_browser'):
            # get attrs
            variable_browser = self.main_widget.variable_manager_widget.variable_browser
            node = self.main_widget.getNode()
            node_type = str(self.currentText())

            # set attrs
            node.getParameter('node_type').setValue(node_type, 0)
            self.main_widget.setNodeType(node_type)

            # check variable menu
            variable_menu = self.main_widget.variable_manager_widget.variable_menu
            if variable_menu.currentText() == '':
                return

            # update
            checkBesterestVersion(self.main_widget)
            variable_browser.reset()

    def cancelled(self):
        self.setExistsFlag(False)
        node_type = self.main_widget.node.getParameter('node_type').getValue(0)
        self.setCurrentIndexToText(node_type)

    """ EVENTS """
    def mousePressEvent(self, *args, **kwargs):
        self.setExistsFlag(False)
        self.update()
        self.setExistsFlag(True)
        return AbstractComboBox.mousePressEvent(self, *args, **kwargs)

    def indexChanged(self):
        """
        # without this it randomly allows the user to change to a
        # new node type =\
        """
        # preflight checks
        # return if this node type does not exist
        if self.currentText() not in NodegraphAPI.GetNodeTypes(): return
        # check gsv to exist...

        # pass preflight do stuff
        if self.getExistsFlag() is True:
            warning_text = "This will delete all of your unsaved work"
            detailed_warning_text = """
Publish your work if you want to save it, either in a file save,
or with the internal publishing mechanism on this node.  If you
continue from here, all unsaved work will be deleted...

{old_node_type} ==> {new_node_type}
""".format(
                    old_node_type=self.main_widget.node.getParameter('node_type').getValue(0),
                    new_node_type=str(self.currentText())
                )
            self.main_widget.showWarningBox(
                warning_text, self.accepted, self.cancelled, detailed_warning_text
            )


class VariableManagerBrowser(QTreeWidget):
    """
    Main widget containing all of the GSV's to the user.  This widget also
    has the ability to create/destroy custom groups with GSV's inside.
    This is essentially the main display widget for the user.

    Item Types
    Three types...
        Master  - lighting rig for the entire variable...
        Block   - container holding multiple variables/blocks
        Pattern    - a single pattern VariableManagerBrowserItem(
            self, name='master', item_type='master'
            )

    Attributes:
        item (VariableManagerBrowserItem): The last selected item,
            this differs from the "getCurrentItem" call, as this will essentially
            store a previously selected item to be called if needed ( I think... )
    """
    def __init__(self, parent=None, variable=''):
        super(VariableManagerBrowser, self).__init__(parent=parent)

        # setup default attrs
        self.item_list = []
        self.main_widget = getMainWidget(self)

        # set up header
        self.head = self.header()
        self.head.setSectionsClickable(True)
        self.head.sectionClicked.connect(self.__createUserBlockItemWrapper)
        self.setHeaderItem(QTreeWidgetItem([variable, 'pattern', 'block']))
        self.head.setStretchLastSection(False)
        self.head.setSectionResizeMode(0, QHeaderView.Stretch)
        for x in range(1, 3):
            self.setColumnWidth(x, 80)
            self.head.setSectionResizeMode(x, QHeaderView.Fixed)

        # setup display attrs
        self.setAlternatingRowColors(True)

        # set flags
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        root_flags = self.invisibleRootItem().flags()
        root_item = self.invisibleRootItem()
        root_item.setFlags(root_flags ^ Qt.ItemIsDropEnabled)

        # setup signals / events
        self.itemCollapsed.connect(self.itemCollapsedEvent)
        self.itemExpanded.connect(self.itemExpandedEvent)
        self.itemChanged.connect(self.itemNameChanged)
        # create all items
        self.populate()

    """ UTILS """
    @classmethod
    def getFullItemPath(cls, item, path):
        if item:
            path = '{text}/{path}'.format(text=item.text(0), path=path)
            return cls.getFullItemPath(item.parent(), path)
        return path

    def getAllRootNodes(self, item, vs_node_list=[]):
        if item:
            if item.getRootNode().getParameter('nodeReference.vs_node'):
                vs_node_list.append(item.getRootNode())
            return self.getAllRootNodes(item.parent(), vs_node_list)
        else:
            return vs_node_list

    def createMasterPublishDir(self):
        """
        Creates the directories associated with a specific item.
        This should probably accept the arg <item> instead of
        the strings...
        """
        # create null directories
        base_publish_dir = self.main_widget.getBasePublishDir(include_node_type=True)
        mkdirRecursive(base_publish_dir + '/patterns')
        mkdirRecursive(base_publish_dir + '/blocks')

        # create default master dirs
        publish_dir = base_publish_dir + '/patterns/master'
        mkdirRecursive(publish_dir + '/pattern/live')
        mkdirRecursive(publish_dir + '/block/live')

    def clear(self):
        """
        Overriding this functionality so that it won't explode in my face
        """
        for index in reversed(range(self.topLevelItemCount())):
            self.takeTopLevelItem(index)
        return

    def reset(self):
        """
        Deletes all of the top level items in.  This is essentially
        clearing the state of the browser so that it can be repopulated.
        """
        self.clear()
        variable = self.main_widget.getVariable()
        node_type = self.main_widget.getNodeType()
        node = self.main_widget.getNode()
        node._reset(variable=variable, node_type=node_type)
        self.populate()
        self.main_widget.updateOptionsList()

    def reparentItem(self, item, new_parent_item, index=0):
        """
        Reparents an item from its current parent to the provided parent.

        Args:
            item (VariableManagerBrowserItem): item to have its parent set.
            new_parent_item (VariableManagerBrowserItem): Item to be
                parented to.

        Kwargs:
            index (int): the new index of the child
        """
        old_parent_item = item.parent()
        try:
            old_parent_item.takeChild(old_parent_item.indexOfChild(item))
        except AttributeError:
            # check to see if this was a top level item drop bug...
            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)
            # if the item does not have a parent, we will duck out
            pass
        new_parent_item.insertChild(index, item)

    def populate(self):
        def populateBlock(root_item, child):
            """
            recursive statement to search through all
            nodes and create the items for those nodes
            """
            root_node = NodegraphAPI.GetNode(child.getValue(0))
            is_disabled = root_node.isBypassed()
            # create pattern item
            if root_node.getParameter('type').getValue(0) == 'pattern':
                version = root_node.getParameter('version').getValue(0)
                unique_hash = root_node.getParameter('hash').getValue(0)
                pattern = root_node.getParameter('pattern').getValue(0)

                VariableManagerBrowserItem(
                    root_item,
                    is_disabled=is_disabled,
                    root_node=root_node,
                    block_node=root_node,
                    pattern_node=root_node,
                    veg_node=root_node.getChildByIndex(0),
                    pattern_version=version,
                    unique_hash=unique_hash,
                    name=pattern,
                    item_type=PATTERN_ITEM
                )

            # create block item, and populate block
            else:
                # get attrs
                version = root_node.getParameter('version').getValue(0)
                unique_hash = root_node.getParameter('hash').getValue(0)

                # get expanded
                if root_node.getParameter('expanded'):
                    string_expanded = root_node.getParameter('expanded').getValue(0)
                    expanded = convertStringBoolToBool(string_expanded)
                else:
                    expanded = False
                pattern_node = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.pattern_node').getValue(0))
                pattern_version = pattern_node.getParameter('version').getValue(0)

                block_node = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.block_group').getValue(0))
                block_version = block_node.getParameter('version').getValue(0)

                # create block item
                block_item = VariableManagerBrowserItem(
                    root_item,
                    block_node=block_node,
                    block_version=block_version,
                    expanded=expanded,
                    item_type=BLOCK_ITEM,
                    is_disabled=is_disabled,
                    name=root_node.getParameter('name').getValue(0),
                    pattern_node=pattern_node,
                    pattern_version=pattern_version,
                    root_node=root_node,
                    unique_hash=unique_hash,
                    veg_node=pattern_node.getChildByIndex(0),
                )

                # recursively populate the block
                for child in block_node.getParameter('nodeReference').getChildren():
                    populateBlock(block_item, child)

        # get publish dir...
        variable = self.main_widget.getVariable()
        node_type = self.main_widget.getNodeType()
        """
        TODO:
            variable != ''
                repeated... because the directories need to exist to
                create the master item?  Do I need to be repeating
                this?
        """
        # do stuff if variable is empty/unassigned/initializing
        if variable != '' and node_type != '':
            # create directories
            self.createMasterPublishDir()

        # create master item
        master_item = self.createNewBrowserItem(MASTER_ITEM, variable)

        # recursively populate the items under the master group
        if variable != '':
            block_root_node = master_item.getBlockNode()
            for child in block_root_node.getParameter('nodeReference').getChildren():
                populateBlock(master_item, child)

    def __deleteItem(self, item):
        """
        Deletes an item, removes all of the node referencing,
        and rewires all of the ports.  Hopefully.

        Attributes:
            item (VariableManagerBrowserItem): Item to be deleted
        """

        """        
        Utils.UndoStack.OpenGroup(
            "Removing item {item} from {node}".format(
                item=item.text(0),
                node=item.getRootNode().getName()
            )
        )"""

        # disconnect node
        self.__unwireNode(item, item.parent())

        # delete node
        item.getRootNode().delete()

        # remove item
        child_index = item.parent().indexOfChild(item)
        item.parent().takeChild(child_index)

        #Utils.UndoStack.CloseGroup()

    def __wireNode(self, item, new_parent_item, new_index):
        """
        Reconnects the node to the new parents internal node network and
        creates the new references on the block group.

        Args:
            item (VariableManagerBrowserItem): The item that is currently
                being moved around.
            new_parent_item (VariableManagerBrowserItem): The parent item
                that has had an item moved under it.
            new_index (int): The new index of the child for the
                new parent.
        """
        node = item.getRootNode()
        # reconnect node
        node_list = []
        for index in range(new_parent_item.childCount()):
            child_item = new_parent_item.child(index)
            # need to check to make sure we don't double append the node
            if child_item.getRootNode() != node:
                node_list.append(child_item.getRootNode())
        node_list.insert(new_index, node)

        # add node reference
        self.__addNodeReference(item, new_parent_item, new_index)

        # update variable switches
        new_root_node = new_parent_item.getRootNode()
        self.main_widget.updateAllVariableSwitches(new_root_node)

        # connect children
        connectInsideGroup(node_list, new_parent_item.getBlockNode())

    def __unwireNode(self, item, old_parent_item):
        """
        Disconnects the node and removes all referencing/linking
        to its existing parent

        Args:
            item (VariableManagerBrowserItem): The item that is currently
                being moved around.
            old_parent_item (VariableManagerBrowserItem): The parent item
                that the item is being removed from
        """
        # get nodes
        node = item.getRootNode()

        # get ports
        """
        Massive duck typing hack to get around issue in the
        dropOnPattern --> __createUserBlockItem
            due to the fact that it has to create at origin every time...
            so... it will disconnect the last node... which will cause it
            to not be able to find a connect port, which will cause the
            index error in the list, which will make me pull me hair out
            trying to trace this down...
        """
        try:
            previous_port = node.getInputPortByIndex(0).getConnectedPorts()[0]
        except IndexError:
            previous_port = node.getParent().getSendPort('in')
        try:
            next_port = node.getOutputPortByIndex(0).getConnectedPorts()[0]
        except IndexError:
            next_port = node.getParent().getReturnPort('out')

        # reconnect network w/out node
        next_port.connect(previous_port)

        # disconnect input ports from node
        disconnectNode(node, input=True)
        """
        for input_port in node.getInputPorts():
            output_ports = input_port.getConnectedPorts()
            for port in output_ports:
                port.disconnect(input_port)
        """
        #remove references
        self.__removeNodeReference(item, old_parent_item)

        # update variable switch
        old_root_node = old_parent_item.getRootNode()
        self.main_widget.updateAllVariableSwitches(old_root_node)

    def __removeNodeReference(self, item, old_parent_item):
        """
        Dereferences the item from the old parent item.

        Args:
            item (VariableManagerBrowserItem): item to be unreferenced
                from the old_parent_item
            old_parent_item (VariableManagerBrowserItem): the item to have
                the reference removed from.
        """
        # update params

        # get nodes
        node = item.getRootNode()
        old_block_node = old_parent_item.getBlockNode()

        # remove reference
        for param in old_block_node.getParameter('nodeReference').getChildren():
            if param.getValue(0) == node.getName():
                old_block_node.getParameter('nodeReference').deleteChild(param)

    def __addNodeReference(self, item, new_parent_item, new_index=-1):
        """
        Adds a node reference of the item, to the new parent item

        Args:
            item (VariableManagerBrowserItem): item with the root node
                to create reference to on the parents block node.
                This can either be a block or pattern.
            new_parent_item (VariableManagerBrowserItem): item whose block
                node will have the new reference on

        Kwargs:
            new_index (int): the index of the item
        """
        node = item.getRootNode()
        # update node reference
        # get param

        node_ref_param = new_parent_item.getBlockNode().getParameter('nodeReference')
        if item.getItemType() == PATTERN_ITEM:
            prefix = PATTERN_PREFIX
            name = item.getPatternNode().getParameter('pattern').getValue(0)
        elif item.getItemType() == BLOCK_ITEM:
            prefix = BLOCK_PREFIX
            name = item.getBlockNode().getParameter('name').getValue(0)
        param_name = '{prefix}{name}'.format(prefix=prefix, name=name)

        createNodeReference(
            node, param_name, param=node_ref_param, index=new_index
        )

    """ PUBLISH """
    def publishBlock(self, name=None):
        """
        Pops up the display
        """
        self.main_widget.publish_display_widget.update(
            name=name, publish_type=BLOCK_ITEM
        )
        self.main_widget.publish_display_widget.display()

    def publishPattern(self, name=None):
        self.main_widget.publish_display_widget.update(
            name=name, publish_type=PATTERN_ITEM
        )
        self.main_widget.publish_display_widget.display()

    """ CREATE NEW ITEM """
    def __setupNodes(self, node, parent_node, current_pos):
        """
        connects the nodes, and sets their position

        Args:
            node (node): Current node that is being created
            parent_node (node): The current nodes parent
            current_pos (QPoint): the current position of the last node
        """
        # get previous port
        if len(parent_node.getChildren()) == 0:
            previous_port = parent_node.getSendPort('in')
        else:
            previous_port = parent_node.getChildByIndex(len(parent_node.getChildren()) - 2).getOutputPortByIndex(0)

        # connect node
        previous_port.connect(node.getInputPortByIndex(0))
        node.getOutputPortByIndex(0).connect(parent_node.getReturnPort('out'))

        # position node
        new_pos = (current_pos[0], current_pos[1] - 100)
        NodegraphAPI.SetNodePosition(node, new_pos)

    def __getNewItemSetupAttributes(self):
        """
        Gets the attributes necessary for creating the creating the new
        nodes and VariableManagerBrowserItems.

        Returns:
            parent_node (node): the parent node to create this new group under
            parent_item (VariableManagerBrowserItem): The parent item
                to create the new VariableManagerBrowserItem under.
            current_pos (QPoint): The current position of the last node in this
                location.  If there are no nodes, this will return (0, 0).
        """
        node = self.main_widget.getNode()

        # Get Parent Node / Parent Item
        current_item = self.currentItem()
        if not current_item:
            current_item = self.topLevelItem(0)

        if not current_item:
            return None, None, None

        if current_item.getItemType() == PATTERN_ITEM:
            parent_item = current_item.parent()
            if current_item.parent():
                parent_node = NodegraphAPI.GetNode(current_item.parent().getRootNode().getParameter('nodeReference.block_group').getValue(0))
            else:
                parent_node = NodegraphAPI.GetNode(node.getParameter('block_node').getValue(0))

        # Block / Master
        elif current_item.getItemType() in [MASTER_ITEM, BLOCK_ITEM]:
            parent_node = NodegraphAPI.GetNode(current_item.getRootNode().getParameter('nodeReference.block_group').getValue(0))
            parent_item = current_item

        # Get last nodes position
        if parent_item.childCount() > 0:
            last_node = parent_item.child(parent_item.childCount() - 1).getRootNode()
            current_pos = NodegraphAPI.GetNodePosition(last_node)
        else:
            # do something if 0
            current_pos = (0, 0)

        # return stuff
        return parent_node, parent_item, current_pos

    def __createNewMasterItem(self):
        """
        Creates the root item.  If there is no variable,
        this will still create the root item, and set it to hidden.
        """
        # set up master item
        # get nodes
        node = self.main_widget.getNode()
        variable = self.main_widget.getVariable()
        master_root_node = NodegraphAPI.GetNode(node.getParameter('variable_root_node').getValue(0))
        pattern_root_node = NodegraphAPI.GetNode(master_root_node.getParameter('nodeReference.pattern_node').getValue(0))
        block_root_node = NodegraphAPI.GetNode(master_root_node.getParameter('nodeReference.block_group').getValue(0))

        # wire nodes
        pattern_root_node.getOutputPortByIndex(0).connect(block_root_node.getInputPortByIndex(0))
        block_root_node.getOutputPortByIndex(0).connect(master_root_node.getReturnPort('out'))

        # get versions
        pattern_version = pattern_root_node.getParameter('version').getValue(0)
        block_version = block_root_node.getParameter('version').getValue(0)

        # setup master item
        master_item = VariableManagerBrowserItem(
            self,
            is_disabled=master_root_node.isBypassed(),
            root_node=master_root_node,
            block_node=block_root_node,
            pattern_node=pattern_root_node,
            veg_node=pattern_root_node.getChildByIndex(0),
            unique_hash='master',
            pattern_version=pattern_version,
            block_version=block_version,
            name=variable,
            item_type=MASTER_ITEM,
            expanded=True
        )

        # setup master item attrs
        if variable == '':
            master_item.setHidden(True)
        self.main_widget.setWorkingItem(master_item)
        self.setCurrentItem(master_item)
        master_item.setSelected(True)

        return master_item

    def __createNewBlockItem(self, item_text='New_Block'):
        """
        Creates a new block item, which is a container for
        holding patterns in a GSV.

        This is called by the createNewBrowserItem method
        Args:
                item_text (str): The name of the new block
        return (VariableManagerBrowserItem)
        """
        # gather variables for item creation
        node = self.main_widget.getNode()
        parent_node, parent_item, current_pos = self.__getNewItemSetupAttributes()

        # create node group
        block_root_node = node.createBlockRootNode(parent_node, name=item_text)
        block_node_name = block_root_node.getParameter('name').getValue(0)
        block_node_hash = block_root_node.getParameter('hash').getValue(0)
        # connect and align nodes
        self.__setupNodes(block_root_node, parent_node, current_pos)

        # Get Nodes
        new_block_node = NodegraphAPI.GetNode(block_root_node.getParameter('nodeReference.block_group').getValue(0))
        pattern_node = NodegraphAPI.GetNode(block_root_node.getParameter('nodeReference.pattern_node').getValue(0))

        # Create Item
        block_item = VariableManagerBrowserItem(
            parent_item,
            block_node=new_block_node,
            block_version='v000',
            pattern_version='v000',
            expanded=False,
            item_type=BLOCK_ITEM,
            name=block_node_name,
            pattern_node=pattern_node,
            veg_node=pattern_node.getChildByIndex(0),
            root_node=block_root_node,
            unique_hash=block_node_hash
        )

        return block_item

    def __createNewPatternItem(self, item_text):
        """
        Args:
            pattern (str): the GSV pattern to be used
        """
        node = self.main_widget.getNode()
        parent_node, parent_item, current_pos = self.__getNewItemSetupAttributes()
        # create node group
        pattern_node = node.createPatternGroupNode(parent_node, pattern=item_text)

        # connect and align nodes
        self.__setupNodes(pattern_node, parent_node, current_pos)

        # Get Parameters
        version = pattern_node.getParameter('version').getValue(0)
        unique_hash = pattern_node.getParameter('hash').getValue(0)
        pattern = pattern_node.getParameter('pattern').getValue(0)

        # Create Item
        item = VariableManagerBrowserItem(
            parent_item,
            item_type=PATTERN_ITEM,
            name=pattern,
            pattern_node=pattern_node,
            veg_node=pattern_node.getChildByIndex(0),
            pattern_version=version,
            root_node=pattern_node,
            unique_hash=unique_hash
        )
        # create variable switch connections
        current_root_node = item.parent().getRootNode()
        new_pattern = PATTERN_PREFIX+pattern
        self.main_widget.updateAllVariableSwitches(current_root_node, new_pattern=new_pattern)

        return item

    def createNewBrowserItem(self, item_type=BLOCK_ITEM, item_text=None):
        """
        Creates a new Variable Browser item, at the currently selected item.
        If no item is selected, it will create the new item under the master item.

        Kwargs:
            item_type (str): what type of item to create, acceptable values are
                master | block | pattern
            item_text (str): the display text of the item...
                this is only used by pattern atm... but I should really clean this up...
        Returns (VariableManagerBrowserItem):
            The newly created item.

        """
        if item_type == BLOCK_ITEM:
            return self.__createNewBlockItem(item_text=item_text)

        elif item_type == PATTERN_ITEM:
            return self.__createNewPatternItem(item_text)

        elif item_type == MASTER_ITEM:
            return self.__createNewMasterItem()

    """ DISABLE ITEM"""
    def __toggleItemDisabledState(self):
        item = self.main_widget.getWorkingItem()
        item.toggleDisabledState()
        pass

    """ PROPERTIES """
    def setItem(self, item):
        self.item = item

    def getItem(self):
        return self.item

    """ DROP EVENTS """
    def __moveItem(self, item, new_index, new_parent_item, old_parent_item):
        """
        Moves all of the nodes for an item to a new location in the hierarchy.
        This will also reset all of the node expressions for linking.

        Args:
            item (VariableManagerBrowserItem): The item that is currently
                being moved around.
            new_index (int): The new index of the child for the
                new parent.
            new_parent_item (VariableManagerBrowserItem): The new parent item
                that has had an item moved under it.
            old_parent_item (VariableManagerBrowserItem): The previous parent item
                that has had an item moved under it.
        """
        # get nodes
        node = item.getRootNode()
        #old_parent_node = old_parent_item.getRootNode()
        #new_parent_node = new_parent_item.getRootNode()
        new_block_node = new_parent_item.getBlockNode()

        # reset node parent
        self.__unwireNode(item, old_parent_item)
        node.setParent(new_block_node)
        self.__wireNode(item, new_parent_item, new_index)

    def __dropOnBlockWrapper(self, item_dropped, new_index, new_parent_item, old_parent_item):
        makeUndoozable(
            self.__dropOnBlockEvent,
            self.main_widget,
            item_dropped.text(0),
            'Drop Event',
            item_dropped,
            new_index,
            new_parent_item,
            old_parent_item
        )

    def __dropOnBlockEvent(self, item_dropped, new_index, new_parent_item, old_parent_item):
        """
        This is what happens when the user drops an item
        onto a block.  This will do all of the internal rewiring
        of the node that was dropped

        Args:
            item_dropped (ITEM): The item that is being dropped
            old_parent_item (VariableManagerBrowserItem): The dropped items
                old parent (BLOCK_ITEM)
            new_parent_item (VariableManagerBrowserItem): The dropped items
                new parent (BLOCK_ITEM)
            new_index (int): The current index of the item that has been dropped on
        """

        self.__moveItem(item_dropped, new_index, new_parent_item, old_parent_item)
        new_parent_item.setExpanded(True)

        if item_dropped.getItemType() == BLOCK_ITEM:
            string_expanded = item_dropped.getRootNode().getParameter('expanded').getValue(0)
            expanded = convertStringBoolToBool(string_expanded)
            item_dropped.setExpanded(expanded)

    def __dropOnPatternWrapper(self, item_dropped, item_dropped_on, new_index, new_parent_item, old_parent_item):
        makeUndoozable(
            self.__dropOnPatternEvent,
            self.main_widget,
            item_dropped.text(0),
            'Drop Event',
            item_dropped,
            item_dropped_on,
            new_index,
            new_parent_item,
            old_parent_item
        )

    def __dropOnPatternEvent(self, item_dropped, item_dropped_on, new_index, new_parent_item, old_parent_item):
        """
        This is what happens when the user drops an item
        onto a pattern.  This will do all of the internal rewiring,
        node creation, and reparenting.

        Args:
            item_dropped (ITEM): The item that is being dropped
            item_dropped_on (PATTERN_ITEM): the item that has recieved
                the drop event.
            new_parent_item (VariableManagerBrowserItem): The dropped items
                new parent (BLOCK_ITEM)
            old_parent_item (VariableManagerBrowserItem): The dropped items
                old parent (BLOCK_ITEM)
            new_index (int): The current index of the item that has been dropped on
        """
        if item_dropped.getItemType() == PATTERN_ITEM:
            # create new block and setup node hierarchy
            new_block_item_parent = item_dropped_on.parent()
            new_block_item = self.__createUserBlockItem(item=item_dropped_on)

            # move block
            self.__moveItem(new_block_item, new_index, new_block_item_parent, old_parent_item)
            self.reparentItem(new_block_item, new_block_item_parent, index=new_index)

            # move dropped node under new block item
            self.reparentItem(item_dropped, new_block_item)
            self.__moveItem(item_dropped, 0, new_block_item, old_parent_item)

            # set expanded
            new_block_item.setExpanded(True)

        elif item_dropped.getItemType() == BLOCK_ITEM:
            # move / rewire nodes
            self.__moveItem(item_dropped, new_index, new_parent_item, old_parent_item)
            self.__moveItem(item_dropped_on, 0, item_dropped, new_parent_item)

            # reparent items...
            self.reparentItem(item_dropped, new_parent_item, index=new_index)
            self.reparentItem(item_dropped_on, item_dropped, 0)

            # set expanded
            item_dropped.setExpanded(True)

        return

    def dropEvent(self, event, *args, **kwargs):
        """
        on drop of the item, it will disconnect/reconnect it and reposition
        all of the nodes inside...
        """

        # get pre resolve attrs
        drop_type = self.dropIndicatorPosition()
        DROP_ON = 0
        item_dropped = self.currentItem()
        old_parent_item = item_dropped.parent()
        item_dropped_on = self.itemAt(event.pos())
        # new_parent_item = item_dropped_on.parent()
        # Dropped on an item
        if drop_type == DROP_ON:
            # TODO: Enable pattern dropping ( method )
            # dropped on pattern
            if item_dropped_on.getItemType() == PATTERN_ITEM:
                new_parent_item = item_dropped_on.parent()
                new_index = new_parent_item.indexOfChild(item_dropped_on)
                self.__dropOnPatternWrapper(item_dropped, item_dropped_on, new_index, new_parent_item,  old_parent_item)

                return
            # dropped on block
            else:
                return_val = super(VariableManagerBrowser, self).dropEvent(event, *args, **kwargs)
                new_parent_item = item_dropped.parent()
                new_index = new_parent_item.indexOfChild(item_dropped)
                # drop on block item
                if new_parent_item == item_dropped_on:
                    self.__dropOnBlockWrapper(item_dropped, new_index, new_parent_item, old_parent_item)

        # Dropped in between items
        else:
            old_index = old_parent_item.indexOfChild(item_dropped)
            return_val = super(VariableManagerBrowser, self).dropEvent(event, *args, **kwargs)
            new_parent_item = item_dropped.parent()

        # move item
        if new_parent_item:
            new_index = new_parent_item.indexOfChild(item_dropped)
            self.__dropOnBlockWrapper(item_dropped, new_index, new_parent_item, old_parent_item)
        # fix weird magical drop spot in the tree inbetween items...
        else:
            self.reparentItem(item_dropped, old_parent_item, index=old_index)

        # return drop event
        return return_val

    """ DISPLAY PARAMETERS EVENTS """
    def displayItemParameters(self):
        self.main_widget.setWorkingItem(self.currentItem())
        if self.main_widget.getNodeType() == 'Group':
            self.showMiniNodeGraph()
            self.main_widget.populateParameters()
            # clear item parameters...
        else:
            self.hideMiniNodeGraph()
            self.showItemParameters()

    def hideMiniNodeGraph(self):
        variable_manager_widget = self.main_widget.variable_manager_widget
        variable_manager_widget.nodegraph_widget.hide()

    def showMiniNodeGraph(self):
        """
        If the Node Type is set to Group by the user.  This will enable it
        so that when a user clicks on a new item, the mini node graph
        to the left of the GSV manager will automatically go to that
        node.
        """
        try:
            if self.currentItem():
                # setup attrs

                self.main_widget.setPattern(str(self.currentItem().text(0)))
                self.main_widget.setWorkingItem(self.currentItem())

                # get attrs
                item = self.currentItem()
                node = item.getVEGNode()
                variable_manager_widget = self.main_widget.variable_manager_widget

                # show nodegraph
                nodegraph_tab = variable_manager_widget.nodegraph_tab

                # go to node
                #self.main_widget.variable_manager_widget.variable_browser
                # variable_browser = variable_manager_widget.variable_browser
                # item = variable_browser.topLevelItem(0)
                # variable_browser.setCurrentItem(item)
                # self.main_widget.setWorkingItem(item)
                goToNode(node, frame=True, nodegraph_tab=nodegraph_tab)

                # resize splitter to let user know that they can do this now...
                variable_manager_widget.variable_splitter.setHandleWidth(
                    SPLITTER_HANDLE_WIDTH
                )

                variable_manager_widget.variable_splitter.setStyleSheet(
                    SPLITTER_STYLE_SHEET
                )
                if nodegraph_tab.isVisible() is False:
                    variable_manager_widget = self.main_widget.variable_manager_widget
                    variable_manager_widget.nodegraph_widget.show()
                    variable_manager_widget.variable_splitter.moveSplitter(self.width() * 0.7, 1)

        except AttributeError:
            # On init of the node, pass because the
            # variable_manager_widget doest not exist yet
            pass

    def showItemParameters(self):
        """
        Shows the parameters of the current item if it
        is not of type Group.
        """
        if self.currentItem():
            node = self.currentItem().getVEGNode().getChildByIndex(0)
            self.main_widget.populateParameters(node_list=[node])

    """ RMB EVENTS """
    def __createUserBlockItemWrapper(self):
        """
        Wrapper function for the horribly named function
        __createUseBlockItem.
        """
        if not self.main_widget.variable:
            return
        item = self.currentItem()
        makeUndoozable(self.__createUserBlockItem, self.main_widget, 'Block', 'Create Block Item', item=item)

    def __createUserBlockItem(self, item=None):
        """
        Creates a new user block item.  This is triggered from the
        Context Menu, and header clicked.

        TODO:
            Merge this with the __createNewBlockItem method

        Kwargs:
            item (VariableManagerBrowserItem): If the item is given,
                the block item will be created at this items location, and
                the item clicked on while creating the block menu will
                be reparented underneath the new block.

        Returns (BLOCK ITEM)
        """
        # create block
        new_parent_item = self.createNewBrowserItem(
            item_type=BLOCK_ITEM, item_text="block"
        )

        # move new item under item clicked on,
        # if created on a pattern item
        if item:
            if item.getItemType() == PATTERN_ITEM:
                # get attrs
                old_parent_item = item.parent()
                index = old_parent_item.indexOfChild(item)

                # move pattern under block
                old_parent_item.takeChild(index)
                new_parent_item.addChild(item)
                self.__moveItem(item, 0, new_parent_item, old_parent_item)

                # move block to patterns old location
                new_grandparent_item = new_parent_item.parent()
                self.__moveItem(new_parent_item, index, new_grandparent_item, new_grandparent_item)

                # move VariableManagerBrowserItem
                new_index = new_grandparent_item.indexOfChild(new_parent_item)
                new_grandparent_item.takeChild(new_index)
                new_grandparent_item.insertChild(index, new_parent_item)

                # expand new group
                new_parent_item.setExpanded(True)

        return new_parent_item

    def contextMenuEvent(self, event):
        """
        popup menu created when the rmb is hit - has a sub method
        'actionPicker' which is choosing another method inside of
        this class to do an action when that particular name is chosen
        """
        def actionPicker(action):
            """
            Select what to do when a user clicks on a specific portion
            of the pop up menu
            """
            # Look at the contents of a specific node in the Node Graph
            if action.text() == 'Go To Node':
                item = self.currentItem()
                node = item.getVEGNode()
                goToNode(node, frame=True)

            # Return publish directory of item to terminal
            elif action.text() == 'Get Publish Dir':
                print(self.main_widget.getWorkingItem().getPublishDir())

            # Create new item
            elif 'Create' in action.text():
                if action.text() == 'Create Block':
                    self.__createUserBlockItemWrapper()

            # Publish item
            elif 'Publish' in action.text():
                # item = self.main_widget.getWorkingItem()
                node = self.main_widget.getNode()
                current_text = self.main_widget.working_item.text(0)
                variable = node.getParameter('variable').getValue(0)

                # determine which button was pressed..
                if action.text() == 'Publish Block':
                    # get publishing display text
                    publish_dir = self.main_widget.getItemPublishDir(include_publish_type=BLOCK_ITEM)
                    version = getNextVersion(publish_dir)
                    name = 'BLOCK  (  %s  |  %s  |  %s  )' % (variable, current_text, version)

                    # publish
                    self.publishBlock(name=name)

                elif action.text() == 'Publish Pattern':
                    # get publishing display text
                    publish_dir = self.main_widget.getItemPublishDir(include_publish_type=PATTERN_ITEM)
                    version = getNextVersion(publish_dir)
                    name = 'PATTERN  (  %s  |  %s  |  %s  )' % (variable, current_text, version)

                    # publish
                    self.publishPattern(name=name)

        # Create pop up menu
        pos = event.globalPos()
        menu = QMenu(self)
        item = self.currentItem()

        # Add actions to menu
        menu.addAction("Create Block")
        menu.addSeparator()
        menu.addAction('Go To Node')
        menu.addAction('Get Publish Dir')
        menu.addSeparator()
        menu.addAction('Publish Pattern')

        # Add items to block/master types
        if item:
            if item.getItemType() in [BLOCK_ITEM, MASTER_ITEM]:
                menu.addAction('Publish Block')

        # Show/Execute menu
        menu.popup(pos)
        action = menu.exec_(QCursor.pos())
        if action is not None:
            actionPicker(action)

    """ EVENTS """
    def dragMoveEvent(self, event, *args, **kwargs):
        """
        handlers to determine if an item is droppable or not
        """
        self.setItem(self.currentItem())
        self.dragging = True
        self.current_parent = None
        current_item_over = self.itemAt(event.pos())

        if current_item_over:
            if current_item_over.getItemType() == BLOCK_ITEM:
                self.current_parent = current_item_over
            elif current_item_over.getItemType() == PATTERN_ITEM:
                if current_item_over.parent():
                    self.current_parent = current_item_over.parent()
            elif current_item_over.getItemType() == MASTER_ITEM:
                self.current_parent = current_item_over
            else:
                self.current_parent = current_item_over

        else:
            self.current_parent = current_item_over
            return QTreeWidget.dragMoveEvent(self, event, *args, **kwargs)
        return QTreeWidget.dragMoveEvent(self, event, *args, **kwargs)

    def itemNameChanged(self, item):
        """
        Updates the node name and parameter name for BLOCK ITEMS
        when the items name is changed

        Args:
            item (VariableManagerBrowserItem): item whose name has just been changed.
        """
        if self.main_widget.suppress_updates is True: return

        if item:
            if item.getItemType() == BLOCK_ITEM:
                index = self.currentIndex()
                if index.column() == 0:
                    name = item.text(0)
                    root_node = item.getRootNode()

                    makeUndoozable(
                        updateNodeName,
                        self.main_widget,
                        item.text(0),
                        'Change Name',
                        root_node,
                        name=name
                    )

    def itemCollapsedEvent(self, item, *args, **kwargs):
        if item.getRootNode().getParameter('expanded'):
            item.getRootNode().getParameter('expanded').setValue('False', 0)

    def itemExpandedEvent(self, item, *args, **kwargs):
        if item.getRootNode().getParameter('expanded'):
            item.getRootNode().getParameter('expanded').setValue('True', 0)

    def keyPressEvent(self, event, *args, **kwargs):
        item = self.currentItem()
        if event.key() in [Qt.Key_Delete, Qt.Key_Backspace]:
            if item.getItemType() != MASTER_ITEM:
                makeUndoozable(self.__deleteItem, self.main_widget, item.text(0), 'Delete', item)

        elif event.key() == Qt.Key_D:
            makeUndoozable(
                self.__toggleItemDisabledState,
                self.main_widget,
                item.text(0),
                'Disable'
            )

        elif event.key() == 96:
            VariableManagerWidget.toggleFullView(self.main_widget.variable_manager_widget.splitter)

        return QTreeWidget.keyPressEvent(self, event, *args, **kwargs)

    def mouseReleaseEvent(self, event, *args, **kwargs):
        """
        Using this to register the mouse press event for
        the publishing event in columns 1 and 2.
        """
        item = self.itemAt(event.pos())
        if item:
            index = self.currentIndex()
            if index.column() == 0:
                pass
            elif index.column() in [1, 2]:
                # load up version dir...
                if event.button() == 1:
                    main_widget = getMainWidget(self)
                    previous_variable = main_widget.getVariable()
                    main_widget.versions_display_widget.update(
                        column=index.column(),
                        previous_variable=previous_variable,
                        gui=True
                    )

            return QTreeWidget.mouseReleaseEvent(self, event, *args, **kwargs)

    def selectionChanged(self, *args, **kwargs):
        """
        displays the current group that is editable in a mini-node graph
        """
        if hasattr(self.main_widget, 'variable_manager_widget'):
            item = self.currentItem()
            if not item:
                item = self.topLevelItem(0)
                self.setCurrentItem(item)
                self.main_widget.setWorkingItem(item)

            self.displayItemParameters()

        return QTreeWidget.selectionChanged(self, *args, **kwargs)


class VariableManagerBrowserItem(QTreeWidgetItem):
    """
    creates items for the VariableManagerBrowser TreeWidget,
    these items can be of type 'master','block','pattern'

    Kwargs:
        parent,
        name='new_item',
        block_node (node): The parent node that holds all of the block nodes.
        block_version (str): the version of the block node of this item
        is_disabled (bool): If True this item and will be disabled, if False,
            this item will be useable.
        expanded (bool): If this location is of type 'block', this will determine
            whether or nots its default state is expanded or not.
        item_type (str):  The type of item to create, acceptable values are
            pattern | block | master
        pattern_node (node): The parent node that holds all of the pattern
            nodes.  This is not the top level pattern node (VEG), but rather the group
            node.
        pattern_version (str): the current version of the pattern node of this item
        root_node (node): The parent node for this items root node to be
            parented under.  This is the node that will be published as a live group
            when a publish pattern or publish block event is triggered...
        unique_hash (str): the hash of this item.  For blocks this is a random
            16digit-ish hash, for patterns, this is the variable that they are created under.
        veg_node (VariableEnabledGroup node): This is the variable enabled group for a
            pattern.  If this is a block, it is the VEG node for that blocks pattern.

    Attributes:
        hash
        publish_dir
        item_type
        root_node
        block_node
        pattern_node
        disable (bool): If True this item and will be disabled, if False,
            this item will be useable.

    Notes:
        For Pattern Node:
            Root Node = Group node at top of pattern node
            Block Node = Group node at top of pattern node (same as root node)
            Pattern Node = VEG node
    """
    def __init__(
        self,
        parent,
        is_disabled=False,
        name='new_item',
        pattern_version='',
        block_version='',
        pattern_node=None,
        root_node=None,
        block_node=None,
        item_type=None,
        expanded=False,
        unique_hash=None,
        veg_node=None
    ):
        super(VariableManagerBrowserItem, self).__init__(parent)

        Utils.UndoStack.DisableCapture()
        self.setItemType(item_type)
        self.pattern_node = pattern_node
        self.root_node = root_node
        self.block_node = block_node
        self.setVEGNode(veg_node)
        self.block_version = block_version
        self.pattern_version = pattern_version
        self.setExpanded(expanded)
        self.hash = unique_hash

        main_widget = getMainWidget(self.treeWidget())
        root_node = main_widget.node

        variable = main_widget.getVariable()
        node_type = main_widget.getNodeType()
        root_location =main_widget.getRootPublishDir()
        #root_location = root_node.getParameter('publish_dir').getValue(0)

        if self.getItemType() == BLOCK_ITEM:
            location = '{root_location}/{variable}/{node_type}/blocks'.format(
                root_location=root_location, variable=variable, node_type=node_type
            )

        elif self.getItemType() in [MASTER_ITEM, PATTERN_ITEM]:
            location = '{root_location}/{variable}/{node_type}/patterns'.format(
                root_location=root_location, variable=variable, node_type=node_type
            )

        self.publish_dir = '%s/%s' % (location, self.hash)

        # END TO DO

        if item_type == BLOCK_ITEM:
            self.setFlags(
                self.flags()
                | Qt.ItemIsEditable
            )
        elif item_type == PATTERN_ITEM:
            self.setFlags(
                self.flags()
                | Qt.ItemIsDropEnabled
                | Qt.ItemIsDragEnabled
            )

        # update text
        self.setText(0, name)
        self.setText(1, pattern_version)
        self.setText(2, block_version)

        # set colors
        self.setColor()
        default_color = QBrush(QColor(*TEXT_COLOR))
        self.setForeground(0, default_color)

        # set initial disabled
        self.setDisabled(is_disabled)
        Utils.UndoStack.EnableCapture()

    def setDisabled(self, is_disabled):
        # get initial styles
        font = self.font(0)
        brush = self.foreground(0)

        # get new color
        if is_disabled is True:
            new_colors = [min(x*.75, 255) for x in brush.color().getRgb()]
        elif is_disabled is False:
            new_colors = TEXT_COLOR

        # update style
        font.setStrikeOut(is_disabled)
        new_brush = QBrush(QColor(*new_colors))
        self.__is_disabled = is_disabled
        self.setForeground(0, new_brush)
        self.setFont(0, font)

        # disable root node
        self.getRootNode().setBypassed(is_disabled)

    def setColor(self):
        """
        Sets the color of the individual item based off of
        what type they are
        """
        # get color
        if self.getItemType() == PATTERN_ITEM:
            color = QColor(*PATTERN_ITEM.COLOR)
        elif self.getItemType() == BLOCK_ITEM:
            color = QColor(*BLOCK_ITEM.COLOR)
        elif self.getItemType() == MASTER_ITEM:
            color = QColor(*MASTER_ITEM.COLOR)

        # set display flag
        pixmap = QPixmap(5, 50)
        pixmap.fill(color)

        icon = QIcon(pixmap)
        self.setIcon(0, icon)
        """        
        self.setForeground(0, QBrush(color))
        """

    def toggleDisabledState(self):
        self.setDisabled(not self.__is_disabled)

    """ ATTRIBUTES """
    def getItemType(self):
        return self._item_type

    def setItemType(self, item_type):
        self._item_type = item_type

    def setExpanded(self, boolean):
        """
        Args:
            boolean (bool): If True expand... if False, collapse...

        Note:
            Not even sure if this is necessary since I have handlers
            on the Tree Widget for collapsing/expanding...
        """
        if self.getItemType() in BLOCK_PUBLISH_GROUP:
            self.getRootNode().getParameter('expanded').setValue(repr(boolean), 0)
        return QTreeWidgetItem.setExpanded(self, boolean)

    def setVEGNode(self, veg_node):
        self._veg_node = veg_node

    def getVEGNode(self):
        return self._veg_node

    def getPatternNode(self):
        return self.pattern_node

    def setPatternNode(self, node):
        self.pattern_node = node

    def getBlockNode(self):
        return self.block_node

    def setBlockNode(self, node):
        self.block_node = node

    def getRootNode(self):
        return self.root_node

    def setRootNode(self, node):
        self.root_node = node

    def getHash(self):
        return self.hash

    def setHash(self, unique_hash):
        self.hash = unique_hash

    def getPublishDir(self):
        return self.publish_dir

    def setPublishDir(self, publish_dir):
        self.publish_dir = publish_dir


class PublishDirWidget(AbstractFileBrowser, iParameter):
    def __init__(self, parent=None):
        super(PublishDirWidget, self).__init__(parent)

        # register as katana param
        self.main_widget.parent().registerCustomParameter(
            self, 'publish_dir', iParameter.STRING, self.text, self.editingFinished
        )

        # set default values
        param = self.main_widget.node.getParameter(self.getLocation())
        publish_dir = PUBLISH_DIR
        if param:
            value = param.getValue(0)
            if value != '':
                publish_dir = value

        # setup signals
        self.editingFinished.connect(self.setPublishDir)

        # set default value
        self.setText(publish_dir)
        self.setPublishDir()

    def setPublishDir(self):
        if str(self.text()) == self.getValue():
            return

        makeUndoozable(
            self.setValue,
            self.main_widget,
            str(self.text()),
            'Change Publish Dir',
            str(self.text())
        )