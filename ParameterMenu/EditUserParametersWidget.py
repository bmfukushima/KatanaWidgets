"""
TODO:
    Display:
        * Custom Widgets
                l.828 --> __updateAllDynamicArgsWidgets
        * Conditional Vis/Locking...
            Need to add this...
    Create New:
        * Ramp ( Color | Float )

Args
    _DEFAULT_SEPARATOR_LENGTH = 4
    _DEFAULT_SEPARATOR_WIDTH = 1
    _DEFAULT_LABEL_LENGTH = 125
Widgets:
    UserParametersMainWidget (QWidget)
        | --  QVBoxLayout
            | --  create_new_parameter_widget (ListInputWidget)
                    When the user selects an input in this list, a new parameter
                    will be created and added to the ShojiModelViewWidget
                    displaying all of the parameters in an hierichical fashion
            | --  user_parameters_widget (UserParametersWidget --> ShojiModelViewWidget)
                    Main view displaying the parameters on this node.
                | --  (UserParametersDynamicWidget --> ShojiLayout)
                        Main display area.  When a user clicks on an item in the TreeView
                        this widget will dynamically update to display the available widgets
                        to manipulate the parameter to the user.
                    | --  default_args_widget (FrameInputWidgetContainer)
                            Display the default args that are available on all parameters
                            to the user.  These args are:
                                widget (Widget Type)
                                label (Display Name)
                                readOnly (Locked)
                        | -*  ( DynamicArgsInputWidget --> LabelledInputWidget )
                    | --  widget_specific_args_widget (FrameInputWidgetContainer)
                            Displays the args that are unique to a specific widget type.
                            If there are no args available for this parameter type, this
                            widget will be hidden.
                        | -*  ( DynamicArgsInputWidget --> LabelledInputWidget )
                    | --  help_text_widget (LabelledInputWidget)
                            Displays the help text to the user.

"""
import json
import ast

from qtpy.QtWidgets import QLabel, QWidget, QVBoxLayout, QPlainTextEdit
from qtpy.QtGui import QCursor
from qtpy.QtCore import QModelIndex, Qt

from cgwidgets.widgets import (
    ShojiLayout,
    ShojiModelViewWidget,
    ListInputWidget,
    LabelledInputWidget,
    OverlayInputWidget,
    FrameInputWidgetContainer,
    StringInputWidget,
    BooleanInputWidget,
    PlainTextInputWidget
)
from cgwidgets.views import AbstractDragDropTreeView
from cgwidgets.utils import getWidgetAncestor
from cgwidgets.settings import attrs
from Katana import UniqueName, PyXmlIO

_DEFAULT_SEPARATOR_LENGTH = 4
_DEFAULT_SEPARATOR_WIDTH = 1
_DEFAULT_LABEL_LENGTH = 125

class UserParametersMainWidget(QWidget):
    """
    The main widget (top level) widget that is displayed to the user.
    """
    BASE_TYPES = [
        "Number",
        "String",
        "Group",
        "Number Array",
        "String Array",
        "Float Vector",
        "Color (RGB)",
        "Color (RGBA)",
        "Color Ramp",
        "Float Ramp",
        "Button",
        "Toolbar",
        "TeleParameter",
        "Node Drop Proxy"
    ]
    STRING_TYPES = [
        "Default",
        "Scene Graph Location",
        "Attribute Name",
        "Attribute Type",
        "CEL Statement",
        "Resolution",
        "Asset",
        "File Path",
        "Boolean",
        "Popup Menu",
        "Mapping Popup Menu",
        "Script Button",
        "Check Box",
        "TeleParameter",
        "Script Editor"
    ]
    NUMBER_TYPES = [
        "Boolean",
        "Popup Menu",
        "Mapping Popup Menu",
        "Check Box"
    ]
    GROUP_TYPES = [
        "Multi",
        "Gradient"
    ]
    STRING_ARRAY_TYPES = [
        "Scene Graph Locations"
    ]
    NUMBER_ARRAY_TYPES = [
        "Color"
    ]
    DISPLAY_NAMES = {
        'User Params Editor': 'userParamsEditor',
        'Scene Graph Location': 'scenegraphLocation',
        'Attribute Name': 'attributeName',
        'Attribute Type': 'attributeType',
        'Asset': 'assetIdInput',
        'File Path': 'fileInput',
        'Resolution': 'resolution',
        'Color': 'color',
        'CEL Statement': 'cel',
        'Scene Graph Locations': 'scenegraphLocationArray',
        'Boolean': 'boolean',
        'Popup Menu': 'popup',
        'Mapping Popup Menu': 'mapper',
        'Script Button': 'scriptButton',
        'Check Box': 'checkBox',
        'Multi': 'multi',
        'Gradient': 'linearGradient',
        'TeleParameter': 'teleparam',
        'Script Editor': 'scriptEditor',
        'Null': 'null',
        'Default': 'default'
    }
    REVERSE_DISPLAY_NAMES = {}
    for key in DISPLAY_NAMES:
        value = DISPLAY_NAMES[key]
        REVERSE_DISPLAY_NAMES[value] = key

    WIDGET_SPECIFIC_OPTIONS = {
        'popup': (
            'options',),
        'assetIdInput': (
            'assetScope', 'context', 'assetTypeTags', 'fileTypes', 'forcefile'),
        'mapper': (
            'options', 'options__order'),
        'color': (
            'color_enableFilmlookVis', 'color_restrictComponents'),
        'scriptButton': (
            'scriptText', 'text'),
        'scriptToolbar': (
            'scriptToolbar', 'buttonData')}

    HINT_OPTIONS_MAP = {
        "Widget Type": "widget",
        "Display Name": "label",
        "Locked": "readOnly",
        "Options": "options",
        "Options Order": "options__order",
        "Script Text": "scriptText",
        "Text": "text",
        "Script Toolbar": "scriptToolbar",
        "Button Data": "buttonData",
        "Help": "help"
    }
    REVERSE_HINT_OPTIONS_MAP = {}
    for key in HINT_OPTIONS_MAP:
        value = HINT_OPTIONS_MAP[key]
        REVERSE_HINT_OPTIONS_MAP[value] = key

    # 'assetIdInput': (
    #     'assetScope', 'context', 'assetTypeTags', 'fileTypes', 'forcefile'),
    #
    # 'color': (
    #     'color_enableFilmlookVis', 'color_restrictComponents'),
    def __init__(self, parent=None, node=None):
        super(UserParametersMainWidget, self).__init__(parent)

        self._node = node
        # create widgets
        QVBoxLayout(self)
        self.user_parameters_widget = UserParametersWidget(node=node)
        self.create_new_parameter_widget = CreateNewParameterWidget(self)
        self.create_new_parameter_widget.setUserFinishedEditingEvent(self.__createNewParameter)

        self.user_parameters_widget.addHeaderDelegateWidget([Qt.Key_Q], self.create_new_parameter_widget, focus=True)
        # add widgets to layout

        self.layout().addWidget(self.user_parameters_widget)

    def node(self):
        return self._node

    """ CREATE NEW PARAMETER"""
    def __createNewParameter(self, widget, value):
        """
        Creates a new parameter.  This is run every time the self.create_new_parameter_widget widget
        has accepted a user input.
        """
        param_type = value
        print('param type == ', param_type)
        # preflight
        if param_type not in UserParametersMainWidget.BASE_TYPES: return
        if param_type == '': return

        # get parent param
        # nothing selected
        if len(self.__getSelectedIndexes()) == 0:
            parent_index = QModelIndex()
            parent_param = self.node().getParameters()
        # something selected...
        else:
            # if not top level param selected
            parent_index = self.__getParentIndex()
            if parent_index.internalPointer():
                parent_param = parent_index.internalPointer().columnData()['parameter']
            else:
                parent_param = self.node().getParameters()

        # create child parameter
        param = self.__createChildParameter(param_type, parent_param)

        # insert shoji widget
        insertion_row = len(parent_param.getChildren()) - 1
        self.user_parameters_widget.createNewParameterIndex(insertion_row, param, parent_index)

        # reset text
        self.previous_text = ''
        self.create_new_parameter_widget.setText('')
        print("finish")

    def __createChildParameter(self, param_type, parent):
        """
        Creates a new parameter based of the type/parent provided

        Run when the user has finished editing the self.create_new_parameter_widget widget.
        This will create a new parameter if the specified type is valid.
        "Float Vector",
        "Color (RGB)",
        "Color (RGBA)",
        "Color Ramp",
        "Float Ramp",
        "Button",
        "Toolbar",
        "TeleParameter",
        "Node Drop Proxy"""

        # TODO Setup for all parameter types...
        if param_type == "Number":
            param = parent.createChildNumber(param_type, 0)
        elif param_type == "Number Array":
            param = parent.createChildNumberArray(param_type, 2)
        elif param_type == "String":
            param = parent.createChildString(param_type, '')
        elif param_type == "String Array":
            param = parent.createChildStringArray(param_type, 2)
        elif param_type == "Group":
            param = parent.createChildGroup(param_type)
        elif param_type == "Float Vector":
            param_name = UniqueName.GetUniqueName('Float Vector', parent.getChild)
            element = PyXmlIO.Element('floatvector_parameter')
            element.setAttr('name', param_name)
            param = parent.createChildXmlIO(element)
        elif param_type == "Color (RGB)":
            param = self.__createArrayParam(param_type, 'number', 3, hints={'widget': 'color'}, parent=parent)
        elif param_type == "Color (RGBA)":
            param = self.__createArrayParam(param_type, 'number', 4, hints={'widget': 'color'}, parent=parent)
        # elif param_type == "Color Ramp":
        #     # todo add support
        #     param = pass
        # elif param_type == "Float Ramp":
        #     # todo add support
        #     param = pass
        elif param_type == "Button":
            param = parent.createChildString(param_type, '')
            hints = {'widget': 'scriptButton'}
            param.setHintString(repr(hints))
        elif param_type == "Toolbar":
            param = parent.createChildString(param_type, '')
            hints = {'widget': 'scriptToolbar', 'buttonData': [{'text': 'button1'}, {'text': 'button2'}]}
            param.setHintString(repr(hints))
        elif param_type == "TeleParameter":
            param = parent.createChildString(param_type, '')
            hints = {'widget': 'teleparam'}
            param.setHintString(repr(hints))
        elif param_type == "Node Drop Proxy":
            param = parent.createChildString(param_type, '')
            hints = {'widget': 'nodeDropProxy'}
            param.setHintString(repr(hints))
        return param

    def __getParentIndex(self):
        """
        Returns the parent parameter for creating new parameters.

        This will be based off of the currently selected item.  If it is a group, it will
        return that.  If not, it will return the parameters parent.

        # TODO needs to register for top level params, and return the
            node.getParameters()

        Returns (item)
        """
        # get selected items
        selected_index = self.__getSelectedIndexes()[0]
        selected_item = selected_index.internalPointer()

        # get selected parameter
        selected_param = selected_item.columnData()['parameter']

        # check parameter type
        if selected_param.getType() != "group":
            parent_index = selected_index.parent()
        else:
            parent_index = selected_index

        # return
        return parent_index

    def __getSelectedIndexes(self):
        """
        Gets all of the currently selected indexes.

        TODO:
            move this to the abstract class to be called...
        """
        selection = self.user_parameters_widget.headerWidget().selectionModel().selectedIndexes()
        selected_indexes = [index for index in selection if index.column() is 0]
        return selected_indexes

    def __createArrayParam(self, param_type, input_type, array_length, value=0, hints=None, parent=None):
        """
        Creates a parameter an XML parameter.

        Args:
            input_type (str): value of the type of input that is expected.  These values
                can be:
                    number | string
            array_length (int): length of the array

        Note:
            This code is based on the UserParameters.__buildArrayStructure located at
            UI4.FormMaster.Editors.UserParameters import UserParametersEditor

            But for obvious reasons, I'm not going to copy/paste that into here *derp*
        """

        param_name = UniqueName.GetUniqueName(param_type, parent.getChild)
        element = PyXmlIO.Element('%sarray_parameter' % input_type)
        element.setAttr('name', param_name)
        element.setAttr('size', array_length)   # no idea why this is here
        element.setAttr('tupleSize', array_length)
        if hints:
            element.setAttr('hints', repr(hints))

        # not sure why this is here... but it seems to only be valid for RGB?
        for i in range(0, 3):
            child = element.addChild(PyXmlIO.Element('%s_parameter' % input_type))
            child.setAttr('name', 'i%i' % i)
            child.setAttr('value', value)

        # create and return new param
        new_param = parent.createChildXmlIO(element)
        return new_param


class UserParametersWidget(ShojiModelViewWidget):
    """
    The main widget for the user edit parameters widget.  This will handle
    all of the parameter interface for drag/dropping, deleting, etc.
    """
    def __init__(self, parent=None, node=None):
        super(UserParametersWidget, self).__init__(parent)
        self._node = node

        # create view
        header_widget = AbstractDragDropTreeView()

        # setup header
        self.setHeaderViewWidget(header_widget)
        self.setHeaderData(['name', 'base type'])
        self.setHeaderPosition(attrs.WEST, attrs.SOUTH)
        #self.setIsDelegateHeaderShown(False)
        self.setDelegateTitleIsShown(False)

        # setup flags
        self.setHeaderItemIsEnableable(False)
        #self.setHeaderItemIsRootDroppable(False)
        self.setHeaderItemIsEditable(True)

        # set custom delegate
        self.setDelegateType(
            ShojiModelViewWidget.DYNAMIC,
            dynamic_widget=UserParametersDynamicWidget,
            dynamic_function=UserParametersDynamicWidget.updateGUI
        )

        # populate parameters
        self.__populate(self._node)

        # set up event
        self.setHeaderItemDropEvent(self.paramDropEvent)
        self.setHeaderItemTextChangedEvent(self.paramNameChangedEvent)
        self.setHeaderItemDeleteEvent(self.paramDeleteEvent)

    def __populate(self, node):
        # get node
        parameters = node.getParameters().getChildren()
        for index, parameter in enumerate(parameters):
            self.__populateParameters(index, parameter)

    def __populateParameters(self, row, parameter, parent=QModelIndex()):
        """
        Recursive function to create a new item for every parameter.  Note that this
        is meant to be called from __populate in order to initialize from the root level.

        Args:
            index (int): row to be inserted at
            parameter (Parameter): Katana parameter information
            parent (QModelIndex): Parent index to create new items under
        """
        new_index = self.createNewParameterIndex(row, parameter, parent)

        # if group
        if parameter.getType() == 'group':
            new_index.internalPointer().setIsDroppable(True)
            children = parameter.getChildren()
            for row, child in enumerate(children):
                self.__populateParameters(row, child, parent=new_index)

    def createNewParameterIndex(self, row, parameter, parent):
        """
        Creates a new parameter index in the shoji widget

        Returns (QModelIndex)
        """
        # get attrs
        name = parameter.getName()
        column_data = {'name': name, 'base type': parameter.getType(), 'parameter': parameter}

        # update hints
        hint_string = parameter.getHintString()
        if hint_string:
            hint_string = ast.literal_eval(hint_string)
            for arg in list(hint_string.keys()):
                column_data[arg] = hint_string[arg]

        # create index
        new_model_index = self.insertShojiWidget(row, column_data=column_data, parent=parent)

        # setup drops
        if parameter.getType() == "group":
            new_model_index.internalPointer().setIsDroppable(True)
        else:
            new_model_index.internalPointer().setIsDroppable(False)

        return new_model_index

    def node(self):
        return self._node

    """ EVENTS """
    def paramDropEvent(self, data, items_dropped, model, row, parent):
        """
        When a user drag/drops an item (parameter).  This will be triggered
        to update the hierarchy of that parameter.
        """
        # get parent dropped on
        try:
            new_parent_param = parent.columnData()['parameter']
        except KeyError:
            #todo keep an eye on this...
            new_parent_param = self.node().getParameters()

        # move all selected parameters
        for item in items_dropped:
            param = item.columnData()['parameter']
            current_parent_param = param.getParent()

            if current_parent_param:
                param_name = UniqueName.GetUniqueName(param.getName(), new_parent_param.getChild)
                # convert param to xml
                param_xml = param.buildXmlIO()
                param_xml.setAttr('name', param_name)

                # delete old param
                current_parent_param.deleteChild(param)

                # create new param
                new_param = new_parent_param.createChildXmlIO(param_xml)
                new_parent_param.reorderChild(new_param, row)

                # update item meta data
                item.columnData()['name'] = param_name
                item.columnData()['parameter'] = new_param

    def paramNameChangedEvent(self, item, old_value, new_value):
        param = item.columnData()['parameter']
        param_name = UniqueName.GetUniqueName(new_value, param.getParent().getChild)
        param.setName(param_name)
        item.columnData()['name'] = param_name

    def paramDeleteEvent(self, item):
        param = item.columnData()['parameter']
        param.getParent().deleteChild(param)


class DynamicArgsInputWidget(LabelledInputWidget):
    """
    One individual arg
    """
    def __init__(self, parent=None, name='', note='', delegate_widget=None, delegate_constructor=None):
        super(DynamicArgsInputWidget, self).__init__(parent, name=name, delegate_widget=delegate_widget, delegate_constructor=delegate_constructor)
        # setup args
        self.arg = name
        self.setToolTip(note)
        self.setUserFinishedEditingEvent(self.userInputEvent)
        self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)
        self.setResizeSlidersOnWidgetResize(True)
        # # setup alignment
        # self.layout().setAlignment(Qt.AlignTop)

    def setText(self, text):
        self.delegateWidget().setText(text)

    def text(self):
        return self.delegateWidget().text()

    def userInputEvent(self, widget, value):
        """
        When the user inputs something into the arg, this event is triggered
        updating the model item
        """
        user_parameters_widget = getWidgetAncestor(self, UserParametersDynamicWidget)
        hint_name = UserParametersMainWidget.HINT_OPTIONS_MAP[self.arg]
        user_parameters_widget.item().columnData()[hint_name] = str(value)
        user_parameters_widget.updateWidgetHint()


class UserParametersDynamicWidget(ShojiLayout):
    """
    Dynamic widget that is updated/displayed every time a user clicks
    on an item.
    - widget type
    - widget options
    - conditional visibility
    - help text
    Args:
        baseType (UserParametersMainWidget.BASE_TYPE): type of the
            basic parameter before any stylesheet are applied
        widgetType (UserParametersMainWidget.WIDGET_TYPE): type of
            widget applied to the basic parameter
    """
    NON_HINTSTRING_ARGS = ['name', 'base type', 'parameter']
    DEFAULT_HINTSTRING_ARGS = ['readOnly', 'label', 'widget', 'help']

    def __init__(self, parent=None):
        super(UserParametersDynamicWidget, self).__init__(parent)

        self.unique_widgets_dict = {}

        # create default args
        self.default_args_widget = self.createDefaultArgsWidget()
        self.default_args_widget.setSeparatorLength(200)
        self.default_args_widget.setSeparatorWidth(_DEFAULT_SEPARATOR_WIDTH)

        # create widget specific args
        self.widget_specific_args_widget = FrameInputWidgetContainer(self, title='Unique Args', direction=Qt.Vertical)
        self.widget_specific_args_widget.layout().setAlignment(Qt.AlignTop)
        self.widget_specific_args_widget.setSeparatorLength(200)
        self.widget_specific_args_widget.setSeparatorWidth(_DEFAULT_SEPARATOR_WIDTH)

        # add widgets to layout
        self.addWidget(self.default_args_widget)
        self.addWidget(self.widget_specific_args_widget)

    def createDefaultArgsWidget(self):
        """
        Creates all of the widgets for the default args

        Creates all of the default args widgets, the default args are ones that
        happen on every single parameter.  These options are:
            Display Name --> label
            Widget Type --> widget
            Locked --> readOnly

        Returns (FrameInputWidgetContainer)
        """
        default_args_widget = FrameInputWidgetContainer(self, title='Default Args', direction=Qt.Vertical)
        default_args_widget.layout().setAlignment(Qt.AlignTop)

        # setup widget type
        widget_type_frame = DynamicArgsInputWidget(None, name='Widget Type', note='', delegate_widget=ListInputWidget(self))
        self.widget_type = widget_type_frame.delegateWidget()
        self.widget_type.dynamic_update = True
        self.widget_type.setCleanItemsFunction(self.getWidgetTypeList)
        self.widget_type.setUserFinishedEditingEvent(self.setWidgetTypeEvent)

        # setup default args
        # TODO wtf does constant do... ['constant', 'label', 'readOnly']

        # Display Name
        display_name_frame = DynamicArgsInputWidget(
            None,
            name='Display Name',
            note='The parameter name to be displayed to the user.',
            delegate_widget=StringInputWidget(self)
        )

        self.display_name_widget = display_name_frame.delegateWidget()

        # Read Only
        read_only_frame = DynamicArgsInputWidget(
            None,
            name='Locked',
            note='If True, this widget will be lock and in a read only state.  If False, the user will be able to manipulate this parameter',
            delegate_widget=BooleanInputWidget(self)
        )
        self.read_only_widget = read_only_frame.delegateWidget()

        # Help Text
        help_text_frame = DynamicArgsInputWidget(
            None,
            name='Help',
            note='Help text to be displayed to the user',
            delegate_widget=PlainTextInputWidget(self)
        )
        self.help_text_widget = help_text_frame.delegateWidget()

        # add widgets to layout
        default_args_widget.addInputWidget(widget_type_frame)
        default_args_widget.addInputWidget(display_name_frame)
        default_args_widget.addInputWidget(read_only_frame)
        default_args_widget.addInputWidget(help_text_frame)

        # create widget dict
        self.widgets_dict = {}
        self.widgets_dict['widget'] = self.widget_type
        self.widgets_dict['readOnly'] = self.read_only_widget
        self.widgets_dict['label'] = self.display_name_widget
        self.widgets_dict['help'] = self.help_text_widget

        # setup default sizes
        for key in self.widgets_dict:
            widget = self.widgets_dict[key]
            frame_widget = widget.parent().parent()
            frame_widget.setDefaultLabelLength(_DEFAULT_LABEL_LENGTH)
            frame_widget.setHandleLength(_DEFAULT_SEPARATOR_LENGTH)
            frame_widget.setHandleWidth(_DEFAULT_SEPARATOR_WIDTH)

        return default_args_widget

    """ HINT OPTIONS"""
    # widget type
    def setWidgetTypeEvent(self, widget, value):
        """
        sets the widget type

        Args:
            widget (widget): Widget that is currently setting the value
            value (value): value that is currently being set

        """
        # reset item hint string
        self.resetItemToDefaultState(reset_default_hints=False)

        # set widget type
        try:
            self.item().columnData()['widget'] = UserParametersMainWidget.DISPLAY_NAMES[str(value)]

            # create default hint string values
            widget_hint_options = self.getWidgetSpecificHintOptions()
            for option in widget_hint_options:
                self.item().columnData()[option] = ''

            # update
            self.updateWidgetHint()
            self.__updateAllDynamicArgsWidgets()

        except KeyError:
            # cannot find the key in the params
            pass

    def getWidgetTypeList(self):
        """ Returns a list of widget types depending on the current input type """
        widget_list = []
        input_type = self.baseType()
        # todo append "Default"
        if input_type == "string":
            widget_list += UserParametersMainWidget.STRING_TYPES
        if input_type == "number":
            widget_list += UserParametersMainWidget.NUMBER_TYPES
        if input_type == "stringArray":
            widget_list += UserParametersMainWidget.STRING_ARRAY_TYPES
        if input_type == "numberArray":
            widget_list += UserParametersMainWidget.NUMBER_ARRAY_TYPES
        if input_type == "group":
            widget_list += UserParametersMainWidget.GROUP_TYPES
        # todo null appending multiple times
        widget_list.append('Null')

        # returns a widget list in the format for the list widget
        _widget_list = [[widget] for widget in sorted(widget_list)]
        return _widget_list

    def mapWidgetTypeToUserReadable(self, widget_type):
        """
        Converts the widget type display name, from katana readable to human readable

        Takes the hint string readable widget value, and maps it to the human
        readable value.  This essentially flips the dictionary located in
        UserParametersMainWidget.DISPLAY_NAMES

        Args:
            widget_type (str): hint string readable name of the type of widget
        """
        widget_types = self.getWidgetTypeList()
        for user_arg in widget_types:
            user_arg = user_arg[0]
            try:
                hint_arg = UserParametersMainWidget.DISPLAY_NAMES[user_arg]
                if hint_arg == widget_type:
                    return user_arg
            except KeyError: pass
        return ''

    # widget specific options
    def getWidgetSpecificHintOptions(self):
        """
        Returns a list of all of the available hint options that are specific to the
        current items widget type.
        """
        try:
            hint_options = UserParametersMainWidget.WIDGET_SPECIFIC_OPTIONS[self.getWidgetType()]
        except KeyError:
            hint_options = []
        return hint_options

    """ PROPERTIES """
    def baseType(self):
        try:
            return self.item().columnData()['base type']
        except KeyError:
            return None

    def getWidgetType(self):
        try:
            return self.item().columnData()['widget']
        except KeyError:
            return None

    def item(self):
        return self._item

    def setItem(self, _item):
        self._item = _item

    def resetItemToDefaultState(self, reset_default_hints=True):
        """
        Clears the hint string on the current item.
        """
        data = self.item().columnData()

        # update dictionary
        for arg in list(data.keys()):
            if arg not in UserParametersDynamicWidget.NON_HINTSTRING_ARGS:
                if reset_default_hints is True:
                    data.pop(arg)
                else:
                    if arg not in UserParametersDynamicWidget.DEFAULT_HINTSTRING_ARGS:
                        data.pop(arg)

    """ Widget Hint"""
    def getWidgetHint(self):
        """
        Get the widget hint here that was created by all of the items'

        Returns (dict)
        """
        # get attrs
        data = self.item().columnData()

        # update dictionary
        widget_hint = {}
        for arg in list(data.keys()):
            if arg not in UserParametersDynamicWidget.NON_HINTSTRING_ARGS:
                widget_hint[arg] = data[arg]

        # return
        return widget_hint

    def updateWidgetHint(self):
        """
        Updates the parameters widget hint with the new user settings

        Note:
            This needs to be called every time the user updates a parameter.

        ToDo
            Does base item need
                * args?
                * update signal?
        """
        hint = self.getWidgetHint()
        param = self.item().columnData()['parameter']
        param.setHintString(repr(hint))

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        parent (ShojiModelViewWidget)
        widget (ShojiModelDelegateWidget)
        item (ShojiModelItem)
        self --> widget.getMainWidget()
        """

        if not widget: return
        if not item: return
        # get attrs
        self = widget.getMainWidget()
        self.setItem(item)
        hint_string = item.columnData()['parameter'].getHintString()

        # preflight
        if not hint_string:
            self.widget_specific_args_widget.hide()
            return

        # update
        # get hints
        hints = ast.literal_eval(hint_string)

        # update default default args
        for hint in list(hints.keys()):
            if hint in UserParametersDynamicWidget.DEFAULT_HINTSTRING_ARGS:
                hint_widget = self.widgets_dict[hint]
                value = hints[hint]

                # special cases
                # if there is a display name / actual value...
                if hint == "widget":
                    value = UserParametersMainWidget.REVERSE_DISPLAY_NAMES[str(value)]

                # boolean
                if isinstance(hint_widget, BooleanInputWidget):
                    if value in ['True', 1]:
                        hint_widget.is_clicked = True
                    else:
                        hint_widget.is_clicked = False
                else:
                    hint_widget.setText(value)

        self.__updateAllDynamicArgsWidgets()

    def __updateAllDynamicArgsWidgets(self):
        """
        Deletes all of the input widgets that are from hints that are
        specific to the current widget type.  Then it creates all
        of the new input widgets based off of the new widget type.

        This should be run every time a user selects a new index.
        """

        # show widget
        self.widget_specific_args_widget.show()

        # get hints available
        unique_hints = self.getWidgetSpecificHintOptions()

        # delete widget specific args
        for widget_name in list(self.unique_widgets_dict.keys()):
            hint_widget = self.unique_widgets_dict[widget_name]
            hint_widget.parent().setParent(None)
            hint_widget.parent().deleteLater()
            self.unique_widgets_dict.pop(widget_name)

        # create widget specific args
        self.unique_widgets_dict = {}

        if len(unique_hints) == 0:
            self.widget_specific_args_widget.hide()
        else:
            for unique_hint in unique_hints:
                # TODO Set up custom widgets here...
                # create widget
                display_name = UserParametersMainWidget.REVERSE_HINT_OPTIONS_MAP[unique_hint]

                # TODO Fail here...
                new_widget = DynamicArgsInputWidget(
                    None,
                    name=display_name,
                    delegate_constructor=StringInputWidget
                )

                # TODO End Fail here...

                # set up default lengths
                new_widget.setDefaultLabelLength(_DEFAULT_LABEL_LENGTH)
                new_widget.setSeparatorLength(_DEFAULT_SEPARATOR_LENGTH)
                new_widget.setSeparatorWidth(_DEFAULT_SEPARATOR_WIDTH)

                # add widget to layout
                input_widget = new_widget.delegateWidget()

                # todo this needs to be more robust...
                # needs to also work with the updateGUI value setter...
                # how to support multiple widget types though?
                # use setValue?
                # set value
                try:
                    value = self.item().columnData()[unique_hint]
                    input_widget.setText(value)
                except:
                    pass
                self.unique_widgets_dict[unique_hint] = input_widget

                self.widget_specific_args_widget.addInputWidget(new_widget)


class CreateNewParameterWidget(ListInputWidget):
    """
    Delegate responsible for displaying the widget types that are a available for the user to create.
    """
    def __init__(self, parent=None):
        super(CreateNewParameterWidget, self).__init__(parent)
        param_types_list = [[param_type] for param_type in sorted(UserParametersMainWidget.BASE_TYPES)]
        self.populate(param_types_list)

#if __name__ == "__main__":
node = NodegraphAPI.GetAllSelectedNodes()[0]
widget = UserParametersMainWidget(node=node)
widget.resize(500, 500)
widget.show()
widget.move(QCursor.pos())