"""
TODO
    Publish
        *   change publish dir to
                $ROOT_DIR / GSV / <node type>
        *   publish root
                combined pattern + block
    Versions
        *   Create simple display of menu, vs the advanced
                display with notes.
    Cleanup
        *    checkHash repeats...
        *    gsv change
                -- load live version of
                        pattern
                        block
        * directory publish
            VariableManagerBrowserItem --> createPublishDir
            VariableManagerMainWidget --> changeDirectory
    WISH LIST:
        1.) Import/Export?
        2.) Drag/Drop
            Drop into Widget:
                if its the same node type, copy parameters into the correct pattern
            Drag out of widget, drop in Nodegraph
                Create duplicate of w/e of drag/dropped
        3.) Expose for pipeline
        4.) Filterable versions in advanced menu
- bugs...
    *  Node Type change
            This needs to be linked to publishing system...
- bad
    *    adding GSV's when auto created...
            this is probably bad... will need some sort of function to ask to add to all or not?
                addGSVPattern

- maybe
    *    publish to node name?
            ie $HOME/.katana/<node name>
    *    Align top for display/publish widgets
    *    Hotkey return to last nodegraph display location?

FEATURES:
    *   Enable / Disable
    *    Delete GSV / Block
            a.) Drag / Drop in/out of Tree Widget.
                - If exists tree widget and direction is horizontal-ish.. or not vertical
                    then delete the location
            b.) Delete key
    *    Import into nodegraph
            a.) Drag / Drop into Nodegraph
                - reparents the node(s) to that node graph, and removes them
                    from the variable manager stack...

# ===============================================================================
# OLD NOTES
# ===============================================================================
BUG

Node Type Change
    Don't repopulate the variableBrowser... just change node type...
        will need to repopulate the meta data though

Should a Block also save/load the pattern for that location?
    - It would load an entire container... rather than a user having
        to load 2 containers...


SuperTool --> group (shot/variable)
            --> block --> group (pattern/shot) [shot] --> block/shots --> LG --> Nodes
PATTERN    :    LG --> VEG --> NODES
BLOCK        :    LG --> ROOT NODES
MASTER: Top most group


BUGS:
    1.) cant name pattern 'block__' or block 'pattern__' will break... due to string search



"""

import os
import math

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QSplitter, QPlainTextEdit,
    QTreeWidget, QHeaderView, QAbstractItemView, QLineEdit,
    QSizePolicy, QMenu, QTreeWidgetItem, QStackedLayout,
    QSpacerItem
)
from PyQt5 import QtCore, QtGui

try:
    from Katana import UI4, QT4Widgets, QT4FormWidgets
    from Katana import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
    from Katana import UniqueName, FormMaster, Utils
except ImportError:
    import UI4, QT4Widgets, QT4FormWidgets
    import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
    import UniqueName, FormMaster, Utils

from ItemTypes import (
    MASTER_ITEM,
    PATTERN_ITEM,
    BLOCK_ITEM,
    BLOCK_PUBLISH_GROUP,
)
from Settings import (
    PATTERN_PREFIX,
    BLOCK_PREFIX,
    GRID_COLOR,
    SPLITTER_STYLE_SHEET,
    SPLITTER_STYLE_SHEET_HIDE,
    SPLITTER_HANDLE_WIDTH,
    ACCEPT_COLOR_RGBA,
    MAYBE_COLOR_RGBA,
    ACCEPT_HOVER_COLOR_RGBA,
    MAYBE_HOVER_COLOR_RGBA
    )

from VariableManagerWidget import VariableManagerWidget as VariableManagerWidget

from Utils import (
    AbstractComboBox,
    AbstractUserBooleanWidget,
    convertStringBoolToBool,
    getMainWidget,
    getNextVersion,
    goToNode,
    mkdirRecursive,
    updateNodeName
)


class VariableManagerEditor(QWidget):
    """
    The top level widget for the editor.  This is here to encapsulate
    the main widget with a stretch box...
    """
    def __init__(self, parent, node):
        super(VariableManagerEditor, self).__init__(parent)
        self.node = node
        QVBoxLayout(self)
        self.main_widget = VariableManagerMainWidget(self, node)
        resize_widget = UI4.Widgets.VBoxLayoutResizer(self)
        self.layout().addWidget(self.main_widget)
        self.layout().addWidget(resize_widget)
        self.setFixedHeight(500)

        # register node delete handler...
        # attempting to destroy the nodegraph lol
        Utils.EventModule.RegisterCollapsedHandler(
            self.nodeDelete, 'node_delete', None
        )

        Utils.EventModule.RegisterCollapsedHandler(
            self.loadBegin, 'nodegraph_loadBegin', None
        )

    def nodeDelete(self, args):
        if args[0][2]['node'] == self.node:
            self.destroyNodegraph()

    def loadBegin(self, args):
        self.destroyNodegraph()

    def destroyNodegraph(self):
        """
        Purges all metadata from the Nodegraph.  If you don't do this,
        holy warning messages batman!  But it doesn't crash ;).

        Essentially there is a private class attr on the Node Graph Widget called
        __nodegraphWidgetList which needs to have the nodegraph removed from it,
        or else it will let you know that its been destroyed
        """
        # get node graph widget
        nodegraph_widget = self.main_widget.variable_manager_widget.nodegraph_tab._NodegraphPanel__nodegraphWidget

        # clean up
        NodeGraphView.CleanupModule(self)
        nodegraph_widget.cleanup()


class VariableManagerMainWidget(QWidget):
    """
    Main editor widget for the Variable Manager.

    Attributes:
        options_list (list): a list of all of the graph state variables
        root_publish_dir (str): path on disk to internal publish directory
            This is the root location for publishing that is displayed to the
            user in the second row titled "publish dir"
        node (node): this node
        pattern
        node_type (str): type of node that this Variable Manager is set by
            default to.
        variable (str): sets the variable for the node
            param / tree widget / editor class
        working_item (item): this attribute is the current selection in the
            VariableManagerBrowser TreeWidget
    """

    def __name__(self):
        return "VariableManagerMainWidget"

    """ INIT """
    def __init__(self, parent, node):
        print("init edit")
        # initialize
        super(VariableManagerMainWidget, self).__init__(parent)

        self.initDefaultAttributes(node)
        self.initGUI()
        self.item_list = None

        # Set up initial values if this node is not being instantiated
        # for the first time
        self.loadUserParameters()

        # Signals / Slots
        Utils.EventModule.RegisterCollapsedHandler(
            self.gsvChanged, 'parameter_finalizeValue', None
        )

        Utils.EventModule.RegisterCollapsedHandler(
            self.selectNodePopulateParameter, 'node_setSelected', None
        )

    def initDefaultAttributes(self, node):
        """
        reinitialize default attributes on the node, so that they
        can be recalled

        Args:
            node (node): This node
        """

        self.setNode(node)
        self.node.__init__(populate=False)
        self.variable = self.node.getParameter('variable').getValue(0)
        self.node_type = self.node.getParameter('node_type').getValue(0)
        self.pattern = None
        self._options_list = []
        self.updateOptionsList()
        publish_dir = self.node.getParameter('publish_dir').getValue(0)
        self.setRootPublishDir(publish_dir)

    def initGUI(self):
        """
        Creates the interface for the user
        """
        # create main layout
        QStackedLayout(self)

        # create widgets
        self.variable_manager_widget = VariableManagerWidget(self, node=self.node)

        self.versions_display_widget = VersionsDisplayWidget(self)
        self.publish_display_widget = PublishDisplayWidget(self)
        self.warning_display_widget = WarningWidget(self)
        # setup layouts
        self.layout().addWidget(self.variable_manager_widget)
        self.layout().addWidget(self.versions_display_widget)
        self.layout().addWidget(self.publish_display_widget)
        self.layout().addWidget(self.warning_display_widget)

    def loadUserParameters(self):
        """
        If this node is not being instantiated and already has
        been modified by the user.  This will load in the users
        settings such as the <node type> and <variable>.
            ( copy / paste  |  load file  |  etc )
        """
        if self.node.getParameter('variable').getValue(0) != '':
            # init GSV menu
            variable = self.node.getParameter('variable').getValue(0)
            self.setVariable(variable)
            # setup gsv change
            self.variable_manager_widget.variable_menu.setCurrentIndexToText(variable)

            self.updateOptionsList()

            # initialize node type menu
            node_type = self.node.getParameter('node_type').getValue(0)
            node_type_menu = self.variable_manager_widget.node_type_menu
            # node_type_menu.setExistsFlag(False)
            node_type_menu.setCurrentIndexToText(node_type)

    """ UTILS """
    """ UPDATE VARIABLE SWITCH"""
    def updateVariableSwitch(self, root_node, variable_list):
        """
        creates/deletes all the ports for one individual variable switch

        Args:
            root_node (Root Node): Root node container
            variable_list (list): list of all of the GSV's in the
                current project plus the new one to append
                if this is a user update.  This is gathered from
                the getVariableList() in this scope.
        """
        # get nodes
        block_group = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.block_group').getValue(0))
        vs_node = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.vs_node').getValue(0))

        # remove existing ports
        for input_port in vs_node.getInputPorts():
            if input_port.getName() != 'default':
                vs_node.removeInputPort(input_port.getName())

        # add ports
        for pattern_string in sorted(variable_list):
            param_string = pattern_string
            for char in param_string:
                if char.isalnum() is False:
                    param_string = param_string.replace(char, '_')

            port = vs_node.addInputPort(param_string)
            pattern = pattern_string.replace(PATTERN_PREFIX, '')
            vs_node.getParameter('patterns.%s' % param_string).setValue(str(pattern), 0)
            port.connect(block_group.getOutputPortByIndex(0))

    def getVariableList(self, block_group, variable_list):
        """
        Gathers all of the patterns necessary for this specific variable
        that is downstream of the current item

        Args:
            block_group (Block Node): Node that holds all of the
                patterns/blocks.
            variable_list (list): A list of strings containing the current GSV list
        Returns (list): of strings with the name of all of the GSVs
            in the current project
        """
        for param in block_group.getParameter('nodeReference').getChildren():
            if PATTERN_PREFIX in param.getName():
                veg_node = NodegraphAPI.GetNode(param.getValue(0))
                pattern = veg_node.getParameter('pattern').getValue(0)
                variable_list.append(PATTERN_PREFIX+pattern)

            elif BLOCK_PREFIX in param.getName():
                root_node = NodegraphAPI.GetNode(param.getValue(0))
                block_group = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.block_group').getValue(0))
                self.getVariableList(block_group, variable_list)
        return list(set(variable_list))

    def updateAllVariableSwitches(self, root_node, new_pattern=None):

        """
        recursively searches up the node graph to set update the variable switches

        Args:
            root_node : node to start looking for update on.  This should be
                a node with the parameter type set to root.
            new_pattern : if it exists will add this to the variable list
                (getVariableList only finds current vars).  This only needs
                to be provided when a NEW GSV has been created.
        """

        # end recursion if at top level
        if root_node.getParameter('hash').getValue(0) == 'master':
            return
        else:
            # get variable list
            block_node_name = root_node.getParameter('nodeReference.block_group').getValue(0)
            block_node = NodegraphAPI.GetNode(block_node_name)
            temp_list = [new_pattern]
            variable_list = self.getVariableList(block_node, variable_list=list(filter(None, temp_list)))

            # update the internal variable switches
            self.updateVariableSwitch(root_node, variable_list)

            # recurse
            new_root_node = root_node.getParent().getParent()
            self.updateAllVariableSwitches(new_root_node, new_pattern=new_pattern)

    def getAllChildItems(self, item):
        """
        returns all children underneath a specific item

        CLEANUP: self.item_list needs to be removed... this recursion is bad...

        Args:
            item (VariableManagerBrowserItem): item to search below for all children
        """
        if item.childCount() > 0:
            for index in range(item.childCount()):
                child = item.child(index)
                self.item_list.append(child)
                if child.childCount() > 0:
                    self.getAllChildItems(child)
        return self.item_list

    def connectInsideGroup(self, node_list, parent_node):
        """
        Connects all of the nodes inside of a specific node in a linear fashion

        TODO:
            len equal to 2 and more
            than n+2 can be combined
            into one function...

        Args:
            node_list (list): list of nodes to be connected together, the order
                of the nodes in this list, will be the order that they are connected in
            parent_node (node): node have the nodes from the node_list
                wired into.
        """
        # get parent send / receive ports
        send_port = parent_node.getSendPort('in')
        return_port = parent_node.getReturnPort('out')
        # 0 nodes to connect
        if len(node_list) == 0:
            send_port.connect(return_port)

        # 1 node to connect
        elif len(node_list) == 1:
            node_list[0].getOutputPortByIndex(0).connect(return_port)
            node_list[0].getInputPortByIndex(0).connect(send_port)

        # 2 nodes to connect
        elif len(node_list) == 2:
            node_list[0].getInputPortByIndex(0).connect(send_port)
            node_list[1].getOutputPortByIndex(0).connect(return_port)
            node_list[0].getOutputPortByIndex(0).connect(node_list[1].getInputPortByIndex(0))
            NodegraphAPI.SetNodePosition(node_list[0], (0, 100))

        # n+2 nodes to connect
        elif len(node_list) > 2:
            for index, node in enumerate(node_list[:-1]):
                node.getOutputPortByIndex(0).connect(node_list[index+1].getInputPortByIndex(0))
                NodegraphAPI.SetNodePosition(node, (0, index * -100))
            node_list[0].getInputPortByIndex(0).connect(send_port)
            node_list[-1].getOutputPortByIndex(0).connect(return_port)
            NodegraphAPI.SetNodePosition(node_list[-1], (0, len(node_list) * -100))

    def getItemPublishDir(self, include_publish_type=None):
        """
        returns the directory which holds the livegroups for the pattern/block

        Kwargs:
            include_publish_type (settings.ITEM_TYPE): inside of the items
                publish directory, this will decide if the publish type subdirectory
                should be included. Accept values are
                    BLOCK_ITEM
                    MASTER_ITEM
        """
        item = self.getWorkingItem()
        variable = self.getVariable()
        publish_dir = self.getRootPublishDir()

        # attribute checks
        try:
            unique_hash = item.getHash()
        except AttributeError:
            unique_hash = 'master'

        try:
            item_type = item.getItemType()
        except AttributeError:
            item_type = MASTER_ITEM

        if item_type in [
            PATTERN_ITEM,
            MASTER_ITEM
        ]:
            publish_type = 'patterns'

        elif item.getItemType() == BLOCK_ITEM:
            publish_type = 'blocks'

        # set location
        location = publish_dir + '/{variable}/{publish_type}/{unique_hash}'.format(
            variable=variable,
            publish_type=publish_type,
            unique_hash=unique_hash
        )

        # include item type
        if include_publish_type:
            if include_publish_type in BLOCK_PUBLISH_GROUP:
                publish_type_str = 'block'
            elif include_publish_type == PATTERN_ITEM:
                publish_type_str = 'pattern'
            else:
                print('invalid publish type provided... derp')

            location += '/{0}'.format(publish_type_str)
        return location

    """ DISPLAY EVENTS """
    def showWarningBox(self, warning_text, accept, cancel, detailed_warning_text=''):
        """
        Shows the warning message to the user.  This is stored as a widget
        on the top most layout of editor.

        warning_text (str): The primary warning text to display to the user
        accept (fun): The function to run if the user hits accept
        cancel (fun): The function to run if the user hits cancel
        detailed_warning_text (str): The super detailed warning message
            to provide any additional warning details to the user.
        """
        self.warning_display_widget.update(
            warning_text, accept, cancel, detailed_warning_text
        )
        self.layout().setCurrentIndex(3)

    """ EVENTS """
    def addGSVPattern(self, param):
        """
        Adds an item to the available graph state variables in the dropdown menu

        Args:
            param (parameter): the GSV parameter that has been changed or updated
        """
        if param.getName() == 'value':
            options_list = self.getOptionsList()
            pattern_name = param.getValue(0)

            if pattern_name in options_list:
                pass
            else:
                # create new browser item and nodes
                self.variable_manager_widget.variable_browser.createNewBrowserItem(
                    item_type=PATTERN_ITEM, item_text=str(pattern_name)
                )

                self.updateOptionsList()

    def gsvChanged(self, args):
        """
        Looks for user parameter changes, and registers a function
        for specific events such as:
            Current publish dir changed --> self.changeDirectory()
            User adds new pattern to current GSV --> addGSVPattern()
        """
        root_node = NodegraphAPI.GetRootNode()
        # NEW
        try:
            if args[2][2]:
                if args[2][2]['node'] == root_node and args[2][2]['param'].getParent().getName() == self.getVariable():
                    self.addGSVPattern(args[2][2]['param'])
        except:
            pass

        # =======================================================================
        # publish_dir updated
        # check to see if it should create new directories
        # =======================================================================
        # MUTATED
        try:
            if args[0][2]:
                if args[0][2]['node'] == self.node and args[0][2]['param'].getName() == 'publish_dir':
                    if args[0][2]['param'].getName() == 'publish_dir':
                        self.changeDirectory(args)
                if args[0][2]['node'] == root_node and args[0][2]['param'].getParent().getName() == self.getVariable():
                    self.addGSVPattern(args[0][2]['param'])
        except:
            pass

    def selectNodePopulateParameter(self, args):
        """
        Displays the meta parameters when the user selects a node.
        However this will only work IF the node_type is set to "<multi>".
        As this is the parameter display handler for inside for the special
        <multi> case..
        """
        if self.node_type == 'Group':
            self.populateParameters(node_list=NodegraphAPI.GetAllSelectedNodes())

    def createParamReference(self, node_name, hide_title=False):
        """
        Creates a teledrop parameter widget

        Args:
            node_name (str): name of node to be referenced

        Returns:
            teledropparam
        """
        policyData = dict(displayNode="")
        rootPolicy = QT4FormWidgets.PythonValuePolicy("cels", policyData)
        params_policy = rootPolicy.getChildByName("displayNode")
        params_policy.getWidgetHints().update(
            widget='teleparam',
            open="True",
            hideTitle=repr(hide_title)
        )
        param_widget = UI4.FormMaster.KatanaWidgetFactory.buildWidget(None, params_policy)
        params_policy.setValue(node_name, 0)
        return param_widget

    def populateParameters(self, node_list=None):
        """
        Displays the parameters in the bottom of the GUI,
        this is currently linked to the Alt+W hotkey.

        Args:
            node_list (list): list of nodes that will have their parameters displayed.
        """
        splitter = self.variable_manager_widget.splitter

        if splitter.widget(1):
            # if splitter.itemAt(2):
            # clear params
            # print(splitter.itemAt(2).widget())
            splitter.widget(1).setParent(None)
            params_layout = self.variable_manager_widget.params_layout
            for i in reversed(range(params_layout.count())):
                params_layout.itemAt(i).widget().setParent(None)

            # add params
            if node_list is None:
                node_list = NodegraphAPI.GetAllSelectedNodes()

            for node in node_list:
                if hasattr(node, 'getType'):
                    if node.getType() != 'VariableManager':
                        parent_node = self.getWorkingItem().getVEGNode()
                        if node.getParent() == parent_node:
                            # determine if title should be hidden or not
                            if len(node_list) < 2:
                                hide_title = True
                            else:
                                hide_title = False

                            # Create teleparams widget
                            params_widget = self.createParamReference(node.getName(), hide_title)
                            params_layout.addWidget(params_widget)
                            params_layout.update()

            splitter.addWidget(self.variable_manager_widget.params_scroll)
        self.variable_manager_widget.params_widget.show()

    def changeDirectory(self, args):
        """
        If publish_dir parameter is changed, this will ask the user if they
        are sure they'd like to continue if the user decides to continue,
        it will create all of the new directories, but will NOT move over
        the current publishes

        TODO:
            change return values from ints to keywords
        """
        def createDirectories(publish_dir, variable):
            """
            Creates all necessary directories / subdirectories
            """

            variable_dir = '{publish_dir}/{variable}'.format(
                publish_dir=publish_dir,
                variable=variable
            )

            dir_list = [
                new_publish_dir,
                variable_dir,
                variable_dir + '/blocks',
                variable_dir + '/patterns'
            ]
            for dir_item in dir_list:
                if not os.path.exists(dir_item):
                    os.mkdir(dir_item)
            master_item = self.variable_manager_widget.variable_browser.topLevelItem(0)
            self.item_list = [master_item]
            self.getAllChildItems(master_item)

            dir_list = ['pattern', 'block']
            for item in self.item_list:
                unique_hash = item.getHash()
                if item.getItemType() == BLOCK_ITEM:
                    item_type = 'blocks'
                elif item.getItemType() in [PATTERN_ITEM, MASTER_ITEM]:
                    if item.getItemType() == PATTERN_ITEM:
                        hash_string = unique_hash[unique_hash.rindex('_') + 1:]
                        unique_hash = '%s_%s' % (variable, hash_string)
                        item.getRootNode().getParameter('hash').setValue(unique_hash, 0)
                    item.setHash(unique_hash)
                    item_type = 'patterns'

                item_dir = '%s/%s/%s' % (variable_dir, item_type, unique_hash)
                os.mkdir(item_dir)
                item.setPublishDir(item_dir)
                for dir_item in dir_list:
                    if not os.path.exists(item_dir + '/%s' % dir_item):
                        os.mkdir(item_dir + '/%s' % dir_item)
                        os.mkdir(item_dir + '/%s/live' % dir_item)

            # publish v000 directories
            item = master_item
            self.publish_display_widget.publish_type = BLOCK_ITEM
            self.publish_display_widget.publishBlock(item=item)

        new_publish_dir = args[0][2]['param'].getValue(0)

        # if no variable set, create the root dir
        if self.variable == '':
            mkdirRecursive(new_publish_dir)
            self.setRootPublishDir(new_publish_dir)
            self.node.getParameter('publish_dir').setValue(new_publish_dir, 0)
            return

        # ask user to confirm directory change...
        if not os.path.exists(new_publish_dir):
            def accept():
                self.setRootPublishDir(new_publish_dir)
                self.node.getParameter('publish_dir').setValue(new_publish_dir, 0)
                createDirectories(new_publish_dir, self.getVariable())

            def cancel():
                root_publish_dir = self.getRootPublishDir()
                self.node.getParameter('publish_dir').setValue(root_publish_dir, 0)

            warning_text = 'Do you wish to create new directories?'
            detailed_warning_text = """
Accepting this event will create a bunch of new crap on your file system,
but you need this crap in order to save stuff into it.
            """

            self.showWarningBox(
                warning_text, accept, cancel, detailed_warning_text
            )
        else:
            """
            check if the dir has actually changed or if it was a
            cancellation of a dir changed to avoid recursion

            I have no idea how this works anymore and I'm to lazy
            to look at it and figure it out...
            """
            if self.getRootPublishDir() == new_publish_dir:
                return
            self.setRootPublishDir(new_publish_dir)
            # set master item
            master_item = self.variable_manager_widget.variable_browser.topLevelItem(0)
            self.setWorkingItem(master_item)

            # set version
            self.versions_display_widget.update(column=2, gui=True)

    """ PROPERTIES """
    def getNode(self):
        return self.node

    def setNode(self, node):
        self.node = node

    def getOptionsList(self):
        return self._options_list

    def updateOptionsList(self):
        """
        repopulates the options list which is a list that
        contains all of the GSV's that are currently available.
        """
        root = NodegraphAPI.GetRootNode()
        variable_param_name = 'variables.{variable}.options'.format(variable=self.getVariable())
        if root.getParameter(variable_param_name):
            children = NodegraphAPI.GetRootNode().getParameter(variable_param_name).getChildren()
            options_list = [x.getValue(0) for x in children]
            self._options_list = options_list

    def getPattern(self):
        return self.pattern

    def setPattern(self, pattern):
        self.pattern = pattern

    def getNodeType(self):
        return self.node_type

    def setNodeType(self, node_type):
        self.node_type = node_type

    def getVariable(self):
        try:
            variable = self.variable
        except AttributeError:
            variable = self.node.getParameter('variable').getValue(0)
            self.setVariable(variable)
        finally:
            return variable

    def setVariable(self, variable):
        self.variable = variable
        self.node.getParameter('variable').setValue(variable, 0)
        self.variable_manager_widget.variable_browser.headerItem().setText(0, variable)

    def setWorkingItem(self, item):
        self.working_item = item

    def getWorkingItem(self):
        if hasattr(self, 'working_item'):
            return self.working_item
        else:
            return None

    def getRootPublishDir(self):
        return self.root_publish_dir

    def setRootPublishDir(self, root_publish_dir):
        self.root_publish_dir = root_publish_dir


class VersionsDisplayWidget(AbstractUserBooleanWidget):
    """
    TODO:
        clean this up...
    creates a new widget for the user to view the versions currently available
    the user can change the version and check the release notes on each version
    before accepting this version
    Args:
        column (int): column clicked to determine if it is publishing a pattern (1) or block (2)
        version (str): version to use in string format such as "v000"
        gui (bool): If True, this widget pops up and lets the user choose what version
            they want to use.  If False, this widget is bypassed, and the updates happen
            automatically to the live/latest version.
        previous_variable (str): the previous GSV.  This is here incase it needs to be reset later?
    """
    def __init__(
        self,
        parent=None
    ):
        super(VersionsDisplayWidget, self).__init__(parent)
        # init attrs
        self.main_widget = getMainWidget(self)
        self._column = 1
        self._gui = False
        self._previous_variable = ''
        # create GUI
        self.initGUI()

    def initGUI(self):
        # Create main layout
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create Widgets
        notes_label = QLabel()
        self.version_combobox = VersionsDisplayMenu(self, notes_label)

        # add widgets to layout
        central_layout.addWidget(self.version_combobox)
        central_layout.addWidget(notes_label)

        self.setCentralWidget(central_widget)
        self.setAcceptEvent(self.__accepted)
        self.setCancelEvent(self.__cancelled)

    """ UTILS """
    def getPublishDir(self):
        """
        return (str): the current directory where this should look
            for relevant publishes.
        """
        if self.column == PATTERN_ITEM.COLUMN:
            include_publish_type = PATTERN_ITEM
        elif self.column == BLOCK_ITEM.COLUMN:
            include_publish_type = BLOCK_ITEM

        publish_dir = self.main_widget.getItemPublishDir(
            include_publish_type=include_publish_type
        )
        return publish_dir

    def getCurrentVersion(self):
        """
        returns (str): the current version available.  This
            will be displayed as the default version.
        """
        item = self.main_widget.getWorkingItem()
        if not hasattr(self, 'version'):
            if item is None:
                version = 'live'
            else:
                version = item.text(self.column)
        return version

    def loadLiveGroup(
        self,
        version=None
    ):
        """
        Loads a live group.  These live groups are used as the
        save file types for individual portions of the Variable
        Manager

        Args:
            version (str): the current version to be loaded, if no version
                is provided, this will check the current text for the version.
                The version is returned as v000
        """
        # current thingy mabobber to publish
        item = self.main_widget.getWorkingItem()

        # get publish node
        """ only look at one thing...
        only looking at the publish type, not looking at the item type...
        """
        if item.getItemType() == PATTERN_ITEM:
            publish_type = PATTERN_ITEM
            publish_node = item.getPatternNode()
        elif item.getItemType() in BLOCK_PUBLISH_GROUP:
            if self.column == PATTERN_ITEM.COLUMN:
                publish_type = PATTERN_ITEM
                publish_node = item.getPatternNode()
            elif self.column == BLOCK_ITEM.COLUMN:
                publish_type = BLOCK_ITEM
                publish_node = item.getBlockNode()

        # get publish directory
        if not version:
            version = str(self.version_combobox.currentText())

        publish_dir = '{publish_dir}/{version}/something.livegroup'.format(
            publish_dir=self.main_widget.getItemPublishDir(include_publish_type=publish_type),
            version=version
        )

        # loading load group
        live_group = NodegraphAPI.ConvertGroupToLiveGroup(publish_node)
        live_group.getParameter('source').setValue(publish_dir, 0)
        live_group.load()
        loaded_publish_node = live_group.convertToGroup()

        # update item attributes
        if item.getItemType() == PATTERN_ITEM:
            item.setRootNode(loaded_publish_node)
            item.setBlockNode(loaded_publish_node)
            item.setPatternNode(loaded_publish_node)
            item.setVEGNode(loaded_publish_node.getChildByIndex(0))
        elif item.getItemType() in BLOCK_PUBLISH_GROUP:
            if self.column == PATTERN_ITEM.COLUMN:
                item.setPatternNode(loaded_publish_node)
                item.setVEGNode(loaded_publish_node.getChildByIndex(0))
            elif self.column == BLOCK_ITEM.COLUMN:
                item.setBlockNode(loaded_publish_node)

        # update browser widget
        self.main_widget.variable_manager_widget.variable_browser.reset()
        self.main_widget.variable_manager_widget.variable_browser.populate()

        # update variable switch...
        root_node = item.getPatternNode().getParent()
        self.main_widget.updateAllVariableSwitches(root_node)
        self.main_widget.updateOptionsList()

    """ EVENTS """
    def display(self):
        self.main_widget.layout().setCurrentIndex(1)

    def update(
        self,
        column=None,
        version=None,
        gui=None,
        previous_variable=None
    ):
        """
        This is the show command, when this is triggered,
        the widget will update and be displayed to the user.
        """
        # change widget to versions display
        self.display()
        if column:
            self.column = column
        if version:
            self.version = version
        if previous_variable:
            self.previous_variable = previous_variable
        if gui:
            self.gui = gui

        # repopulate versions
        local_publish_dir = self.getPublishDir()
        self.version_combobox.updateVersions(local_publish_dir)

        # get/display latest version if there is no gui
        if self.gui is True:
            root_publish_dir = self.main_widget.getRootPublishDir()
            variable_dir = '%s/%s' % (root_publish_dir, self.main_widget.getVariable())

            master_dir = variable_dir + '/patterns/master/block'

            versions = sorted(os.listdir(master_dir))
            versions.remove('live')
            versions_dir_list = []

            for version in versions:
                live_file = '/'.join([master_dir, version, 'live.csv'])
                if os.path.exists(live_file) is True:
                    versions_dir_list.append(version)
            if len(versions_dir_list) > 0:
                latest_version = versions_dir_list[-1]
            elif len(versions) > 0:
                latest_version = versions[-1]
            else:
                latest_version = 'live'

            self.version_combobox.setCurrentIndexToText(latest_version)

    def __cancelled(self):
        """
        resets all settings that were set up for display versions
        """
        root_publish_dir = self.main_widget.getRootPublishDir()
        self.main_widget.node.getParameter('publish_dir').setValue(root_publish_dir, 0)
        self.main_widget.setVariable(self.previous_variable)
        self.main_widget.variable_manager_widget.variable_menu.setCurrentIndexToText(self.previous_variable)

    def __accepted(self):
        """
        load block selected and set the publish dir
        """
        self.loadLiveGroup()

    """ PROPERTIES """
    @property
    def column(self):
        return self._column

    @column.setter
    def column(self, column):
        self._column = column

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        self._version = version

    @property
    def previous_variable(self):
        return self._previous_variable

    @previous_variable.setter
    def previous_variable(self, previous_variable):
        self._previous_variable = previous_variable

    @property
    def gui(self):
        return self._gui

    @gui.setter
    def gui(self, gui):
        self._gui = gui


class VersionsDisplayMenu(AbstractComboBox):
    '''
    Inside of the VersionsDisplayWidget, this is the drop down
    menu that will display the versions to the user to be selected

    Need to make this inherit from AbstractComboBox...
    notes_label (QLabel): The widget that will display the notes
        to the user from a specific version of the publish.
    '''
    def __init__(
        self,
        parent,
        notes_label
    ):
        super(VersionsDisplayMenu, self).__init__(parent)
        self.label = notes_label
        # connect signals
        self.currentIndexChanged.connect(self.updateNoteText)

    def updateNoteText(self):
        """
        When the publish version is changed, this will update
        the note that is displayed to the user.
        """
        # Set Color
        live_dir = '%s/%s/live.csv' % (self.publish_dir, self.currentText())
        version_dir_list = []
        for version in os.listdir(self.publish_dir):
            live_file = '/'.join([self.publish_dir, version, 'live.csv'])
            if os.path.exists(live_file) is True:
                version_dir_list.append(version)
        if os.path.exists(live_dir):
            if max(version_dir_list) == self.currentText():
                self.lineEdit().setStyleSheet("background-color: rgb(60,94,60);border: none;")
            else:
                self.lineEdit().setStyleSheet("background-color: rgb(94,94,60);border: none;")
        else:
            self.lineEdit().setStyleSheet("")

        # Write Notes
        notes_dir = '%s/%s/notes.csv' % (self.publish_dir, self.currentText())
        if os.path.exists(notes_dir):
            with open(notes_dir, 'rb') as csvfile:
                note = csvfile.readlines()
                note_text = ''.join(note)
                self.label.setText(str(note_text))
                self.label.setWordWrap(True)
        else:
            self.label.setText('try making some notes...')
            self.label.setWordWrap(True)

    """ UTILS """
    def updateVersions(self, publish_dir):
        """
        Updates the versions available for selection.

        Args:
            publish_dir (str): directory to search for publishing.
                Not really sure why Im' setting this here...
        """
        self.publish_dir = publish_dir
        self.populate()

    def populate(self):
        """
        adds all of the items to the model widget
        adds color to the items
        """
        model = QtGui.QStandardItemModel()
        live_item = None
        version_list = sorted(os.listdir(self.publish_dir))
        for i, version in enumerate(reversed(version_list)):
            item = QtGui.QStandardItem(version)
            # setup colors
            if os.path.exists('%s/%s/live.csv' % (self.publish_dir, version)):
                color = QtGui.QColor(60, 94, 60, 255)
                if live_item:
                    color = QtGui.QColor(94, 94, 60, 255)
                    brush = QtGui.QBrush(color)
                brush = QtGui.QBrush(color)
                item.setBackground(brush)
                live_item = item
            model.setItem(i, 0, item)

        self.setModel(model)
        self.setModelColumn(0)


class PublishDisplayWidget(AbstractUserBooleanWidget):
    """
    Main widget for publishing notes for the user.  When the user selects
    the call to publish a pattern or block.  This widget is displayed to the
    user instead of the main GUI.

    Hitting Accept / Cancel will return the user back to the main GUI
    for the Variable Manager

    TODO:
        Update doc strings...
    """
    def __init__(self, parent=None):
        super(PublishDisplayWidget, self).__init__(parent)

        # init attrs
        self.main_widget = getMainWidget(self)
        self._name = ''

        # init gui
        self.initGUI()

    def initGUI(self):
        """
        Creates the GUI for the user
        """
        # create main layout
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)

        # create widgets
        self.besterest_button = QPushButton()
        self.besterest_button.clicked.connect(self.togglePublishState)
        self.setBesterestButtonHeight(100)
        self.besterest_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # set initial state
        self.setPublishState(0)

        # create display label
        self.label = QLabel(self.name)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        font = self.label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() * 5)
        self.label.setFont(font)
        self.text_edit = PublishNotesWidget()
        self.text_edit.setMinimumHeight(200)

        # add widgets to layout
        central_layout.addWidget(self.label)
        central_layout.addWidget(self.text_edit)
        central_layout.addWidget(self.besterest_button)

        self.setCentralWidget(central_widget)
        self.setAcceptEvent(self.__accepted)
        self.setCancelEvent(self.__cancelled)

    def update(
        self,
        name=None,
        publish_type=None,
        item=None,
    ):
        """
        Args:
            name (str): gsv name, pattern, and version of what the user
                will currently publish.  Display as
                    <gsv name>|<gsv pattern>|<v000>
            publish_type (settings.ITEM_TYPE):
                How is this setting to pattern somewhere...
            item (VariableManagerBrowserItem): Item that is currently being
                published
        """
        if name:
            self.label.setText(name)
            self.name = name
        if publish_type:
            self.publish_type = publish_type
        if item:
            self.item = item
        pass

    def updateStyleSheet(self):
        """
        Updates the color on the style sheet, as it appears
        this is caching the values into the stylesheet.  Rather
        than dynamically calling them =\
        """
        self.besterest_button.setStyleSheet(
            """
            QPushButton{
                background-color: rgba%s;
                border: none;
                color: rgb(0, 0, 0);
            }
            QPushButton::hover{
                background-color: rgba%s;
            }
            """ % (
                    self.besterest_button_color,
                    self.besterest_button_hover_color
                )
            )

    """ PUBLISH """
    def __setAsBesterest(self, publish_loc, node, note):
        """
        sets up this publish to be live

        Args:
            publish_loc (str): path to live directory of this
            node (node): Root node to be published
            note (str): the user notes for this publish
        Kwargs:
            publish_type (VariableManagerBrowserItem.TYPE): The type of
                the browser item to be published.
        """
        if self.getPublishState() == 1:
            # get live dir
            live_dir = publish_loc[:publish_loc.rindex('/')] + '/live'
            live_file = live_dir + '/something.livegroup'

            # remove existing live data
            if os.path.exists(live_file):
                os.remove(live_file)
            if os.path.exists(live_file):
                os.remove(live_dir + '/notes.csv')

            # convert and publish
            node.publishAssetAndFinishEditingContents(live_dir + '/something.livegroup')

            # publish notes
            self.__publishNotesToDisk(live_dir, note)

            # create live flag file... this should really change to something less stoopid
            with open(publish_loc + '/live.csv', 'w') as filehandle:
                filehandle.write('thecowlevel.slack.com')
            return

    def __convertToLiveGroup(self, publish_loc, node, version):
        """
        Converts the group to a live group and ensures that there
        are no local changes on the live group by publishing the
        contents via the live groups "publishAssetAndFinishEditingContents"

        Args:
            publish_loc (str): the directory to publish all of the new files in
            node (Group Node): The group node to be published, this should
                be the root of either a BLOCK or PATTERN.
            version (str): the new version to publish
        """
        os.mkdir(publish_loc)
        Utils.EventModule.ProcessAllEvents()
        live_group = NodegraphAPI.ConvertGroupToLiveGroup(node)
        if not live_group.getParameter('version'):
            live_group.getParameters().createChildString('version', version)
        live_group.getParameter('version').setValue(version, 0)
        live_group.publishAssetAndFinishEditingContents(publish_loc + '/something.livegroup')
        return live_group

    def __publishNotesToDisk(self, publish_loc, note):
        """
        Publishes the user written notes to disk.

        Args:
            publish_loc (str): the location on disk where the notes will be saved
            note (str): the note the user puts on this publish...
        """
        with open(publish_loc + '/notes.csv', 'w') as filehandle:
            filehandle.write(note)

    def publishAllGroups(self, item, orig_item):
        """
        start of recursive function to run through each subgroup and publish them

        Args:
            item (VariableManagerBrowserItem): the current item to publish
            orig_item (VariableManagerBrowserItem): the original item that can be considered the root of this publish
        """
        # get publish dir
        publish_loc = self.main_widget.getItemPublishDir(include_publish_type=self.publish_type)
        version = getNextVersion(publish_loc)
        publish_loc += '/{version}'.format(version=version)
        note = self.text_edit.toPlainText()

        # publish all child groups
        if item.getItemType() in [
            BLOCK_ITEM,
            MASTER_ITEM
        ]:
            num_children = item.childCount()
            for index in range(num_children):
                child = item.child(index)
                self.publishAllGroups(child, orig_item)

        # Below the recursion to inverse the winding order...
        self.main_widget.setWorkingItem(item)
        self.main_widget.setPattern(str(item.text(0)))

        # Statement to check for original item, if it is, dont publish the pattern
        if item != orig_item:
            self.publishPattern(item)
            if item.getItemType() == BLOCK_ITEM:
                self.publishGroup(publish_loc, item, version, note)

        # Publish the group
        elif item.getItemType() in [
            BLOCK_ITEM,
            MASTER_ITEM
        ]:
            self.publishGroup(publish_loc, item, version, note)

    def publishGroup(self, publish_loc, item, version, note):
        """
        publishes the group and writes out the notes...
        """
        # convert to live group
        block_node = item.getBlockNode()
        live_group = self.__convertToLiveGroup(publish_loc, block_node, version)

        # write notes to disk
        self.__publishNotesToDisk(publish_loc, note)

        self.__setAsBesterest(publish_loc, live_group, note)

        new_block_node = live_group.convertToGroup()
        # reset references
        new_pattern_node = NodegraphAPI.GetNode(item.getRootNode().getParameter('nodeReference.pattern_node').getValue(0))
        item.setPatternNode(new_pattern_node)
        item.setVEGNode(new_pattern_node.getChildByIndex(0))
        item.setBlockNode(new_block_node)
        item.setText(2, version)

    def publishBlock(self, item=None):
        """
        publishes the live group container holding all of the different patterns/blocks
        inside of this block it does NOT publish the changes made at this level
        (only changes underneath) to publish changes made at this level, publish the "pattern"

        Kwargs:
            item (VariableManagerBrowserItem): the item to be published
        """
        if not item:
            item = self.main_widget.getWorkingItem()

        orig_item = item
        self.publishAllGroups(item, orig_item)
        self.main_widget.variable_manager_widget.variable_browser.reset()
        self.main_widget.variable_manager_widget.variable_browser.populate()

    def publishPattern(self, item=None):
        """
        publishes the live group containing all of the changes made at this level
        this will be the group called "pattern" in most cases and only publishes the
        nodes... not the hierarchy below... to publish an entire hierarchy use "publishBlock"

        Kwargs:
            item (VariableManagerBrowserItem): the current item to publish
        """
        # get item
        if not item:
            item = self.main_widget.getWorkingItem()

        # get node to publish
        item_type = item.getItemType()
        if item_type in BLOCK_PUBLISH_GROUP:
            pattern_node = item.getPatternNode()
        else:
            pattern_node = item.getRootNode()

        # get attrs
        location = self.main_widget.getItemPublishDir(include_publish_type=PATTERN_ITEM)
        version = getNextVersion(location)
        publish_loc = '{location}/{version}'.format(
            location=location, version=version
        )
        note = self.text_edit.toPlainText()

        # prep for publishing
        live_group = self.__convertToLiveGroup(publish_loc, pattern_node, version)

        # write notes to disk...
        self.__publishNotesToDisk(publish_loc, note)

        # determine if this is a besterest publish
        self.__setAsBesterest(publish_loc, live_group, note)

        # reset item attributes/parameters
        new_root_node = live_group.convertToGroup()
        #new_pattern_node = new_root_node.getChildByIndex(0)

        # update nodes
        if item_type in BLOCK_PUBLISH_GROUP:
            item.setPatternNode(new_root_node)
            item.setVEGNode(new_root_node.getChildByIndex(0))
        else:
            item.setRootNode(new_root_node)
            item.setBlockNode(new_root_node)
            item.setPatternNode(new_root_node)
            item.setVEGNode(new_root_node.getChildByIndex(0))

        # set display text
        item.setText(1, version)

    def __setBesterestButtonStyle(self):
        """
        Sets the color / text of the besterest button based
        on its current publish status
        """
        if self._publish_state % 2 == 0:
            self.besterest_button_color = repr(MAYBE_COLOR_RGBA)
            self.besterest_button_hover_color = repr(MAYBE_HOVER_COLOR_RGBA)
            self.besterest_button.setText('Simply not the best... Not better than all the rest')
        elif self._publish_state % 2 == 1:
            self.besterest_button_color = repr(ACCEPT_COLOR_RGBA)
            self.besterest_button_hover_color = repr(ACCEPT_HOVER_COLOR_RGBA)
            self.besterest_button.setText("""
BESTEREST
* Tina Turner Voice *
( Simply the best, better than all the rest )
            """)
        self.updateStyleSheet()

    def togglePublishState(self):
        """
        Toggles the publish state between boolean values.
        """
        self._publish_state += 1
        self.__setBesterestButtonStyle()

    def setPublishState(self, publish_state):
        self._publish_state = publish_state
        self.__setBesterestButtonStyle()

    def getPublishState(self):
        return self._publish_state % 2

    """ EVENTS """
    def __accepted(self):
        """
        If the user accepts the publish.
        """
        # choose publish type
        if self.publish_type == PATTERN_ITEM:
            self.publishPattern()

        elif self.publish_type == BLOCK_ITEM:
            self.publishBlock()

        # for some reason we're going to the node
        self.goToNode()

        #
        self.main_widget.variable_manager_widget.variable_browser.showItemParameters()

    def __cancelled(self):
        self.goToNode()

    def goToNode(self):
        item = self.main_widget.variable_manager_widget.variable_browser.currentItem()
        if item:
            nodegraph_tab = self.main_widget.variable_manager_widget.nodegraph_tab
            self.main_widget.setPattern(str(item.text(0)))
            self.main_widget.setWorkingItem(item)
            node = item.getVEGNode()
            goToNode(node, nodegraph_tab=nodegraph_tab, frame=True)

    def display(self):
        self.main_widget.layout().setCurrentIndex(2)
        self.text_edit.setPlainText("")
        self.setPublishState(0)

    """ PROPERTIES """
    def getBesterestButtonHeight(self):
        return self.besterest_button_height

    def setBesterestButtonHeight(self, besterest_button_height):
        self.besterest_button.setFixedHeight(besterest_button_height)
        self.besterest_button_height = besterest_button_height

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def publish_type(self):
        return self._publish_type

    @publish_type.setter
    def publish_type(self, publish_type):
        self._publish_type = publish_type

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, item):
        self._item = item


class PublishNotesWidget(QPlainTextEdit):
    """
    Widget that will pop up for users to create their notes in that will be
    published with the internal saving mechanism.

    This is really only subclassed because of the keyboard focus event
    that seems to bug out in Katana.
    """
    def __init__(self, parent=None):
        super(PublishNotesWidget, self).__init__(parent)

    def focusInEvent(self, event, *args, **kwargs):
        self.grabKeyboard()
        QPlainTextEdit.focusInEvent(self, event, *args, **kwargs)

    def focusOutEvent(self, event, *args, **kwargs):
        self.releaseKeyboard()
        QPlainTextEdit.focusOutEvent(self, event, *args, **kwargs)


class WarningWidget(AbstractUserBooleanWidget):
    """
    The warning display that is shown to the user whenever
    they trigger an event that will require a user to accept/deny
    the proposed event.
    """
    def __init__(self, parent=None):
        super(WarningWidget, self).__init__(parent)
        central_widget = QWidget()
        self.text_layout = QVBoxLayout(central_widget)
        self.text_layout.setAlignment(QtCore.Qt.AlignTop)
        self.warning_text = QLabel()
        self.detailed_warning_text = QLabel()
        self.text_layout.addWidget(self.warning_text)
        self.text_layout.addSpacerItem(QSpacerItem(25, 25))
        self.text_layout.addWidget(self.detailed_warning_text)

        self.setCentralWidget(central_widget)

    def update(self, warning_text, accept_pressed, cancel_pressed, detailed_warning_text=''):
        """
        Updates the attributes of this widget in preparation for a show event.

        Args:
            warning_text (str): The warning to be displayed to the user,
                this should be roughly one sentence.
            accept_pressed (fun): The function to be run if the '=>' button is pressed
            cancel_pressed (fun): The function to be run if the '<=" button is pressed

        Kwargs:
            detailed_warning_text (str): the detailed warning message to
                be display to the user.  This should be roughly a paragraph.
        """
        self.setAcceptEvent(accept_pressed)
        self.setCancelEvent(cancel_pressed)
        self.warning_text.setText(warning_text)
        self.detailed_warning_text.setText(detailed_warning_text)

#QTreeWidget