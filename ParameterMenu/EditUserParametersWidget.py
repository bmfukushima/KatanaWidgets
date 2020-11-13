"""
TODO:
    Signals
        * Drag / Drop
            Different Hierarchy
                    Reparent hierarchy
                    Move to position
            Same Hierarchy
                move to position
            Issue...
                Multi select... drag/drop duplicating =\
        * Edit
                Change parameter name
        * Delete
                Delete parameter
    Display:
        * Create param value display
    Create New:
        *
"""

from qtpy.QtWidgets import QLabel, QWidget
from qtpy.QtGui import QCursor
from qtpy.QtCore import QModelIndex

from cgwidgets.widgets import TansuModelViewWidget, TansuHeaderTreeView
from cgwidgets.utils import attrs

from Katana import UniqueName


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
        name = parameter.getName()
        widget = QLabel(name)
        # create index
        column_data = {'name': name, 'type': parameter.getType(), 'parameter': parameter}
        new_model_index = self.insertTansuWidget(row, column_data=column_data, widget=widget, parent=parent)
        new_model_index.internalPointer().setIsDropEnabled(False)

        # if group
        if parameter.getType() == 'group':
            new_model_index.internalPointer().setIsDropEnabled(True)
            children = parameter.getChildren()
            for row, child in enumerate(children):
                self.__populateParameters(row, child, parent=new_model_index)

    def paramDropEvent(self, row, indexes, parent):
        """

        """
        # get parent dropped on
        try:
            new_parent_param = parent.columnData()['parameter']
        except KeyError:
            new_parent_param = NodegraphAPI.GetNode('Group').getParameters()

        # move all selected parameters
        for item in indexes:
            param = item.columnData()['parameter']

            paramParent = param.getParent()

            if paramParent:
                # convert param to xml
                #paramName = UniqueName.GetUniqueName(param.getName(), new_parent_param.getChild)

                paramXml = param.buildXmlIO()
                paramXml.setAttr('name', param.getName())

                # delete old param
                paramParent.deleteChild(param)

                # create new param
                newParam = new_parent_param.createChildXmlIO(paramXml)
                new_parent_param.reorderChild(newParam, row)



                # update item meta data
                item.columnData()['parameter'] = newParam

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

node = NodegraphAPI.GetAllSelectedNodes()[0]
tansu_widget = EditUserParametersWidget(node=node)
tansu_widget.resize(500, 500)
tansu_widget.show()
tansu_widget.move(QCursor.pos())