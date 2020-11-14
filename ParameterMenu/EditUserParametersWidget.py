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

from Katana import UniqueName


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
        param_type = value

        # preflight
        if param_type not in EditUserParametersMainWidget.TYPES: return

        # create param
        # get parent
        parent_index = self.__getParentIndex()
        parent_param = parent_index.internalPointer().columnData()['parameter']
        # todo
        param = self.__createChildParameter(param_type, parent_param)

        # insert tansu widget
        insertion_row = parent_index.internalPointer().childCount()
        self.main_widget.createNewParameterIndex(insertion_row, param, parent_index)
        # reset text
        self.new_parameter.setText('')

    def __createChildParameter(self, param_type, parent):
        # TODO Setup for all parameter types...
        if param_type == "Number":
            param = parent.createChildNumber(param_type, 0)
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


class EditUserParametersDisplayWidget(QLabel):
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
    group = 'group'
    number = 'number'
    string = 'string'

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
        #node = NodegraphAPI.GetNode('AttributeSet')
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
        # create indexes for parameters
        # name = parameter.getName()
        # widget = QLabel(name)
        # # create index
        # column_data = {'name': name, 'type': parameter.getType(), 'parameter': parameter}
        # new_model_index = self.insertTansuWidget(row, column_data=column_data, widget=widget, parent=parent)
        # new_model_index.internalPointer().setIsDropEnabled(False)

        new_index = self.createNewParameterIndex(row, parameter, parent)

        # if group
        if parameter.getType() == 'group':
            new_index.internalPointer().setIsDropEnabled(True)
            children = parameter.getChildren()
            for row, child in enumerate(children):
                self.__populateParameters(row, child, parent=new_index)

    def createNewParameterIndex(self, row, parameter, parent):
        name = parameter.getName()
        widget = QLabel(name)
        # create index
        column_data = {'name': name, 'type': parameter.getType(), 'parameter': parameter}
        new_model_index = self.insertTansuWidget(row, column_data=column_data, widget=widget, parent=parent)
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
                # convert param to xml
                param_xml = param.buildXmlIO()
                param_xml.setAttr('name', param.getName())

                # delete old param
                current_parent_param.deleteChild(param)

                # create new param
                new_param = new_parent_param.createChildXmlIO(param_xml)
                new_parent_param.reorderChild(new_param, row)

                # update item meta data
                item.columnData()['parameter'] = new_param

        """
        destIndex = 0
        param = param_to_move
        paramParent = param.getParent()
        if not paramParent:
            return
        myParam = self.__getParam()
        paramName = UniqueName.GetUniqueName(param.getName(), myParam.getChild)
        paramXml = param.buildXmlIO()
        paramXml.setAttr('name', paramName)
        Utils.UndoStack.OpenGroup('Reparent User Parameter')
        try:
            newParam = myParam.createChildXmlIO(paramXml)
            myParam.reorderChild(newParam, destIndex)
            paramParent.deleteChild(param)
        finally:
            Utils.UndoStack.CloseGroup()
        """

    def paramNameChangedEvent(self, item, old_value, new_value):
        param = item.columnData()['parameter']
        param.setName(new_value)

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