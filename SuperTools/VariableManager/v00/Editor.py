"""
n = UI4.App.Tabs.FindTopTab('Node Graph')
w = n._NodegraphPanel__nodegraphWidget

for i in wl.iterkeys():
    NodeGraphView.CleanupModule(i)
    #w._NodegraphWidget__nodegraphWidgetList.pop(i, None)
    print i

*    need to be able to create patterns...

*    checkHash repeats...

*    gsv change
        -- load live version of
                pattern
                block

* directory publish
    VariableManagerBrowserItem --> createPublishDir
    VariableManagerMainWidget --> changeDirectory

- bugs...
    *  Node Type change
            This needs to be linked to publishing system...
- bad
    *    adding GSV's when auto created...
            this is probably bad... will need some sort of function to ask to add to all or not?
                addGSVPattern
    *    __init__ never registers... until set node viewed flag hit...
            so... what do you do?

- maybe
    *    publish to node name?
            ie $HOME/.katana/<node name>
    *    Align top for display/publish widgets
    *    Hotkey return to last nodegraph display location?

FEATURES:
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
###will fail if GSV has no children/options...

Probably remove GSV Parameter  reference...


Cancel/Restting...
    maybe add a previous variable/dir property to call? Rather than
    the current way of manually every time?

Node Type Change
    Don't repopulate the variableBrowser... just change node type...
        will need to repopulate the meta data though

Should a Block also save/load the pattern for that location?
    - It would load an entire container... rather than a user having
        to load 2 containers...



SuperTool --> group (shot/variable)
            --> block --> group (pattern/shot) [shot] --> block/shots --> LG --> Nodes
PATTERN    :    VEG --> LG --> NODES
BLOCK        :    GROUP/GROUP/VARIABLE SWITCH
MASTER: Top most group

ADD NODES
ports bug.... if ports dont exist?

CLEANUP:
    1.) add getters/settings for widgets in main widget
    2.) Undo Stack --> Need to find all the events...
        Utils.UndoStack.OpenGroup('Import Library Asset')
        Utils.UndoStack.CloseGroup()
BUGS:

    critical?
    0.) Node list... displaying a shitton of useless nodes

    1.) when publish_dir changed... doesnt check subdirs... ie if dir exists,
        it wont create the new blocks, it will assume they already exist,
        which will cause failures...
    non-critcal

    2.) Node not deleting?
    1.) Closing parameters error
            from Nodegraph hack
                    - potentially close widget on param view?

    3.) cant name pattern 'block__' or block 'pattern__' will break... due to string search
    3.) Splitter - default geometry settings?
            init width is wrong somewhere...
            min_width...?

WISH LIST:
    1.) Import/Export?
    3.) Drag/Drop nodes into LG?
    4.) Change 'master' name to <variable name>
    5.) Expose %s to shot/master/creation dirs... so that it can be easily added into a pipeline
        for custom save directories
    6.) Show version of live/greatest (filters by these versions?)
"""

import os
import math

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QShortcut, QScrollArea, QSplitter, QMessageBox, QPlainTextEdit,
    QTreeWidget, QHeaderView, QAbstractItemView, QLineEdit,
    QGridLayout, QSizePolicy, QMenu, QTreeWidgetItem, QStackedLayout,
    QSpacerItem
)
from PyQt5 import QtCore, QtGui

from Katana import UI4, QT4Widgets, QT4FormWidgets
from Katana import NodegraphAPI, Utils, Nodes3DAPI, FnGeolib, NodeGraphView
from Katana import UniqueName, FormMaster, Utils

from ItemTypes import (
    MASTER_ITEM,
    PATTERN_ITEM,
    BLOCK_ITEM,
    BLOCK_PUBLISH_GROUP,
)

from Settings import (
    PATTERN_PREFIX,
    BLOCK_PREFIX,
    SPLITTER_STYLE_SHEET,
    SPLITTER_STYLE_SHEET_HIDE,
    SPLITTER_HANDLE_WIDTH,
    ACCEPT_COLOR_RGBA,
    CANCEL_COLOR_RGBA,
    MAYBE_COLOR_RGBA,
    ACCEPT_HOVER_COLOR_RGBA,
    CANCEL_HOVER_COLOR_RGBA,
    MAYBE_HOVER_COLOR_RGBA
    )

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
        renitializes default attributes on the node, so that they
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

    def updateAllVariableSwitches(self, root_node, new_pattern=None):
        """
        recusively searchs up the node graph to set update the variable switches

        Args:
            root_node : node to start looking for udpate on.  This should be
                a node with the parameter type set to root.
            new_pattern : if it exists will add this to the variable list
                (getVariableList only finds current vars).  This only needs
                to be provided when a NEW GSV has been created.
        """
        def getVariableList(block_group, variable_list=[]):
            """
            Gathers all of the patterns necessary for this specific variable
            that is downstream of the current item

            Args:
                block_group (Block Node): Node that holds all of the
                    patterns/blocks.

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
                    getVariableList(block_group, variable_list=variable_list)
            return list(set(variable_list))

        def updateVariableSwitch(root_node, variable_list):
            """
            creates/deletes all the ports for the variable switch

            Args:
                root_node (Root Node): Root node container
                variable_list (list): list of all of the GSV's in the
                    current project plus the new one to append
                    if this is a user update.  This is gathered from
                    the getVariableList() in this scope.
            """
            block_group = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.block_group').getValue(0))
            vs_node = NodegraphAPI.GetNode(root_node.getParameter('nodeReference.vs_node').getValue(0))
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

        # end recursion if at top level
        if root_node.getParameter('hash').getValue(0) == 'master':
            return
        else:
            # get variable list
            block_node_name = root_node.getParameter('nodeReference.block_group').getValue(0)
            block_node = NodegraphAPI.GetNode(block_node_name)
            temp_list = [new_pattern]
            variable_list = getVariableList(block_node, variable_list=filter(None, temp_list))

            # update the internal variable switches
            updateVariableSwitch(root_node, variable_list)

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
            len equal to 2 and more than n+2 can be combined into one function...

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
            to provide any additinoal warning details to the user.
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
        if self.node_type == '<multi>':
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
            change retvals from ints to keywords
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
            self.versions_display_widget.update(column=2, GUI=True)

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
            set this to display that nodes parameters.  If it is set to <multi> a special
            hotkey will need to be hit to display the parameters in this window,
            by default it is Alt+W
    """
    def __init__(self, parent=None, node=None):
        super(VariableManagerWidget, self).__init__(parent)

        # main layout
        self.main_widget = getMainWidget(self)
        self.node = node
        self.initGUI()

    def initGUI(self):

        QVBoxLayout(self)
        # row 1
        self.r1_hbox = QHBoxLayout()
        self.variable_menu = VariableManagerGSVMenu(self)
        self.publish_dir = self.createValueParam('publish_dir')
        self.node_type_menu = VariableManagerNodeMenu(self)

        self.r1_hbox.addWidget(self.variable_menu)
        self.r1_hbox.addWidget(self.node_type_menu)

        # row 2
        self.r2_hbox = QHBoxLayout()
        self.r2_hbox.addWidget(self.publish_dir)

        self.splitter = QSplitter(QtCore.Qt.Vertical)
        #self.splitter = QVBoxLayout()
        #self.splitter_handle = UI4.Widgets.VBoxLayoutResizer(self)
        self.splitter.setStyleSheet(SPLITTER_STYLE_SHEET)
        #self.splitter.setHandleWidth(settings.SPLITTER_HANDLE_WIDTH)
        # row 2.1
        self.variable_stack = self.createVariableStack()

        # row 2.2
        self.params_widget = self.createParamsWidget()
        self.splitter.addWidget(self.variable_stack)
        self.splitter.addWidget(self.params_scroll)
        self.splitter.setSizes([200, 600])

        #
        self.layout().addLayout(self.r1_hbox)
        self.layout().addLayout(self.r2_hbox)
        self.layout().addWidget(self.splitter)

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

            """
            TODO:
                Create item creation widget here...
            """
            params = QLabel("12345")
            variable_browser_vbox.addWidget(self.variable_browser)
            variable_browser_vbox.addWidget(params)

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

        variable_browser_widget = createVariableManagerBrowserStack()
        self.node_graph_widget = self.createNodeGraphWidget()
        # self.variable_browser.showMiniNodeGraph()

        # Setup Layouts
        self.variable_splitter.addWidget(variable_browser_widget)
        self.variable_splitter.addWidget(self.node_graph_widget)
        vbox.addWidget(self.variable_splitter)
        return widget

    def createNodeGraphWidget(self):
        """
        Creates the internal node graph for this widget.
        This is essentially a mini nodegraph that is embedded
        inside of the parameters.
        """
        node_graph_widget = QWidget()
        layout = QVBoxLayout(node_graph_widget)
        tab_with_timeline = UI4.App.Tabs.CreateTab('Node Graph', None)

        self.nodegraph_tab = tab_with_timeline.getWidget()
        ngw_menu_bar = self.nodegraph_tab.getMenuBar()
        ngw_menu_bar.setParent(None)

        self.nodegraph_tab.layout().itemAt(0).widget().hide()
        layout.addWidget(self.nodegraph_tab)

        return node_graph_widget

    def createParamsWidget(self):
        """
        Creates the widget that will display the parameters
        back to the user when a node is selected in the mini nodegraph.
        """
        params_widget = QWidget()
        self.params_layout = QVBoxLayout()
        self.params_layout.setAlignment(QtCore.Qt.AlignTop)

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


class VersionsDisplayWidget(AbstractUserBooleanWidget):
    """
    creates a new widget for the user to view the versions currently available
    the user can change the version and check the release notes on each version
    before accepting this version
    Args:
        display_type
        column (int): column clicked to determine if it is publishing a pattern (1) or block (2)
        version
        GUI (bool)
        previous_variable
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
        the widget will update and be dispalyed to the user.
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

    Args:
        name (str): gsv name, pattern, and version of what the user
            will currently publish.  Display as
                <gsv name>|<gsv pattern>|<v000>
        publish_type (settings.ITEM_TYPE):
            How is this setting to pattern somewhere...
        publish_state (int): determines if this should be set to the live version or not.
            0 = Note Live
            1 = Live
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


class VariableManagerCreateGSVWidget(QLineEdit):

    def __init__(self, parent=None):
        super(VariableManagerCreateGSVWidget, self).__init__(parent)

    def createGSV(self):
        """
        Creates a new pattern item for this widget.  If that pattern
        does not exist for the current graph state variable, it will
        create the new pattern aswell
        """


class VariableManagerGSVMenu(AbstractComboBox):
    '''
    Drop down menu with autocomplete for the user to select
    what GSV that they wish for the Variable Manager to control
    '''
    def __init__(self, parent=None):
        '''
        @exists: flag used to determine whether or not the popup menu for the GSV change
                            should register or not (specific to copy/paste of a node)
        '''
        super(VariableManagerGSVMenu, self).__init__(parent)
        self.main_widget = getMainWidget(self)
        self.populate()
        self.setSelectionChangedEmitEvent(self.checkUserInput)
        self.currentIndexChanged.connect(self.indexChanged)

    def populate(self):
        """
        Populate the model with all of the graph state variables.

        This will add the additional value of an empty string to start the list.
        This empty string is meant to be the default value when a user
        creates a VariableManager so that it can start at a default state,
        rather than selecting the first GSV and populating that.
        """
        model = QtGui.QStandardItemModel()
        variable_list = [''] + [x.getName() for x in NodegraphAPI.GetNode('rootNode').getParameter('variables').getChildren()]
        for i, variable_name in enumerate(variable_list):
            item = QtGui.QStandardItem(variable_name)
            model.setItem(i, 0, item)

        self.setModel(model)
        self.setModelColumn(0)

    def update(self):
        """
        Updates the model items with all of the graph state variables.

        This is very similair to the populate call, except that with this, it
        will remove all of the items except for the current one.  Which
        will ensure that an indexChanged event is not registered thus
        updating the UI.
        """
        variable = self.currentText()
        variables = NodegraphAPI.GetNode('rootNode').getParameter('variables').getChildren()
        variable_list = [x.getName() for x in variables]
        model = self.model()
        """
        # remove all items
        for i in reversed(range(model.rowCount())):
            item = model.item(i, 0)
            model.takeRow(item.row())

        # add items
        for variable in variable_list:
            item = QtGui.QStandardItem(variable)
            model.insertRow(model.rowCount(), item)

        # remove blank space...
        if str(self.currentText()) != '':
            item = model.findItems('', QtCore.Qt.MatchExactly)
            if len(item) > 0:
                    current_row = model.indexFromItem(item[0]).row()
                    model.takeRow(current_row)

        # set current item
        self.setExistsFlag(False)
        self.setCurrentIndexToText(variable)
        # add items
        """
        # remove all items except current one
        for i in reversed(range(model.rowCount())):
            item = model.item(i, 0)
            variable = item.text()
            if variable != str(self.currentText()):
                model.takeRow(item.row())

        # add items
        for variable in variable_list:
            if variable != str(self.currentText()):
                item = QtGui.QStandardItem(variable)
                model.insertRow(model.rowCount(), item)

        # remove blank space...
        if str(self.currentText()) != '':
            item = model.findItems('', QtCore.Qt.MatchExactly)
            if len(item) > 0:
                    current_row = model.indexFromItem(item[0]).row()
                    model.takeRow(current_row)

    """ UTILS """
    def checkUserInput(self):
        """
        Checks the user input to determine if it is a valid option
        in the current model.  If it is not this will create a brand
        spanking new GSV for the user.
        """
        does_node_variable_exist = self.isUserInputValid()
        if does_node_variable_exist is False:
            self.setExistsFlag(False)
            self.createNewGSV(str(self.currentText()))
            self.setExistsFlag(True)
            return

    def gsvChanged(self):
        """
        When the user changes the GSV and accepts the change,
        this function will be triggered.
        """
        # get attributes
        variable_browser = self.main_widget.variable_manager_widget.variable_browser
        variable = str(self.currentText())
        previous_variable = self.main_widget.getVariable()
        node = self.main_widget.getNode()
        publish_dir = node.getParameter('publish_dir').getValue(0)
        """
        add items
        display versions to load
        determine if this should display the versions popup for the user
        or if this should automatically create the v000
        """
        publish_loc = '%s/%s/%s' % (publish_dir, variable, 'patterns/master/block/v000')

        # if the directory exists
        if os.path.exists(publish_loc) is True:
            self.main_widget.setVariable(variable)
            node.getParameter('variable').setValue(variable, 0)
            # need to update / create master item here...
            self.main_widget.versions_display_widget.update(
                column=2, gui=True, previous_variable=previous_variable
            )
            # if not cancelled...
        else:
            # if doesnt exist
            # publish
            self.main_widget.setVariable(variable)
            node.getParameter('variable').setValue(variable, 0)

            # create new directories
            if not os.path.exists(publish_dir):
                os.mkdir(publish_dir)

            if not os.path.exists(publish_dir + '/%s' % variable):
                os.mkdir(publish_dir + '/%s' % variable)
                os.mkdir(publish_dir + '/%s/blocks' % variable)
                os.mkdir(publish_dir + '/%s/patterns' % variable)

            # populate
            variable_browser.reset()
            node._reset(variable=variable)
            variable_browser.populate()
            self.main_widget.updateOptionsList()

            # set attributes
            item = variable_browser.topLevelItem(0)
            variable_browser.setCurrentItem(item)
            self.main_widget.setWorkingItem(item)
            variable_browser.showMiniNodeGraph()

            initial_publish_display_text = "BLOCK  (  {variable}  |  v000  )".format(variable=variable)
            self.main_widget.publish_display_widget.update(name=initial_publish_display_text, publish_type=BLOCK_ITEM)
            self.main_widget.publish_display_widget.display()

        self.main_widget.setVariable(variable)
        if self.main_widget.node_type == '<multi>':
            self.main_widget.variable_manager_widget.variable_browser.showMiniNodeGraph()

    def createNewGSV(self, gsv):
        '''
        Creates a new GSV in the project settings.

        Args:
            gsv (str) the name of the GSV to add
        '''
        variablesGroup = NodegraphAPI.GetRootNode().getParameter('variables')
        variableParam = variablesGroup.createChildGroup(gsv)
        variableParam.createChildNumber('enable', 1)
        variableParam.createChildString('value', '')
        variableParam.createChildStringArray('options', 0)
        return variableParam.getName()

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
                def cancel():
                    self.setExistsFlag(False)
                    self.setCurrentIndexToText(self.main_widget.getVariable())
                    self.setExistsFlag(True)
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
                self.main_widget.showWarningBox(warning_text, self.gsvChanged, cancel, detailed_warning_text)

        elif self.getExistsFlag() is False:
            self.setCurrentIndexToText(self.main_widget.getVariable())
            self.setExistsFlag(True)


class VariableManagerNodeMenu(AbstractComboBox):
    def __init__(self, parent=None):
        super(VariableManagerNodeMenu, self).__init__(parent)
        self.main_widget = getMainWidget(self)
        self.populate()
        self.update()
        self.setSelectionChangedEmitEvent(self.checkUserInput)
        self.currentIndexChanged.connect(self.indexChanged)

    def checkUserInput(self):
        """
        Checks the user input to determine if it is a valid option
        in the current model.  If it is not this will reset the menu
        back to the previous option
        """
        does_node_variable_exist = self.isUserInputValid()
        if does_node_variable_exist is False:
            self.setExistsFlag(False)
            node_type = self.main_widget.node.getParameter('node_type').getValue(0)
            self.setCurrentIndexToText(node_type)
            self.setExistsFlag(True)
            return

    def populate(self):
        """
        adds all of the items to the model widget
        adds color to the items
        """

        model = QtGui.QStandardItemModel()
        variable_list = ['', '<multi>'] + NodegraphAPI.GetNodeTypes()
        for i, variable_name in enumerate(variable_list):
            item = QtGui.QStandardItem(variable_name)
            model.setItem(i, 0, item)
        self.setModel(model)
        self.setModelColumn(0)

    def indexChanged(self):
        # check to see if user input is valid, if not valid, exit
        """
        # without this it randomly allows the user to change to a
        # new node type =\
        """
        # return if this node type does not exist
        if self.currentText() not in NodegraphAPI.GetNodeTypes():
            return

        if self.getExistsFlag() is True:
            def accept():
                if hasattr(self.main_widget.variable_manager_widget, 'variable_browser'):
                    variable_browser = self.main_widget.variable_manager_widget.variable_browser
                    Utils.UndoStack.OpenGroup('Variable Manager | Node Type Changed')

                    variable = self.main_widget.getVariable()
                    node = self.main_widget.getNode()

                    node.getParameter('node_type').setValue(str(self.currentText()), 0)
                    self.main_widget.setNodeType(str(self.currentText()))

                    variable_browser.reset()
                    node._reset(variable=variable)
                    variable_browser.populate()
                    self.main_widget.updateOptionsList()

                    Utils.UndoStack.CloseGroup()

            def cancel():
                self.setExistsFlag(False)
                node_type = self.main_widget.node.getParameter('node_type').getValue(0)
                self.setCurrentIndexToText(node_type)

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
            self.main_widget.showWarningBox(warning_text, accept, cancel, detailed_warning_text)


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
        self.head.sectionClicked.connect(self.__createUserBlockItem)
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
        root_item.setFlags(root_flags ^ QtCore.Qt.ItemIsDropEnabled)

        # setup signals / events
        self.itemCollapsed.connect(self.itemCollapsedEvent)
        self.itemExpanded.connect(self.itemExpandedEvent)
        self.itemChanged.connect(self.itemNameChanged)
        # create all items
        self.populate()

    """ UTILS """
    def getAllRootNodes(self, item, vs_node_list=[]):
        if item:
            if item.getRootNode().getParameter('nodeReference.vs_node'):
                vs_node_list.append(item.getRootNode())
            return self.getAllRootNodes(item.parent(), vs_node_list)
        else:
            return vs_node_list

    def createDirectories(self, variable_dir=None, publish_dir=None):
        """
        Creates the directories associated with a specific item.
        This should probably accept the arg <item> instead of
        the strings...
        """
        # create null directories
        if variable_dir:
            if not os.path.exists(variable_dir):
                os.mkdir(variable_dir)
                os.mkdir(variable_dir+'/patterns')
                os.mkdir(variable_dir+'/blocks')

        # create default master dirs
        if publish_dir:
            if not os.path.exists(publish_dir):
                dir_list = ['pattern', 'block']
                mkdirRecursive(publish_dir)
                for dir_item in dir_list:
                    mkdirRecursive(publish_dir + '/%s/live' % dir_item)

    def reset(self):
        """
        Deletes all of the top level items in.  This is essentially
        clearing the state of the browser so that it can be repopulated.
        """
        for index in reversed(range(self.topLevelItemCount())):
                self.takeTopLevelItem(index)

    def reparentItem(self, item, new_parent_item, index=0):
        """
        Reparents an item from its current parent to the provided parent.

        Args:
            item (VariableManagerBrowserItem): item to have its parent set.
            new_parent_item (VariableManagerBrowserItem): Item to be
                parented to.
        """
        old_parent_item = item.parent()

        old_parent_item.takeChild(old_parent_item.indexOfChild(item))
        new_parent_item.insertChild(index, item)

    def populate(self):
        def populateBlock(root_item, child):
            """
            recursive statement to search through all
            nodes and create the items for those nodes
            """
            root_node = NodegraphAPI.GetNode(child.getValue(0))
            # create pattern item
            if root_node.getParameter('type').getValue(0) == 'pattern':
                version = root_node.getParameter('version').getValue(0)
                unique_hash = root_node.getParameter('hash').getValue(0)
                pattern = root_node.getParameter('pattern').getValue(0)

                VariableManagerBrowserItem(
                    root_item,
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
        root_dir = self.main_widget.getRootPublishDir()

        """
        To Do:
            variable != ''
                repeated... because the directories need to exist to
                create the master item?  Do I need to be repeating
                this?
        """
        # do stuff if variable is empty/unassigned/iniatlizing
        if variable != '':
            variable_dir = '{root_dir}/{variable}'.format(root_dir=root_dir, variable=variable)
            publish_dir = variable_dir + '/patterns/master'

            # create directories
            self.createDirectories(variable_dir=variable_dir, publish_dir=publish_dir)

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
        """
        # disconnect node
        self.__unwireNode(item, item.parent())

        # delete node
        item.getRootNode().delete()

        # remove item
        child_index = item.parent().indexOfChild(item)
        item.parent().takeChild(child_index)

    def __wireNode(self, item, new_parent_item, new_index):
        """
        Reconnects the node to the new parents internal node network and
        creates the new references on the block group.

        Args:
            item (VariableManagerBrowserItem): The item that is currently
                being moved around.
            new_parent (VariableManagerBrowserItem): The parent item
                that has had an item moved under it.
            new_index (int): The new index of the child for the
                new parent.
        """
        node = item.getRootNode()
        # reconnect node
        node_list = []
        for index in range(new_parent_item.childCount()):
            child_item = new_parent_item.child(index)
            node_list.append(child_item.getRootNode())
        node_list.insert(new_index, node)

        # connect children
        self.main_widget.getNode().connectInsideGroup(node_list, new_parent_item.getBlockNode())

        # add node reference
        self.__addNodeReference(item, new_parent_item, new_index)

    def __unwireNode(self, item, old_parent_item):
        """
        Disconnects the node and removes all referencing/linking
        to its existing parent

        Args:
            node (Root Node):  The items root node
            old_block_node (Block Node): The items previous parents
                block node.
        """
        # get nodes
        node = item.getRootNode()

        # get ports
        """
        Massive duck typing hack to get around issue in the
        dropOnPattern --> __createUserBlockItem
            due to the fact that it has to create at origin every time...
            so... it will disconenct the last node... which will cause it
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
        for input_port in node.getInputPorts():
            output_ports = input_port.getConnectedPorts()
            for port in output_ports:
                port.disconnect(input_port)

        self.__removeNodeReference(item, old_parent_item)

    def __removeNodeReference(self, item, old_parent_item):
        """
        Dereferences the item from the old parent item.

        Args:
            item (VariableManagerBrowserItem): item to be dereferenced
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

        self.main_widget.getNode().createNodeReference(
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
            self, root_node=master_root_node,
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

    def __createNewBlockItem(self):
        """
        Creates a new block item, which is a container for
        holding patterns in a GSV.

        This is called by the createNewBrowserItem method

        return (VariableManagerBrowserItem)
        """
        # gather variables for item creation
        node = self.main_widget.getNode()
        parent_node, parent_item, current_pos = self.__getNewItemSetupAttributes()

        # create node group
        block_node = node.createBlockRootNode(parent_node, name='New_Block')

        # connect and align nodes
        self.__setupNodes(block_node, parent_node, current_pos)

        # Get Nodes
        new_block_node = NodegraphAPI.GetNode(block_node.getParameter('nodeReference.block_group').getValue(0))
        pattern_node = NodegraphAPI.GetNode(block_node.getParameter('nodeReference.pattern_node').getValue(0))

        # Create Item

        block_item = VariableManagerBrowserItem(
            parent_item,
            block_node=new_block_node,
            expanded=False,
            item_type=BLOCK_ITEM,
            name=block_node.getName(),
            pattern_node=pattern_node,
            veg_node=pattern_node.getChildByIndex(0),
            root_node=block_node
        )

        # Set Parameters
        block_node.getParameter('version').setValue(block_item.block_version, 0)
        block_node.getParameter('hash').setValue(str(block_item.getHash()), 0)

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
            return self.__createNewBlockItem()

        elif item_type == PATTERN_ITEM:
            return self.__createNewPatternItem(item_text)

        elif item_type == MASTER_ITEM:
            return self.__createNewMasterItem()

    """ PROPERTIES """
    def setItem(self, item):
        self.item = item

    def getItem(self):
        return self.item

    """ DROP EVENTS """
    def __moveItem(self, item, new_parent_item, old_parent_item, new_index):
        """
        Moves all of the nodes for an item to a new location in the hierarchy.
        This will also reset all of the node expressions for linking.

        Args:
            item (VariableManagerBrowserItem): The item that is currently
                being moved around.
            new_parent_item (VariableManagerBrowserItem): The new parent item
                that has had an item moved under it.
            old_parent (VariableManagerBrowserItem): The previous parent item
                that has had an item moved under it.
            new_index (int): The new index of the child for the
                new parent.
        """

        node = item.getRootNode()

        old_parent_node = old_parent_item.getRootNode()

        new_parent_node = new_parent_item.getRootNode()
        new_block_node = new_parent_item.getBlockNode()

        # reset node parent
        self.__unwireNode(item, old_parent_item)
        node.setParent(new_block_node)
        self.__wireNode(item, new_parent_item, new_index)

        # update variable switches
        self.main_widget.updateAllVariableSwitches(old_parent_node)
        self.main_widget.updateAllVariableSwitches(new_parent_node)

    def __dropOnBlockEvent(self, dropped_item, old_parent, new_parent, new_index):
        """
        This is what happens when the user drops an item
        onto a block.  This will do all of the internal rewiring
        of the node that was dropped

        Args:
            dropped_item (ITEM): The item that is being dropped
            old_parent (VariableManagerBrowserItem): The dropped items
                old parent (BLOCK_ITEM)
            new_parent (VariableManagerBrowserItem): The dropped items
                new parent (BLOCK_ITEM)
        """

        self.__moveItem(dropped_item, new_parent, old_parent, new_index)
        new_parent.setExpanded(True)

        if dropped_item.getItemType() == BLOCK_ITEM:
            string_expanded = dropped_item.getRootNode().getParameter('expanded').getValue(0)
            expanded = convertStringBoolToBool(string_expanded)
            dropped_item.setExpanded(expanded)

    def __dropOnPatternEvent(self, dropped_item, old_parent, new_parent, item_dropped_on, new_index):
        """
        This is what happens when the user drops an item
        onto a pattern.  This will do all of the internal rewiring,
        node creation, and reparenting.

        Args:
            dropped_item (ITEM): The item that is being dropped
            old_parent (VariableManagerBrowserItem): The dropped items
                old parent (BLOCK_ITEM)
            new_parent (VariableManagerBrowserItem): The dropped items
                new parent (BLOCK_ITEM)
            item_dropped_on (PATTERN_ITEM): the item that has recieved
                the drop event.
            new_index (int): The current index of the item that has been dropped on
        """
        if dropped_item.getItemType() == PATTERN_ITEM:
            # create new block and setup node hierarchy
            new_block_item = self.__createUserBlockItem(item_dropped_on)
            self.__moveItem(new_block_item, new_parent, new_block_item.parent(), new_index)
            self.reparentItem(new_block_item, new_parent, index=new_index)

            # move dropped node under new block item
            self.reparentItem(dropped_item, new_block_item)
            self.__moveItem(dropped_item, new_block_item, old_parent, 0)

            # set expanded
            new_block_item.setExpanded(True)

        elif dropped_item.getItemType() == BLOCK_ITEM:
            # move / rewire nodes
            self.__moveItem(dropped_item, new_parent, old_parent, new_index)
            self.__moveItem(item_dropped_on, dropped_item, new_parent, 0)

            # reparent items...
            self.reparentItem(dropped_item, new_parent, index=new_index)
            self.reparentItem(item_dropped_on, dropped_item, 0)

            # set expanded
            dropped_item.setExpanded(True)

        return

    def dropEvent(self, event, *args, **kwargs):
        """
        on drop of the item, it will disconnect/reconnect it and reposition
        all of the nodes inside...
        """

        # get pre resolve attrs
        drop_type = self.dropIndicatorPosition()
        DROP_ON = 0
        dropped_item = self.currentItem()
        old_parent = dropped_item.parent()
        item_dropped_on = self.itemAt(event.pos())

        # Dropped on an item
        if drop_type == DROP_ON:
            # dropped on pattern
            if item_dropped_on.getItemType() == PATTERN_ITEM:
                new_parent = item_dropped_on.parent()
                new_index = new_parent.indexOfChild(item_dropped_on)
                self.__dropOnPatternEvent(dropped_item, old_parent, new_parent, item_dropped_on, new_index)
                return
            # dropped on block
            else:
                return_val = super(VariableManagerBrowser, self).dropEvent(event, *args, **kwargs)
                new_parent = dropped_item.parent()
                new_index = new_parent.indexOfChild(dropped_item)
                # drop on block item
                if new_parent == item_dropped_on:
                    self.__dropOnBlockEvent(dropped_item, old_parent, new_parent, new_index)

        # Dropped inbetween items
        else:
            return_val = super(VariableManagerBrowser, self).dropEvent(event, *args, **kwargs)
            new_parent = dropped_item.parent()
            new_index = new_parent.indexOfChild(dropped_item)
            self.__dropOnBlockEvent(dropped_item, old_parent, new_parent, new_index)

        # return drop event
        return return_val

    """ DISPLAY EVENTS """
    def hideMiniNodeGraph(self):
        """
        When the user sets the Node Type to anything but <multi>
        this will hide the mini nodegraph.

        Currently this is a massive hack... because Katana explodes
        when I try to do a proper widget create/destroy event... =(
        """
        # kinda hacky... to fix copy/paste error
        """
        To Do:
            Figure out what's going on with copy/paste.  When <multi>
            is note used as the node_type, for some reason the
            variable_manager_widget does not exist... potentially it is
            either destroyed or never created?
        """
        variable_manager_widget = self.main_widget.variable_manager_widget
        variable_manager_widget.variable_splitter.setStyleSheet(
            SPLITTER_STYLE_SHEET_HIDE
        )
        # this is really stupid
        variable_manager_widget.variable_splitter.moveSplitter(100000, 1)
        """ disabling this for now... because it breaks when setting """
        # variable_manager_widget.variable_splitter.setHandleWidth(0)
        '''
        variable_manager_widget.variable_splitter.setHandleWidth(
            settings.SPLITTER_HANDLE_WIDTH
        )
        '''
        nodegraph_tab = variable_manager_widget.nodegraph_tab

        # nodegraph_tab.setFixedWidth(0)
        nodegraph_tab.hide()

    def showMiniNodeGraph(self):
        """
        If the Node Type is set to <multi> by the user.  This will enable it
        so that when a user cilcks on a new item, the mini node graph
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
                goToNode(node, frame=True, nodegraph_tab=nodegraph_tab)

                # resize splitter to let user know that they can do this now...
                variable_manager_widget.variable_splitter.setHandleWidth(
                    SPLITTER_HANDLE_WIDTH
                )

                variable_manager_widget.variable_splitter.setStyleSheet(
                    SPLITTER_STYLE_SHEET
                )
                if nodegraph_tab.isVisible() is False:
                    variable_manager_widget.variable_splitter.moveSplitter(self.width() * 0.7, 1)
                    nodegraph_tab.show()

        except AttributeError:
            # On init of the node, pass because the
            # variable_manager_widget doest not exist yet
            pass

    def showItemParameters(self):
        """
        Shows the parameters of the current item if it
        is not of type <multi>.
        """
        if self.currentItem():
            node = self.currentItem().getVEGNode().getChildByIndex(0)
            self.main_widget.populateParameters(node_list=[node])

    """ RMB EVENTS """
    def __createUserBlockItem(self, item=None):
        """
        Creates a new user block item.

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
                self.__moveItem(item, new_parent_item, old_parent_item, 0)
                # move block to patterns old location
                new_grandparent_item = new_parent_item.parent()
                self.__moveItem(new_parent_item, new_grandparent_item, new_grandparent_item, index)
                new_grandparent_item.takeChild(new_grandparent_item.childCount()-1)
                new_grandparent_item.insertChild(index, new_parent_item)

                # expand new group
                new_parent_item.setExpanded(True)

        return new_parent_item

    def contextMenuEvent(self, event):
        """
        popup menu created when the rmb is hit - has a submethod
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
                    item = self.currentItem()
                    self.__createUserBlockItem(item=item)

            # Publish item
            elif 'Publish' in action.text():
                item = self.main_widget.getWorkingItem()
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
        action = menu.exec_(QtGui.QCursor.pos())
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
        if item:
            if item.getItemType() == BLOCK_ITEM:
                index = self.currentIndex()
                if index.column() == 0:
                    name = item.text(0)
                    root_node = item.getRootNode()
                    updateNodeName(root_node, name=name)

    def itemCollapsedEvent(self, item, *args, **kwargs):
        if item.getRootNode().getParameter('expanded'):
            item.getRootNode().getParameter('expanded').setValue('False', 0)

    def itemExpandedEvent(self, item, *args, **kwargs):
        if item.getRootNode().getParameter('expanded'):
            item.getRootNode().getParameter('expanded').setValue('True', 0)

    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            item = self.currentItem()
            if item.getItemType() != MASTER_ITEM:
                self.__deleteItem(item)
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
                        previous_variable=previous_variable
                    )

            return QTreeWidget.mouseReleaseEvent(self, event, *args, **kwargs)

    def selectionChanged(self, *args, **kwargs):
        """
        displays the current group that is editable in a mini-node graph
        """
        if hasattr(self.main_widget, 'variable_manager_widget'):
            self.main_widget.setWorkingItem(self.currentItem())
            if self.main_widget.getNodeType() == '<multi>':
                self.showMiniNodeGraph()
            else:
                self.hideMiniNodeGraph()
                self.showItemParameters()
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

    Notes:
        For Pattern Node:
            Root Node = Group node at top of pattern node
            Block Node = Group node at top of pattern node (same as root node)
            Pattern Node = VEG node
    """
    def __init__(
        self,
        parent,
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

        self.setItemType(item_type)
        self.pattern_node = pattern_node
        self.root_node = root_node
        self.block_node = block_node
        self.setVEGNode(veg_node)
        self.block_version = block_version
        self.pattern_version = pattern_version
        self.setExpanded(expanded)
        self.hash = self.createPublishDir(unique_hash=unique_hash)

        if item_type == BLOCK_ITEM:
            self.setFlags(
                self.flags()
                | QtCore.Qt.ItemIsEditable
            )
        elif item_type == PATTERN_ITEM:
            self.setFlags(
                self.flags()
                | QtCore.Qt.ItemIsDropEnabled
                | QtCore.Qt.ItemIsDragEnabled
            )

        # update text
        self.setText(0, name)
        self.setText(1, pattern_version)
        self.setText(2, block_version)

    def createPublishDir(self, unique_hash=None):
        """
        creates all directories on disk to be used when
        a new item is created (pattern) returns the unique hash
        """
        def checkHash(thash, location):
            thash = int(math.fabs(hash(str(thash))))

            if str(thash) in os.listdir(location):
                thash = int(math.fabs(hash(str(thash))))
                return checkHash(str(thash), location)
            return thash
        main_widget = getMainWidget(self.treeWidget())
        root_node = main_widget.node

        variable = main_widget.getVariable()

        if self.getItemType() == BLOCK_ITEM:
            location = root_node.getParameter('publish_dir').getValue(0) + '/%s/blocks'%variable

        elif self.getItemType() in [MASTER_ITEM, PATTERN_ITEM]:
            location = root_node.getParameter('publish_dir').getValue(0) + '/%s/patterns'%variable

        if unique_hash:
            self.hash = unique_hash
        else:
            self.hash = hash(self.pattern_node.getName())
            self.hash = checkHash(self.hash, location)
            """
            TODO:
                not sure if I need publish...
            """
            # dir_list = ['pattern', 'block', 'publish']
            dir_list = ['pattern', 'block']
            block_location = '%s/%s' % (location, self.hash)
            os.mkdir(block_location)
            for dir_item in dir_list:
                os.mkdir(block_location + '/%s' % dir_item)
                os.mkdir(block_location + '/%s/live' % dir_item)

        self.publish_dir = '%s/%s' % (location, self.hash)
        return self.hash

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
