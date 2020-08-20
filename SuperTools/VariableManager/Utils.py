import os

from PyQt5.QtWidgets import (
    QComboBox, QLineEdit, QCompleter, QWidget,
    QHBoxLayout, QPushButton, QSizePolicy,
    QLabel, QVBoxLayout
)
from PyQt5.QtGui import (
    QMovie
)
from PyQt5 import QtCore

from Settings import (
    ACCEPT_GIF,
    CANCEL_GIF,
    MAYBE_COLOR_RGBA,
    ACCEPT_COLOR_RGBA,
    CANCEL_COLOR_RGBA
)
from PyQt5.Qt import QApplication


class GifPlayer(QWidget):
    def __init__(
        self,
        gifFile,
        hover_color,
        parent=None
    ):
        super(GifPlayer, self).__init__(parent)

        QVBoxLayout(self)
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.hover_color = repr(hover_color)
        self.style_sheet = self.styleSheet()

        # create movie widget
        self.movie_widget = QLabel()
        self.layout().addWidget(self.movie_widget)

        self.movie_widget.movie = QMovie(gifFile, QtCore.QByteArray(), self.movie_widget)
        self.movie_widget.movie.setScaledSize(QtCore.QSize(100, 300))
        self.movie_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.movie_widget.setAlignment(QtCore.Qt.AlignTop)
        # start movie
        self.movie_widget.movie.setCacheMode(QMovie.CacheAll)
        self.movie_widget.setMovie(self.movie_widget.movie)
        self.movie_widget.movie.start()
        self.movie_widget.movie.loopCount()

    def updateStyleSheet(self):
        """
        Updates the color on the style sheet, as it appears
        this is caching the values into the stylesheet.  Rather
        than dynamically calling them =\
        """
        self.movie.setStyleSheet(
            """
            QLabel::hover{
                border-color: rgba%s;
            }
            """ % (
                    self.hover_color
                )
            )

    """ EVENTS """
    def setMousePressAction(self, action):
        self._action = action

    def mousePressEvent(self, *args, **kwargs):
        self._action()
        return QWidget.mousePressEvent(self, *args, **kwargs)

    def resizeEvent(self, *args, **kwargs):
        height = self.movie_widget.movie.scaledSize().height()
        self.movie_widget.setFixedHeight(height)
        return QWidget.resizeEvent(self, *args, **kwargs)

    def enterEvent(self, *args, **kwargs):
        self.setStyleSheet(
            """
            border: 5px solid;
            border-color: rgba%s;
            """ % (
                    self.hover_color
                )
            )
        return QWidget.enterEvent(self, *args, **kwargs)

    def leaveEvent(self, *args, **kwargs):
        self.setStyleSheet(self.style_sheet)
        return QWidget.leaveEvent(self, *args, **kwargs)

    """ PROPERTIES """
    @property
    def hover_color(self):
        return self._hover_color

    @hover_color.setter
    def hover_color(self, hover_color):
        self._hover_color = hover_color


class AbstractUserBooleanWidget(QWidget):
    """
    Abstract widget that will require user input of
    Accepting / Canceling the current event that
    is proposed to them.

    The event can be accepted/denied with the buttons
    to the left/right of the widget, or with the esc / enter/return keys.

    Args:
        central_widget (QWidget): Central widget to be displayed
            to the user.  Can also be set with setCentralWidget.
        button_width (int): The width of the accept/cancel buttons.
    Widgets:
        accept_button (QPushButton): When pressed, accepts the
            current event registered with setAcceptEvent.
        cancel_button (QPushButton): When pressed, cancels the
            current event registered with setCancelEvent.
        central_widget (QWidget): The central widget to be displayed
            to the user.
    """
    def __init__(self, parent=None, central_widget=None, button_width=None):
        super(AbstractUserBooleanWidget, self).__init__(parent)
        self.main_widget = getMainWidget(self)

        # Create main layout
        QHBoxLayout(self)

        # create text layout
        if not central_widget:
            self.central_widget = QWidget()

        # create accept / cancel widgets
        """
        self.accept_button = QPushButton('=>')
        self.cancel_button = QPushButton('<=')
        self.accept_button.clicked.connect(self.acceptPressed)
        self.cancel_button.clicked.connect(self.cancelPressed)
        """
        self.accept_button = GifPlayer(ACCEPT_GIF, hover_color=ACCEPT_COLOR_RGBA)
        self.cancel_button = GifPlayer(CANCEL_GIF, hover_color=CANCEL_COLOR_RGBA)
        self.accept_button.setMousePressAction(self.acceptPressed)
        self.cancel_button.setMousePressAction(self.cancelPressed)

        # setup accept / cancel widgets
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.accept_button.setSizePolicy(size_policy)
        self.cancel_button.setSizePolicy(size_policy)
        self.setupButtonTooltips()

        # set up main layout
        self.layout().addWidget(self.cancel_button, 1)
        self.layout().addWidget(self.central_widget)
        self.layout().addWidget(self.accept_button, 1)

        self.layout().setAlignment(QtCore.Qt.AlignTop)

        # set default button size
        if not button_width:
            self.setButtonWidth(100)

    def setupButtonTooltips(self):
        """
        Creates the tooltips for the user on how to use these buttons
        when they hover over the widget.
        """
        self.accept_button.setToolTip("""
The happy af dog bouncing around that has a massive
green border around it when you hover over it means to continue.

FYI:
You can also hit <ENTER> and <RETURN> to continue...
        """)
        self.cancel_button.setToolTip("""
The super sad dog who looks really sad with the massive red border
around it when you hover over it means to go back...

FYI:
You can also hit <ESCAPE> to go back...
        """)
        self.setStyleSheet("""
            QToolTip {
                background-color: black;
                color: white;
                border: black solid 1px
            }"""
        )

    def setButtonWidth(self, width):
        """
        Sets the accept/cancel buttons to a fixed width...
        """
        self.accept_button.setFixedWidth(width)
        self.cancel_button.setFixedWidth(width)

    """ PROPERTIES """
    def setCentralWidget(self, central_widget):
        self.layout().itemAt(1).widget().setParent(None)
        self.layout().insertWidget(1, central_widget)
        self.central_widget = central_widget

    def getCentralWidget(self):
        return self.central_widget

    """ EVENTS """
    def setAcceptEvent(self, accept):
        self._accept = accept

    def setCancelEvent(self, cancel):
        self._cancel = cancel

    def acceptPressed(self):
        self.main_widget.layout().setCurrentIndex(0)
        self._accept()

    def cancelPressed(self):
        self.main_widget.layout().setCurrentIndex(0)
        self._cancel()

    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancelPressed()
        elif event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self.acceptPressed()
        return QWidget.keyPressEvent(self, event, *args, **kwargs)


class AbstractComboBox(QComboBox):
    """
    A custom QComboBox with a completer / model.  This is
    designed to be an abstract class that will be inherited by the
    the GSV and Node ComboBoxes

    Attributes:
        exists (bool) flag used to determine whether or not the popup menu
            for the menu change should register or not (specific to copy/paste
            of a node.

            In plain english... this flag is toggled to hide the Warning PopUp Box
            from displaying to the user in some events.
        previous_text (str): the previous items text.  This is stored for cancel events
            and allowing the user to return to the previous item after cancelling.
    """
    def __init__(self, parent=None):
        super(AbstractComboBox, self).__init__(parent)
        self.main_widget = self.parent()
        self.current_text = ''
        self.setExistsFlag(True)

        # setup line edit
        self.line_edit = QLineEdit("Select & Focus", self)
        self.line_edit.editingFinished.connect(self.userFinishedEditing)
        self.setLineEdit(self.line_edit)

        self.setEditable(True)

        # setup completer
        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.setPopup(self.view())
        self.setCompleter(self.completer)
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)

    def userFinishedEditing(self):
        is_input_valid = self.isUserInputValid()
        if is_input_valid:
            self.__selectionChangedEmit()
            self._previous_text = self.currentText()
        else:
            self.setCurrentIndexToText(self.currentText())

    def setCurrentIndexToText(self, text):
        """
        Sets the current index to the text provided.  If no
        match can be found, this will default back to the
        first index.

        If no first index... create '' ?
        """
        self.setExistsFlag(False)

        # get all matches
        items = self.model().findItems(text, QtCore.Qt.MatchExactly)

        # set to index of match
        if len(items) > 0:
            index = self.model().indexFromItem(items[0]).row()
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(0)
        self._previous_text = self.currentText()
        self.setExistsFlag(True)

    def setExistsFlag(self, exists):
        self._exists = exists

    def getExistsFlag(self):
        return self._exists

    def setModel(self, model):
        super(AbstractComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(AbstractComboBox, self).setModelColumn(column)

    def view(self):
        return self.completer.popup()

    """ UTILS """
    def isUserInputValid(self):
        """
        Determines if the new user input is currently
        in the model.

        Returns True if this is an existing item, Returns
        false if it is not.
        """
        items = self.model().findItems(self.currentText(), QtCore.Qt.MatchExactly)
        if len(items) > 0:
            return True
        else:
            return False

    def __selectionChangedEmit(self):
        pass

    def setSelectionChangedEmitEvent(self, method):
        """
        sets the method for the selection changed emit call
        this will be called everytime the user hits enter/return
        inside of the line edits as a way of sending an emit
        signal from the current text changed (finalized) before
        input changed event...
        """
        self.__selectionChangedEmit = method

    """ EVENTS """
    def event(self, event, *args, **kwargs):
        """
        Registering key presses in here as for some reason
        they don't work in the keyPressEvent method...
        """
        if event.type() == QtCore.QEvent.KeyPress:
            modifiers = QApplication.keyboardModifiers()
            if event.key() == QtCore.Qt.Key_Tab:
                if modifiers == QtCore.Qt.ShiftModifier:
                    self.previous_completion()
                else:
                    self.next_completion()

                return True

            elif event.key() in [
                QtCore.Qt.Key_Return,
                QtCore.Qt.Key_Enter,
                QtCore.Qt.Key_Down
            ]:
                self.__selectionChangedEmit()

        return QComboBox.event(self, event, *args, **kwargs)

    def next_completion(self):
        row = self.completer.currentRow()
        if not self.completer.setCurrentRow(row + 1):
            self.completer.setCurrentRow(0)
        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)

    def previous_completion(self):
        row = self.completer.currentRow()
        numRows = self.completer.completionCount()
        if not self.completer.setCurrentRow(row - 1):
            self.completer.setCurrentRow(numRows-1)
        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)


def connectInsideGroup(node_list, parent_node):
    """
    Connects all of the nodes inside of a specific node in a linear fashion

    Args:
        node_list (list): list of nodes to be connected together, the order
            of the nodes in this list, will be the order that they are connected in
        parent_node (node): node have the nodes from the node_list
            wired into.
    """
    import NodegraphAPI
    send_port = parent_node.getSendPort('in')
    return_port = parent_node.getReturnPort('out')
    if len(node_list) == 0:
        send_port.connect(return_port)
    elif len(node_list) == 1:
        node_list[0].getOutputPortByIndex(0).connect(return_port)
        node_list[0].getInputPortByIndex(0).connect(send_port)
    elif len(node_list) == 2:
        node_list[0].getInputPortByIndex(0).connect(send_port)
        node_list[1].getOutputPortByIndex(0).connect(return_port)
        node_list[0].getOutputPortByIndex(0).connect(node_list[1].getInputPortByIndex(0))
        NodegraphAPI.SetNodePosition(node_list[0], (0, 100))
    elif len(node_list) > 2:
        for index, node in enumerate(node_list[:-1]):
            node.getOutputPortByIndex(0).connect(node_list[index+1].getInputPortByIndex(0))
            NodegraphAPI.SetNodePosition(node, (0, index * -100))
        node_list[0].getInputPortByIndex(0).connect(send_port)
        node_list[-1].getOutputPortByIndex(0).connect(return_port)
        NodegraphAPI.SetNodePosition(node_list[-1], (0, len(node_list) * -100))


def convertStringBoolToBool(string_bool):
    """
    Converts a string boolean to a boolean

    Args:
        string_bool (str): string value of the boolean
            such as "True" or "False"

    Returns (bool)
    """
    if string_bool == "True":
        return True
    elif string_bool == "False":
        return False
    else:
        return False


def createNodeReference(node_ref, param_name, param=None, node=None, index=-1):
    """
    Creates a new string parameter whose expression value
    returns a reference to a node.

    Args:
        node_ref (node): the node to be referenced
        param_name (str): the name of the new parameter to create
    Kwargs:
        node (node): node to create parameter on if param kwarg
            param is not provided
        param (group param): the param to create the new parameter as
            a child of
    Returns (string param)
    """
    if not param:
        param = node.getParameters()
    new_param = param.createChildString(param_name, '', index)
    new_param.setExpressionFlag(True)
    new_param.setExpression('@%s' % node_ref.getName())
    return new_param


def disconnectNode(node, input=False, output=False):
    """
    Disconnects the node provide from all over nodes.  The same
    as hitting 'x' on the keyboard... or "Extract Nodes" except this
    is in the NodegraphWidget, not the NodegraphAPI. so kinda hard
    to call... so I made my own...

    Args:
        node (node): Node to be extracted
        input (bool): If true disconnect all input ports
        output (bool): If true disconnect all output ports

    """
    if input is True:
        for input_port in node.getInputPorts():
            output_ports = input_port.getConnectedPorts()
            for port in output_ports:
                port.disconnect(input_port)

    if output is True:
        for output in node.getOutputPorts():
            input_ports = output.getConnectedPorts()
            for port in input_ports:
                port.disconnect(output)


def mkdirRecursive(path):
    """
    Creates a directory and all parent directories leading
    to that directory.  This is not as necessary in Python 3.x+
    as you can do stuff like os.mkdirs.

    Args:
        path (str): directory to be created
    """
    sub_path = os.path.dirname(path)
    if not os.path.exists(sub_path):
        mkdirRecursive(sub_path)
    if not os.path.exists(path):
        os.mkdir(path)


def goToNode(node, frame=False, nodegraph_tab=None):
    """
    Changes the nodegraph to the selected items node,
    if it is not a group node, then it goes to its parent
    as the parent must be a group... (hopefully)

    Args:
        node (node): node to go to

    Kwargs:
        frame (bool): if True will frame all of the nodes inside of the "node" arg
        nodegraph_tab (nodegraph_panel): if exists, will frame in this node graph, if there is no
            node graph tab.  Then it will search for the default node graph.
    """
    from Katana import UI4
    if not nodegraph_tab:
        nodegraph_tab = UI4.App.Tabs.FindTopTab('Node Graph')
    nodegraph_tab._NodegraphPanel__navigationToolbarCallback(node.getName(), 'useless')

    if frame is True:
        nodegraph_widget = nodegraph_tab.getNodeGraphWidget()
        nodegraph_widget.frameNodes(nodegraph_tab.getEnteredGroupNode().getChildren())


def getMainWidget(widget):
    try:
        name = widget.__name__()
        if name == 'VariableManagerMainWidget':
            return widget
        else:
            return getMainWidget(widget.parent())
    except AttributeError:
        return getMainWidget(widget.parent())


def getNextVersion(location):
    """
    Args:
        location (str): path on disk to to publish dir

    return (str): A string of the next version with the format of v000
    """
    versions = os.listdir(location)
    if 'live' in versions:
        versions.remove('live')

    if len(versions) == 0:
        next_version = 'v000'
    else:
        versions = [int(version[1:]) for version in versions]
        next_version = 'v'+str(sorted(versions)[-1] + 1).zfill(3)

    return next_version


def makeUndoozable(func, node, _action_string, _undo_type, *args, **kwargs):
    """
    This will encapsulate the function as an undo stack.

    Args:
        func (function): the function to encapsulate as an undoable operation
        undo_string (str): the name of the undo operation to be displayed
        node (node): the main node ie self.node
            This is a massive hack to register undo operations

    """
    # start recording undo operation
    Utils.UndoStack.OpenGroup(
        "{node} | {undo_type} | {action}".format(
            node=node.getName(),
            undo_type=_undo_type,
            action=_action_string
        )
    )

    # register operation hack...
    if Utils.UndoStack.IsUndoEnabled():
        node.getParameter('undoozable').setValue('my oh my what a hack1', 0)

    # do stuff
    func(*args, **kwargs)

    # register operation hack...
    if Utils.UndoStack.IsUndoEnabled():
        node.getParameter('undoozable').setValue('my oh my what a hack2', 0)

    # stop recording
    Utils.UndoStack.CloseGroup()

    # disable capture for remaining updates
    Utils.UndoStack.DisableCapture()
    Utils.EventModule.ProcessAllEvents()
    Utils.UndoStack.EnableCapture()

# HACK
def transferNodeReferences(xfer_from, xfer_to):
    """
    Transfer the node references from one node to another.

    xfer_from (param): the nodeReference param to transfer FROM
    xfer_to  (param): the nodeReference param to transfer TO

    """
    import NodegraphAPI
    # transfer node refs
    for param in xfer_from.getChildren():
        param_name = param.getName()
        node_ref = NodegraphAPI.GetNode(param.getValue(0))
        createNodeReference(
            node_ref, param_name, param=xfer_to
        )


def updateNodeName(node, name=None):
    """
    updates the nodes name.  If a name is provided
    then this will update it to that name.  If not, it will
    merely check to ensure that no funky digits have
    been automatically added to this nodes name...

    Kwarg:
        name (str): name to update to
    """
    # set name
    if name:
        node.setName(str(name))
        node.getParameter('name').setValue(str(name), 0)
    else:
        # update name
        node.setName(node.getName())
        node.getParameter('name').setValue(node.getName(), 0)


from Katana import Utils
Utils.EventModule.RegisterEventHandler(updateNodeName, '_update_node_name')