"""
TODO:
    Display:
        * Create param value display
                - widget type
                - widget options
                - conditional visibility
                - help text
    Create New:
        *
"""

from qtpy.QtWidgets import QLabel, QWidget, QVBoxLayout
from qtpy.QtGui import QCursor
from qtpy.QtCore import QModelIndex

from cgwidgets.widgets import TansuModelViewWidget, TansuHeaderTreeView, ListInputWidget
from cgwidgets.utils import attrs

from Katana import UniqueName, PyXmlIO
from UI4.FormMaster.Editors.UserParameters import UserParametersEditor


class EditUserParametersMainWidget(QWidget):
    TYPES = [
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
        "Attribute Name"
    ]

    def __init__(self, parent=None, node=None):
        super(EditUserParametersMainWidget, self).__init__(parent)

        self.node = node
        # create widgets
        QVBoxLayout(self)
        self.main_widget = EditUserParametersWidget(node=node)

        param_types_list = [[param_type] for param_type in EditUserParametersMainWidget.TYPES]
        self.new_parameter = ListInputWidget(self, item_list=param_types_list)
        self.new_parameter.setUserFinishedEditingEvent(self.__createNewParameter)

        # add widgets to layout
        self.layout().addWidget(self.new_parameter)
        self.layout().addWidget(self.main_widget)

    """ CREATE NEW PARAMETER"""
    def __createNewParameter(self, widget, value):
        """
        Creates a new parameter.  This is run every time the self.new_parameter widget
        has accepted a user input.
        """
        param_type = value

        # preflight
        if param_type not in EditUserParametersMainWidget.TYPES: return

        # get parent param
        if len(self.__getSelectedIndexes()) == 0:
            parent_index = QModelIndex()
            parent_param = self.node.getParameters()
        else:
            parent_index = self.__getParentIndex()
            parent_param = parent_index.internalPointer().columnData()['parameter']

        # create child parameter
        param = self.__createChildParameter(param_type, parent_param)

        # insert tansu widget
        insertion_row = len(parent_param.getChildren()) - 1
        self.main_widget.createNewParameterIndex(insertion_row, param, parent_index)

        # reset text
        self.new_parameter.setText('')

    def __createChildParameter(self, param_type, parent):
        """
        Run when the user has finished editing the self.new_parameter widget.
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
        elif param_type == "Color Ramp":
            # todo add support
            param =
        elif param_type == "Float Ramp":
            # todo add support
            param =
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
        Returns the parent parameter for creating new parameters.  This
        will be based off of the currently selected item.  If it is a group, it will
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
        selection = self.main_widget.headerWidget().selectionModel().selectedIndexes()
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


class EditUserParametersDisplayWidget(QLabel):
    """
    Dynamic widget that is updated/displayed every time a user clicks
    on an item.
    """
    def __init__(self, parent=None):
        super(EditUserParametersDisplayWidget, self).__init__(parent)

    @staticmethod
    def updateGUI(parent, widget, item):
        """
        parent (TansuModelViewWidget)
        widget (TansuModelDelegateWidget)
        item (TansuModelItem)
        self --> widget.getMainWidget()
        """
        #print('custom event')
        #print(parent, widget, item)
        this = widget.getMainWidget()
        this.setText(item.columnData()['name'])


class EditUserParametersWidget(TansuModelViewWidget):
    """
    The main widget for the user edit parameters widget.  This will handle
    all of the parameter interface for drag/dropping, deleting, etc.
    """
    def __init__(self, parent=None, node=None):
        super(EditUserParametersWidget, self).__init__(parent)
        self.node = node

        # create view
        header_widget = TansuHeaderTreeView()

        # setup header
        self.setHeaderWidget(header_widget)
        self.setHeaderData(['name', 'type'])
        self.setHeaderPosition(attrs.WEST)

        # setup flags
        self.setHeaderItemIsEnableable(False)
        self.setHeaderItemIsRootDropEnabled(False)

        # set custom delegate
        self.setDelegateType(
            TansuModelViewWidget.DYNAMIC,
            dynamic_widget=EditUserParametersDisplayWidget,
            dynamic_function=EditUserParametersDisplayWidget.updateGUI
        )

        # populate parameters
        self.__populate(self.node)

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
            new_index.internalPointer().setIsDropEnabled(True)
            children = parameter.getChildren()
            for row, child in enumerate(children):
                self.__populateParameters(row, child, parent=new_index)

    def createNewParameterIndex(self, row, parameter, parent):
        """
        Creates a new parameter index in the tansu widget

        Returns (QModelIndex)
        """
        # get attrs
        name = parameter.getName()
        column_data = {'name': name, 'type': parameter.getType(), 'parameter': parameter}

        # create index
        new_model_index = self.insertTansuWidget(row, column_data=column_data, parent=parent)

        # disable drops
        new_model_index.internalPointer().setIsDropEnabled(False)

        return new_model_index

    """ EVENTS """
    def paramDropEvent(self, row, item_list, parent):
        """
        When a user drag/drops an item (parameter).  This will be triggered
        to update the hierarchy of that parameter.
        """
        # get parent dropped on
        try:
            new_parent_param = parent.columnData()['parameter']
        except KeyError:
            new_parent_param = NodegraphAPI.GetNode('Group').getParameters()

        # move all selected parameters
        for item in item_list:
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


"""    def buildAddMenu(self, menu):
        menu.addAction('Number', UndoableAction('Add Number Parameter', self.__addNumberParameter))
        menu.addAction('String', UndoableAction('Add String Parameter', self.__addStringParameter))
        menu.addSeparator()
        menu.addAction('Group', UndoableAction('Add Group Parameter', self.__addGroupParameter))
        menu.addSeparator()
        menu.addAction('Number Array', UndoableAction('Add Number Array Parameter', self.__addNumberArrayParameter))
        menu.addAction('String Array', UndoableAction('Add String Array Parameter', self.__addStringArrayParameter))
        menu.addAction('Float Vector', UndoableAction('Add Float Vector Parameter', self.__addFloatVectorParameter))
        menu.addSeparator()
        menu.addAction('Color, RGB', UndoableAction('Add Color Parameter', self.__addColorParameterRGB))
        menu.addAction('Color, RGBA', UndoableAction('Add Color Parameter', self.__addColorParameterRGBA))
        menu.addSeparator()
        menu.addAction('Color Ramp', UndoableAction('Add Color Ramp Parameter', self.__addColorRampParameter))
        menu.addAction('Float Ramp', UndoableAction('Add Float Ramp Parameter', self.__addFloatRampParameter))
        menu.addSeparator()
        menu.addAction('Button', UndoableAction('Add Button Parameter', self.__addButtonParameter))
        menu.addAction('Toolbar', UndoableAction('Add Toolbar Parameter', self.__addToolbarParameter))
        menu.addSeparator()
        menu.addAction('TeleParameter', UndoableAction('Add TeleParameter', self.__addTeleParameter))
        menu.addAction('Node Drop Proxy', UndoableAction('Node Drop Proxy', self.__addNodeDropProxyParameter))"""

#if __name__ == "__main__":
node = NodegraphAPI.GetAllSelectedNodes()[0]
widget = EditUserParametersMainWidget(node=node)
widget.resize(500, 500)
widget.show()
widget.move(QCursor.pos())