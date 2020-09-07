import os
import math

from PyQt5.QtWidgets import (
    qApp, QWidget,  QVBoxLayout, QHBoxLayout,
    QScrollArea, QSplitter, QPushButton, QLineEdit, QTreeWidget,
    QApplication, QHeaderView, QAbstractItemView,
    QMenu, QTreeWidgetItem
)
from PyQt5.QtCore import (
    Qt
)

from PyQt5.QtGui import (
    QColor, QPixmap, QIcon, QCursor, QBrush
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
    SPLITTER_STYLE_SHEET,
    SPLITTER_STYLE_SHEET_HIDE,
    SPLITTER_HANDLE_WIDTH,
    PUBLISH_DIR
    )

from .Utils import (
    checkBesterestVersion,
    createNodeReference,
    getMainWidget,
    getNextVersion,
    goToNode,
    updateNodeName,
)

from Utils2 import (
    convertStringBoolToBool,
    disconnectNode,
    gsvutils,
    makeUndoozable,
    nodeutils,
)

from Utils2.colors import(
    ERROR_COLOR_RGBA,
    GRID_COLOR,
    TEXT_COLOR
)

from Widgets2 import(
    AbstractComboBox,
    AbstractFileBrowser,
    AbstractNodegraphWidget,
    AbstractParametersDisplayWidget
)

from Widgets2.AbstractSuperToolEditor import iParameter


class VariableManagerWidget(QWidget):
    """
    The main display widget for modifying the GSV stack.
    This widget will display by default and is at index 0 of
    the main layout.

    Widgets:
        variable_menu (VariableManagerGSVMenu): QCombobox that contains an
            editable list of GSVs that the user can change to.
        node_type_menu (VariableManagerNodeTypeMenu): QCombobox that contains an
            editable list of Node Types that the user can change to.
        publish_dir (PublishDirWidget): str value that returns the current root
            directory for publishing.By default this is set to
                $HOME/.katana/VariableManager
            This is set in the settings file, potentially will change this to
                $HOME/.katana/<node_name>
        param_scroll (QScrollArea): An internal parameters display window for this
            node.  If the node_type is set to a Katana node type, it will automagically
            set this to display that nodes parameters.  If it is set to Group a special
            hotkey will need to be hit to display the parameters in this window
                QScrollArea --> QWidget --> QVBoxLayout
        variable_browser (VariableManagerBrowser): The tree widget / organizer
            for all of the patterns inside of the specified GSV
        nodegraph_widget (AbstractNodegraphWidget):  Hidden unless node type is set
            to 'Group'.

    """
    def __init__(self, parent=None, node=None):
        super(VariableManagerWidget, self).__init__(parent)

        self.main_widget = getMainWidget(self)
        self.node = node
        self.initGUI()
        self.setObjectName("Variable Manager Widget")

    def __name__(self):
        return "Variable Manager Widget"

    """ CREATE GUI"""
    def initGUI(self):

        QVBoxLayout(self)
        # row 1
        self.r1_widget = QWidget()
        self.r1_hbox = QHBoxLayout(self.r1_widget)

        self.variable_menu = VariableManagerGSVMenu(self)
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
        #self.params_widget = self.createParamsWidget()
        self.params_widget = AbstractParametersDisplayWidget(self)
        self.splitter.addWidget(self.variable_stack)
        self.splitter.addWidget(self.params_widget)
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
        self.nodegraph_widget = AbstractNodegraphWidget(self, node=self.node)

        # Setup Layouts
        self.variable_splitter.addWidget(self.variable_browser_widget)
        self.variable_splitter.addWidget(self.nodegraph_widget)
        vbox.addWidget(self.variable_splitter)

        return widget

    # def createParamsWidget(self):
    #     """
    #     Creates the widget that will display the parameters
    #     back to the user when a node is selected in the mini nodegraph.
    #     """
    #     params_widget = QWidget()
    #     params_widget.setObjectName("params widget")
    #     self.params_layout = QVBoxLayout(params_widget)
    #     self.params_layout.setAlignment(Qt.AlignTop)
    #
    #     self.params_widget = QScrollArea()
    #     self.params_widget.setWidget(params_widget)
    #     self.params_widget.setWidgetResizable(True)
    #
    #     return params_widget

    """ EVENTS """
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
        QApplication.processEvents()
        resolved_pos = QCursor.pos()
        new_widget = qApp.widgetAt(resolved_pos)
        new_widget.setFocus()

    def keyPressEvent(self, event):
        if event.key() == 96:
            # ~ KEY... can't find this in the Qt.Key_Tilda...
            VariableManagerWidget.toggleFullView(self.splitter)


class VariableManagerCreateNewItemWidget(QWidget):
    """
    Lives at the bottom of the variable stack, this widget
    is in charge of creating new items for the user.  This
    could be a block or pattern depending on the selection
    chosen by the user.

    Attributes:
        item_type (ITEM_TYPE): the type of item to create
        spacing (int): how much space is between the buttons
            and the user input.
    Widgets:
        item_type_button (QPushButton): Toggles what type
            of item the user will be creating.
        item_text_field (VariableManagerCreateNewItemTextWidget):
            Text of the new item to be created.
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
            variable = self.main_widget.variable
            pattern = str(self.item_text_field.text())
            gsvutils.createNewPattern(pattern, variable)

        # reset text
        self.item_text_field.setText('')

    def resizeEvent(self, event):
        height = self.height()
        self.item_type_button.setFixedWidth(height+self.spacing)
        self.enter_button.setFixedWidth(height)
        QWidget.resizeEvent(self, event)

    """ UTILS"""
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

    Attributes:
        is_toggled (bool): determines if the create item type button
            has been toggled via the ctrl+shift hotkey functionality.
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
        self.setCleanItemsFunction(gsvutils.getAllVariables)

        # populate
        self.populate(self.getCleanItems())
        self.setCurrentIndexToText(self.previous_text)

    """ UTILS """
    def gsvChanged(self):
        """
        When the user changes the GSV and accepts the change,
        this function will be triggered.
        """
        # get attributes
        variable_browser = self.main_widget.variable_manager_widget.variable_browser
        variable = str(self.currentText())
        node = self.main_widget.getNode()

        # create new pattern if it doesn't exist
        gsvutils.createNewGSV(variable)

        # update variables
        self.main_widget.setVariable(variable)
        node.getParameter('variable').setValue(variable, 0)

        # if node type is not set yet, then return
        if self.main_widget.variable_manager_widget.node_type_menu.currentText() == '':
            return

        # update
        variable_browser.reset()

        # TODO do I need this?
        if self.main_widget.getNodeType() == 'Group':
            variable_browser.showMiniNodeGraph()

    def accepted(self):
        self.main_widget.layout().setCurrentIndex(0)
        makeUndoozable(
            self.gsvChanged,
            self.main_widget,
            str(self.currentText()),
            'Change GSV'
        )

    def cancelled(self):
        self.main_widget.layout().setCurrentIndex(0)
        self.setCurrentIndexToText(self.main_widget.getVariable())
        self.main_widget.variable_manager_widget.variable_browser.topLevelItem(0).setText(0, self.main_widget.variable)

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
        as doing so will essentially reinstated this node back to an initial setting.
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
        self.main_widget.layout().setCurrentIndex(0)
        makeUndoozable(
            self.changeNodeType,
            self.main_widget,
            str(self.currentText()),
            'Change Node Type'
        )

    def cancelled(self):
        self.main_widget.layout().setCurrentIndex(0)
        self.setExistsFlag(False)
        node_type = self.main_widget.node.getParameter('node_type').getValue(0)
        self.setCurrentIndexToText(node_type)

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
            variable_browser.reset()

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

        # show warning box
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
        self.head.sectionClicked.connect(self.__createNewBlockItemHeader)
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

        # create initial master item
        self.createNewBrowserItem(MASTER_ITEM, self.main_widget.getVariable(), check_besterest=False)

    def populate(self, check_besterest=True):
        """
        Creates all of the items for a specific variable.  This will create all of the
        items for the TreeWidget, aswell as any directories if needed.  If there is
        no directory, this will publish a v000 and load it.

        check_besterest (bool): Determines if this should check the besterest
            version or not.  Certain events will want to bypass the besterest
            call, especially those that have deleted node functionality.
        """
        # get publish dir...
        variable = self.main_widget.getVariable()
        node_type = self.main_widget.getNodeType()

        # create master item
        master_item = self.createNewBrowserItem(MASTER_ITEM, variable, check_besterest=False)
        # not this...
        if check_besterest is True:
            checkBesterestVersion(self.main_widget, item=master_item, item_types=[MASTER_ITEM])
            # somehow... this needs to determine if this is a new master item or not... =\
            #return

        # recursively populate the items under the master group
        block_root_node = master_item.getBlockNode()

        for child in block_root_node.getParameter('nodeReference').getChildren():
            self.populateBlock(master_item, child, check_besterest)

    def populateBlock(self, parent_item, child, check_besterest):
        """
        recursive statement to search through all
        nodes and create the items for those nodes
        Args:
            parent_item (VariableManagerBrowserItem): The parent item of
                the newly created item.
            child (Parameter): The parameter whose value will return
                the new nodes name to check.
            check_besterest (bool): Determines if this should check the besterest
                version or not.  This is really here to disable recursion when loading
                live groups.
        """
        # root node is the current item's root node being operated on
        root_node = NodegraphAPI.GetNode(child.getValue(0))
        is_disabled = root_node.isBypassed()

        # create PATTERN item
        if root_node.getParameter('type').getValue(0) == 'pattern':
            # create pattern item
            pattern = root_node.getParameter('pattern').getValue(0)
            new_item = self.createNewBrowserItem(
                item_type=PATTERN_ITEM, item_text=pattern, node=root_node, check_besterest=check_besterest, parent_item=parent_item
            )

            # set item attrs
            new_item.setDisabled(is_disabled)
            return

        # create BLOCK item, and populate block
        else:
            # get attrs
            string_expanded = root_node.getParameter('expanded').getValue(0)
            is_expanded = convertStringBoolToBool(string_expanded)

            # create block item
            item_text = root_node.getParameter('name').getValue(0)
            new_item = self.createNewBrowserItem(
                item_type=BLOCK_ITEM, item_text=item_text, node=root_node, check_besterest=check_besterest, parent_item=parent_item
            )

            # set item attrs
            # disabled
            new_item.setDisabled(is_disabled)

            # expanded
            new_item.setExpanded(is_expanded)

            # recurse through block
            block_node = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.block_group').getValue(0))
            for child in block_node.getParameter('nodeReference').getChildren():
                self.populateBlock(new_item, child, check_besterest)
                return

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

    def __reparentItem(self, item, new_parent_item, index=0):
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

    def __reparentNode(self, item, new_index, new_parent_item, old_parent_item):
        """
        Moves all of the nodes for an item to a new location in the hierarchy.
        This will also reset all of the node expressions for linking.

        Args:
            item (VariableManagerBrowserItem): The item that is currently
                being moved around.  Whose root node should be reparented
            new_index (int): The new index of the child for the
                new parent.
            new_parent_item (VariableManagerBrowserItem): The new parent item
                that has had an item moved under it.
            old_parent_item (VariableManagerBrowserItem): The previous parent item
                that has had an item moved under it.
        """
        # get nodes
        node = item.getRootNode()
        new_block_node = new_parent_item.getBlockNode()

        # reset node parent
        self.__unwireNode(item, old_parent_item)
        node.setParent(new_block_node)
        self.__wireNode(item, new_parent_item, new_index)

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
        nodeutils.connectInsideGroup(node_list, new_parent_item.getBlockNode())

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
    def __publish(self, name='', item_type=PATTERN_ITEM):
        """
        Context menu event for displaying a user publish
        """
        self.main_widget.publish_display_widget.update(
            name=name, publish_type=item_type
        )
        self.main_widget.publish_display_widget.display()

    """ CREATE NEW ITEM """
    def __getParentNode(self):
        """
        Gets the the current items parent node.  The parent node
        is the block_node of the selection, or its parent, depending
        on whether or not a pattern/block type is currently chosen

        Returns:
            parent_node (node): the parent node to create this new group under

        """
        node = self.main_widget.getNode()

        # Get Parent Node / Parent Item
        current_item = self.currentItem()
        if not current_item:
            current_item = self.topLevelItem(0)
        if not current_item:
            return None

        if current_item.getItemType() == PATTERN_ITEM:
            if current_item.parent():
                parent_node = NodegraphAPI.GetNode(current_item.parent().getRootNode().getParameter('nodeReference.block_group').getValue(0))
            else:
                parent_node = NodegraphAPI.GetNode(node.getParameter('block_node').getValue(0))

        # Block / Master
        elif current_item.getItemType() in [MASTER_ITEM, BLOCK_ITEM]:
            parent_node = NodegraphAPI.GetNode(current_item.getRootNode().getParameter('nodeReference.block_group').getValue(0))

        return parent_node

    def __getPublishDir(self, item_type, unique_hash):
        """
        Gets the full publish dir for an item that is being created
        """

        variable = self.main_widget.getVariable()
        node_type = self.main_widget.getNodeType()
        root_location = self.main_widget.getRootPublishDir()

        if item_type in [MASTER_ITEM, BLOCK_ITEM]:
            publish_dir = '{root_location}/{variable}/{node_type}/block/{unique_hash}'.format(
                root_location=root_location, variable=variable, node_type=node_type, unique_hash=unique_hash
            )

        elif item_type in [PATTERN_ITEM]:
            publish_dir = '{root_location}/{variable}/{node_type}/pattern/{unique_hash}'.format(
                root_location=root_location, variable=variable, node_type=node_type, unique_hash=unique_hash
            )

        return publish_dir

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

        # get publish dir
        publish_dir = self.__getPublishDir(MASTER_ITEM, 'master')

        # setup master item
        master_item = VariableManagerBrowserItem(
            self.invisibleRootItem(),
            is_disabled=master_root_node.isBypassed(),
            root_node=master_root_node,
            block_node=block_root_node,
            pattern_node=pattern_root_node,
            veg_node=pattern_root_node.getChildByIndex(0),
            unique_hash='master',
            pattern_version=pattern_version,
            publish_dir=publish_dir,
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

    def __createNewBlockItem(self, item_text='New_Block', block_root_node=None, parent_item=None):
        """
        Creates a new block item, which is a container for
        holding patterns in a GSV.  If no block root node is provided, this will
        create a new block root node.

        This is called by the createNewBrowserItem method
        Args:
                item_text (str): The name of the new block
                block_root_node (Block Root Node): The new block node... if this
                    is provided, it will be used as the block root node, rather than
                    creating a new one.
                check_besterest (bool): Determines if this should check the besterest
                    version or not.  This is really here to disable recursion when loading
                    live groups.
        return (VariableManagerBrowserItem)
        """
        # gather variables for item creation
        node = self.main_widget.getNode()
        parent_node = self.__getParentNode()

        # create node group
        if not block_root_node:
            block_root_node = node.createBlockRootNode(parent_node, name=item_text)
            # connect and align nodes
            nodeutils.insertNode(block_root_node, parent_node)

        block_node_name = block_root_node.getParameter('name').getValue(0)
        block_node_hash = block_root_node.getParameter('hash').getValue(0)
        # connect and align nodes

        # Get Nodes
        new_block_node = NodegraphAPI.GetNode(block_root_node.getParameter('nodeReference.block_group').getValue(0))
        pattern_node = NodegraphAPI.GetNode(block_root_node.getParameter('nodeReference.pattern_node').getValue(0))

        # get publish dir
        publish_dir = self.__getPublishDir(BLOCK_ITEM, block_node_hash)
        # Create Item
        block_item = VariableManagerBrowserItem(
            parent_item,
            block_node=new_block_node,
            block_version='v000',
            pattern_version='v000',
            expanded=False,
            item_type=BLOCK_ITEM,
            publish_dir=publish_dir,
            name=block_node_name,
            pattern_node=pattern_node,
            veg_node=pattern_node.getChildByIndex(0),
            root_node=block_root_node,
            unique_hash=block_node_hash
        )

        return block_item

    def __createNewBlockItemHeader(self):
        """
        When the header is pressed, this will create a new block item.  I'm not
        to sure if I even want to keep this functionality...
        """
        # preflight
        if self.main_widget.getVariable() == '': return
        if self.main_widget.getNodeType() == '': return

        self.__createUserBlockItemWrapper()

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
                self.__reparentNode(item, 0, new_parent_item, old_parent_item)

                # move block to patterns old location
                new_grandparent_item = new_parent_item.parent()
                self.__reparentNode(new_parent_item, index, new_grandparent_item, new_grandparent_item)

                # move VariableManagerBrowserItem
                new_index = new_grandparent_item.indexOfChild(new_parent_item)
                new_grandparent_item.takeChild(new_index)
                new_grandparent_item.insertChild(index, new_parent_item)

                # expand new group
                new_parent_item.setExpanded(True)

        return new_parent_item

    def __createNewPatternItem(self, item_text, pattern_node=None, parent_item=None):
        """
        Creates a new pattern item, which is a container for
        holding patterns in a GSV.  If no pattern node is provided, this will
        create a new block root node.

        This is called by the createNewBrowserItem method
        Args:
                item_text (str): The name of the new block
                pattern_node (Pattern Node): The new block node... if this
                    is provided, it will be used as the block root node, rather than
                    creating a new one.
                check_besterest (bool): Determines if this should check the besterest
                    version or not.  This is really here to disable recursion when loading
                    live groups.
        return (VariableManagerBrowserItem)
        TODO
            Consider merging with __createNewBlockItem
        """
        node = self.main_widget.getNode()
        parent_node = self.__getParentNode()

        # create node group
        if not pattern_node:
            pattern_node = node.createPatternGroupNode(parent_node, pattern=item_text)
            # connect and align nodes
            nodeutils.insertNode(pattern_node, parent_node)

        # Get Parameters
        version = pattern_node.getParameter('version').getValue(0)
        unique_hash = pattern_node.getParameter('hash').getValue(0)
        pattern = pattern_node.getParameter('pattern').getValue(0)

        # get publish dir
        publish_dir = self.__getPublishDir(PATTERN_ITEM, unique_hash)

        # Create Item
        item = VariableManagerBrowserItem(
            parent_item,
            item_type=PATTERN_ITEM,
            name=pattern,
            pattern_node=pattern_node,
            veg_node=pattern_node.getChildByIndex(0),
            publish_dir=publish_dir,
            pattern_version=version,
            root_node=pattern_node,
            unique_hash=unique_hash
        )

        # create variable switch connections
        current_root_node = item.parent().getRootNode()
        new_pattern = PATTERN_PREFIX+pattern
        self.main_widget.updateAllVariableSwitches(current_root_node, new_pattern=new_pattern)

        return item

    def createNewBrowserItem(self, item_type=BLOCK_ITEM, item_text=None, node=None, check_besterest=True, parent_item=None):
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
        # handle non existent scenerio
        if not parent_item:
            parent_item = self.main_widget.getWorkingItem()

        # handle pattern scenario
        if item_type != MASTER_ITEM:
            if parent_item:
                if parent_item.getItemType() == PATTERN_ITEM:
                    parent_item = parent_item.parent()

        # create items
        if item_type == BLOCK_ITEM:
            new_item = self.__createNewBlockItem(item_text=item_text, block_root_node=node, parent_item=parent_item)

        elif item_type == PATTERN_ITEM:
            new_item = self.__createNewPatternItem(item_text, pattern_node=node, parent_item=parent_item)

        elif item_type == MASTER_ITEM:
            new_item = self.__createNewMasterItem()

        # This
        #self.setCurrentItem(new_item)
        self.main_widget.setWorkingItem(new_item)

        # check to see if item should be published or not
        if check_besterest is True:
            checkBesterestVersion(self.main_widget, item=new_item, item_types=[item_type])

        return new_item

    """ DISABLE ITEM"""
    def __toggleItemDisabledState(self):
        item = self.main_widget.getWorkingItem()
        item.toggleDisabledState()

    """ PROPERTIES """
    def setItem(self, item):
        self.item = item

    def getItem(self):
        return self.item

    """ DROP EVENTS """
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
        self.__reparentNode(item_dropped, new_index, new_parent_item, old_parent_item)
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
            self.__reparentNode(new_block_item, new_index, new_block_item_parent, old_parent_item)
            self.__reparentItem(new_block_item, new_block_item_parent, index=new_index)

            # move dropped node under new block item
            self.__reparentItem(item_dropped, new_block_item)
            self.__reparentNode(item_dropped, 0, new_block_item, old_parent_item)

            # set expanded
            new_block_item.setExpanded(True)

        elif item_dropped.getItemType() == BLOCK_ITEM:
            # move / rewire nodes
            self.__reparentNode(item_dropped, new_index, new_parent_item, old_parent_item)
            self.__reparentNode(item_dropped_on, 0, item_dropped, new_parent_item)

            # reparent items...
            self.__reparentItem(item_dropped, new_parent_item, index=new_index)
            self.__reparentItem(item_dropped_on, item_dropped, 0)

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

        # Dropped on an item
        if drop_type == DROP_ON:
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
                self.__reparentItem(item_dropped, old_parent_item, index=old_index)

        # return drop event
        return return_val

    """ DISPLAY PARAMETERS EVENTS """
    def showItemParameters(self):
        """
        Shows the parameters of the current item if it
        is not of type Group.
        """
        if self.currentItem():
            node = self.currentItem().getVEGNode().getChildByIndex(0)
            self.main_widget.populateParameters(node_list=[node])

    def displayItemParameters(self):
        """
        Shows the currently selected items parameters.  Unless the node type
        is set to "Group" then it will display the mini node graph, which will
        allow selecting of nodes to display the parameters to the user.
        """
        self.main_widget.setWorkingItem(self.currentItem())
        if self.main_widget.getNodeType() == 'Group':
            self.showMiniNodeGraph()
            node_list = NodegraphAPI.GetAllSelectedNodes()
            self.main_widget.populateParameters(node_list)
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
                nodegraph_widget = variable_manager_widget.nodegraph_widget
                nodegraph_panel = nodegraph_widget.getPanel()

                # go to node
                goToNode(node, frame=True, nodegraph_panel=nodegraph_panel)

                # resize splitter to let user know that they can do this now...
                variable_manager_widget.variable_splitter.setHandleWidth(
                    SPLITTER_HANDLE_WIDTH
                )

                variable_manager_widget.variable_splitter.setStyleSheet(
                    SPLITTER_STYLE_SHEET
                )
                if nodegraph_widget.isVisible() is False:
                    variable_manager_widget = self.main_widget.variable_manager_widget
                    variable_manager_widget.nodegraph_widget.show()
                    variable_manager_widget.variable_splitter.moveSplitter(self.width() * 0.7, 1)

        except AttributeError:
            # On init of the node, pass because the
            # variable_manager_widget doest not exist yet
            pass

    """ RMB EVENTS """
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
                    item_type = BLOCK_ITEM
                    publish_dir = self.main_widget.getItemPublishDir(include_publish_type=item_type)
                    version = getNextVersion(publish_dir)
                    name = 'BLOCK  (  %s  |  %s  |  %s  )' % (variable, current_text, version)

                    # publish
                    self.__publish(name=name, item_type=item_type)

                elif action.text() == 'Publish Pattern':
                    # get publishing display text
                    item_type = PATTERN_ITEM
                    publish_dir = self.main_widget.getItemPublishDir(include_publish_type=item_type)
                    version = getNextVersion(publish_dir)

                    name = 'PATTERN  (  %s  |  %s  |  %s  )' % (variable, current_text, version)

                    # publish
                    self.__publish(name=name, item_type=item_type)

        # Create pop up menu
        pos = event.globalPos()
        menu = QMenu(self)
        item = self.currentItem()

        if item.getIsBroken(): return

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
                        name,
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
            # ~ Tilda pressed
            VariableManagerWidget.toggleFullView(self.main_widget.variable_manager_widget.splitter)

        return QTreeWidget.keyPressEvent(self, event, *args, **kwargs)

    def mouseReleaseEvent(self, event, *args, **kwargs):
        """
        Using this to register the mouse press event for
        the publishing event in columns 1 and 2.
        """
        item = self.itemAt(event.pos())
        if item:
            if item.getIsBroken(): return

            index = self.currentIndex()
            if index.column() == 0:
                pass
            elif index.column() in [1, 2]:
                # load up version dir...
                if event.button() == 1:
                    previous_variable = self.main_widget.getVariable()
                    self.main_widget.setWorkingItem(item)
                    self.main_widget.versions_display_widget.update(
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
        publish_dir=None,
        unique_hash=None,
        veg_node=None
    ):
        super(VariableManagerBrowserItem, self).__init__(parent)

        Utils.UndoStack.DisableCapture()

        # setup default attrs
        self.setItemType(item_type)
        self.pattern_node = pattern_node
        self.root_node = root_node
        self.block_node = block_node
        self.setVEGNode(veg_node)
        self.block_version = block_version
        self.pattern_version = pattern_version
        self.setExpanded(expanded)
        self.hash = unique_hash
        self.publish_dir = publish_dir

        # setup flags
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

        # setup display
        # update text
        self.setText(0, name)
        self.setText(1, pattern_version)
        self.setText(2, block_version)

        # update colors
        self.checkValidity(update=False)
        self.setDisabled(is_disabled, update=False)
        self.updateColors()

        Utils.UndoStack.EnableCapture()

    def checkValidity(self, update=True):
        """
        Checks to determine if the item is broken or not based off of if
        the directories exist or not.  This will set the _is_broken attr via setIsBroken
        to determine if the item is broken or not.

        Args:
            update (bool): if true the colors will be updated.
        """
        # get attrs
        publish_dir = self.publish_dir
        pattern_version = self.pattern_version
        block_version = self.block_version
        item_type = self.getItemType()

        # setup is broken
        self.setIsBroken(False)
        if not os.path.exists('{publish_dir}/pattern/{version}/something.livegroup'.format(
                publish_dir=publish_dir, version=pattern_version
        )):
            self.setIsBroken(True)
        if item_type in [BLOCK_ITEM, MASTER_ITEM]:
            if not os.path.exists('{publish_dir}/block/{version}/something.livegroup'.format(
                publish_dir=publish_dir, version=block_version
            )):
                self.setIsBroken(True)
        if update is True:
            self.updateColors()

    """ COLORS """
    def updateColors(self):
        """
        Updates all of the colors for the item including the
            icon, text
        """
        self.setIconColor()
        self.setTextColor()

    def setIconColor(self):
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

    def setTextColor(self):
        """
        sets the text's color based on the specific arguments set to it
        such as enable/disable and errors
        """
        # Set text color
        brush = self.foreground(0)

        # get color
        if self.isDisabled() is True:
            new_colors = [min(x*.75, 255) for x in brush.color().getRgb()]
        elif self.isDisabled() is False:
            new_colors = TEXT_COLOR
        elif self.getIsBroken() is True:
            new_colors = ERROR_COLOR_RGBA

        new_brush = QBrush(QColor(*new_colors))
        self.setForeground(0, new_brush)

    """ DISPLAY ATTRS"""
    def isDisabled(self):
        return self._is_disabled

    def setDisabled(self, is_disabled, update=True):
        """
        Sets the flag for if this item is disabled or not.

        Args:
            is_disabled (bool): flag to determine if this item is disabled.
            update (bool): if true the colors will be updated.
        """
        # setter
        self._is_disabled = is_disabled

        # strike out font
        font = self.font(0)
        font.setStrikeOut(is_disabled)
        self.setFont(0, font)

        # update color
        if update is True:
            self.updateColors()

        # disable root node
        self.getRootNode().setBypassed(is_disabled)

        return is_disabled

    def toggleDisabledState(self):
        self.setDisabled(not self._is_disabled)

    def getIsBroken(self):
        return self._is_broken

    def setIsBroken(self, bool):
        self._is_broken = bool

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
    """
    Custom parameter widget type thing.  This will be the File Path browser
    widget for the user to change their publish directory with.
    """
    def __init__(self, parent=None):
        super(PublishDirWidget, self).__init__(parent)
        self.main_widget = getMainWidget(self)

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
        self.editingFinished.connect(self.directoryChanged)

        # set default value
        self.main_widget.setRootPublishDir(publish_dir)
        self.setText(publish_dir)
        self.setValue(publish_dir)

    def directoryChanged(self):
        """
        If publish_dir parameter is changed, this will ask the user if they
        are sure they'd like to continue if the user decides to continue,
        it will create all of the new directories, but will NOT move over
        the current publishes

        Args:
            new_publish_dir (str): The path on disk to the new publish dir
        TODO:
            change return values from ints to keywords
        """
        def accept():
            self.main_widget.setRootPublishDir(str(self.text()))
            self.setValue(str(self.text()))

        # check to make sure its not reset
        if str(self.text()) == self.getValue():
            return

        # if no variable set, create the root dir
        if (
                self.main_widget.getVariable() == ''
                or self.main_widget.getNodeType() == ''
        ):

            makeUndoozable(
                accept,
                self.main_widget,
                str(self.text()),
                "Publish Directory"
            )
            return

        # ask user to confirm directory change...
        if not os.path.exists(str(self.text())):
            warning_text = 'Do you wish to create new directories?'
            detailed_warning_text = """
    Accepting this event will create a bunch of new crap on your file system,
    but you need this crap in order to save stuff into it.
                """

            self.main_widget.showWarningBox(
                warning_text,
                self.__acceptDirectoryChange,
                self.__cancelDirectoryChange,
                detailed_warning_text
            )
        else:
            """
            check if the dir has actually changed or if it was a
            cancellation of a dir changed to avoid recursion

            I have no idea how this works anymore and I'm to lazy
            to look at it and figure it out...
            """
            # cancel recursion
            # the "real version"
            if self.main_widget.getRootPublishDir() == str(self.text()):
                return
            self.__acceptDirectoryChange()

    def __acceptDirectoryChange(self):
        def accept():
            self.main_widget.setRootPublishDir(str(self.text()))
            self.setValue(str(self.text()))
            checkBesterestVersion(self.main_widget)

        makeUndoozable(
            accept,
            self.main_widget,
            str(self.text()),
            "Publish Directory"
        )

    def __cancelDirectoryChange(self):
        root_publish_dir = self.main_widget.getRootPublishDir()
        self.setUpdatesEnabled(False)
        self.setText(root_publish_dir)
        self.setUpdatesEnabled(True)