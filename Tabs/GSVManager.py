"""
TODO
    Hierarchy:
        * Move lists to LabelledInputWidgets
            * EditGSVOptionsWidget --> AbstractStringInput
    Katana (Normal GSV updates in Project Settings):
        * Delete
        * Rename
        * New (Option, GSV)
    Katana (Events)
        * GSV Changed Events
            - create installable event in gsvutils
            - GSV Events Tab, to change when event happens
        * Need to make script ingestor thingymabobber?
            would also run on the EventsTab
"""

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit)
from qtpy.QtCore import Qt

from Katana import UI4, NodegraphAPI, Utils
from cgwidgets.widgets import (
    AbstractModelViewItem,
    FrameInputWidgetContainer,
    ListInputWidget,
    LabelledInputWidget,
    ModelViewWidget,
    ShojiModelViewWidget,
    StringInputWidget)

from cgwidgets.utils import getWidgetAncestor

from Utils2 import gsvutils


class GSVManager(UI4.Tabs.BaseTab):
    """

    Attributes:
        gsv_list (list): of all GSVs that are currently in this widget.
            This is separate from Katanas internal GSV's

    Hierarchy:
        QVBoxLayout
            |- mainWidget --> (ShojiModelViewWidget)
                |- viewWidget --> (ViewWidget --> QWidget)
                |    |* ViewGSVWidget --> (LabelledInputWidget)
                |- editWidget --> (EditWidget --> QWidget)
                    |> VBoxLayout:
                        |- editGSVNamesWidget --> (ListInputWidget)
                        |- line_edit --> (EditGSVOptionsWidget --> QLineEdit)
                        |- displayEditableOptionsWidget --> (ModelViewWidget)
    """
    NAME = "GSVManager"

    def __init__(self, parent=None):
        super(GSVManager, self).__init__(parent)

        # create widgets
        self._main_widget = ShojiModelViewWidget(parent=self)
        self._view_widget = ViewWidget(parent=self)
        self._edit_widget = EditWidget(parent=self)
        self._main_widget.insertShojiWidget(0, column_data={"name":"View"}, widget=self.viewWidget())
        self._main_widget.insertShojiWidget(1, column_data={"name":"Edit"}, widget=self.editWidget())

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._main_widget)
        self.mainWidget().setHeaderItemIsDragEnabled(False)
        self.mainWidget().setHeaderItemIsEditable(False)
        # setup Katana events
        # Utils.EventModule.RegisterCollapsedHandler(self.gsvChanged, 'parameter_finalizeValue', None)
        Utils.EventModule.RegisterCollapsedHandler(self.nodeGraphLoad, 'nodegraph_loadEnd', None)
        # Utils.EventModule.RegisterCollapsedHandler(self.paramChildDeleted, 'parameter_deleteChild', None)

    def rename(self, args):
        pass

    """ WIDGETS """
    def mainWidget(self):
        return self._main_widget

    def viewWidget(self):
        return self._view_widget

    def editWidget(self):
        return self._edit_widget

    """ KATANA EVENTS """
    def nodeGraphLoad(self, args):
        """ Reload the View Widget when a new Katana scene is opened"""
        self.editWidget().setText("<variables>")
        self.viewWidget().update()
        self.editWidget().update()

    # def gsvChanged(self, args):
    #     """ When  GSV is changed, this will updated the main display for the user
    #     #TODO Update this so...
    #         * Will create new GSV's
    #     """
    # 
    #     root_node = NodegraphAPI.GetRootNode()
    #     ## NEW
    #     try:
    #         if args[2][2]:
    #             test_param = args[2][2]['param'].getParent().getParent().getName()
    #             if args[2][2]['node'] == root_node and test_param == 'variables':
    #                 gsv = args[2][2]['param'].getParent().getName()
    #                 value = args[2][2]['param'].getValue(0)
    #                 # self.update(gsv=gsv, value=value)
    #     except:
    #         pass
    # 
    #     ## MUTATED
    #     try:
    #         if args[0][2]:
    #             test_param = args[0][2]['param'].getParent().getParent().getName()
    #             if args[0][2]['node'] == root_node and test_param == 'variables':
    #                 gsv = args[0][2]['param'].getParent().getName()
    #                 value = args[0][2]['param'].getValue(0)
    #                 # self.update(gsv=gsv, value=value)
    #     except:
    #         pass
    # 
    # def paramChildDeleted(self, args):
    #     '''
    #     event when the user uses the "Clear Menu Options" from the GSV menu to update
    #     this GUI
    #     '''
    #     
    #     def clearMenuOptions():
    #         param = args[0][2]['param']
    #         if args[0][2]['node'] == NodegraphAPI.GetRootNode(): 
    #             if param.getParent().getName() == 'variables':
    #                 gsv = param.getName()
    #                 combo_box_gsv = str(self.editWidget().text())
    #                 gsv_list = gsvutils.getGSVOptions(gsv)
    #                 # update Edit Widgets List View
    #                 if gsv == combo_box_gsv:
    #                     self.editWidget().displayEditableOptionsWidget().update()
    # 
    #                 # update View Widgets ComboBox
    #                 # get combo box
    #                 layout = self.viewWidget().layout()
    #                 for index in range(layout.count()):
    #                     child = layout.itemAt(index).widget()
    #                     if hasattr(child, 'text'):
    #                         if str(child.text()) == gsv:
    #                             combo_box = layout.itemAt(index+1).widget()
    #                             model = combo_box.getModel()
    #                             child_delete_index = index
    #                 # remove items from main widget combo box
    #                 for index in reversed(range(model.rowCount())):
    #                     item = model.item(index)
    #                     if str(item.text()) not in gsv_list:
    #                         model.removeRow(index)
    #                 current_gsv = param.getChild('value').getValue(0)
    #                 combo_box.setEditText(current_gsv)
    # 
    #     def deleteGSV():
    #         child_name = args[0][2]['childName']
    #         current_options_list = [child_name]
    # 
    #         # update list_widget
    #         if self.editWidget().text() == '<variables>':
    #             self.editWidget().displayEditableOptionsWidget().clearModel()
    #             self.editWidget().displayEditableOptionsWidget().populate()
    # 
    #         # delete Edit Widget combo box model entry...
    #         new_gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
    #         old_gsv_list = self.getGSVList()
    #         gsv_list_delta = list(set(old_gsv_list) - set(new_gsv_list))
    #         
    #         self.setGSVList(new_gsv_list)
    # 
    #         # delete main_widget form widget?
    #         layout = self.viewWidget().layout()
    #         for index in reversed(range(layout.count())):
    #             child = layout.itemAt(index).widget()
    #             if hasattr(child, 'text'):
    #                 if child.text() in gsv_list_delta:
    #                     layout.itemAt(index+1).widget().setParent(None)
    #                     layout.itemAt(index).widget().setParent(None)
    # 
    #     clearMenuOptions()
    #     deleteGSV()


""" VIEW WIDGET """
class ViewWidget(FrameInputWidgetContainer):
    """
    Main wigdet for viewing GSV's.

    Attributes:
        widgets (dict): key pair values to map the GSV name to the LabelledInputWidget
    """
    def __init__(self, parent=None):
        super(ViewWidget, self).__init__(parent)
        self.setIsHeaderShown(False)
        self.setDirection(Qt.Vertical)
        #QVBoxLayout(self)
        self._widget_list = {}
        self.populate()

    """ POPULATE """
    def clear(self):
        """
        Removes all of the GSVViewWidgets from the display
        """
        # clear layout (if it exists)
        if self.layout().count() > 0:
            for index in reversed(range(self.layout().count())):
                self.layout().itemAt(index).widget().setParent(None)

        self._widget_list = {}

    def populate(self):
        """Creates the display for every GSV.  This is the left side of the display."""
        # create a combobox for each GSV that is available
        gsv_keys = gsvutils.getAllGSV(return_as=gsvutils.STRING)
        for gsv in gsv_keys:
            self.addWidget(gsv)

    def update(self):
        """
        Updates the current view widgets dispalyed to the user
        """
        self.clear()
        self.populate()

    """ PROPERTIES """
    def addWidget(self, gsv):
        """
        Adds a widget to the layout.

        Args:
            gsv (str): name of GSV to create
        """
        widget = ViewGSVWidget(self, name=gsv)

        self.addInputWidget(widget)
        self.widgets()[gsv] = widget

    def removeWidget(self, gsv):
        # remove widget
        self.widgets()[gsv].setParent(None)
        self.widgets()[gsv].deleteLater()

        # remove key
        del self.widgets()[gsv]

    def renameWidget(self, gsv, new_name):
        """
        Renames the GSV widget to the new name provided

        Args:
            gsv (str): name of widget to change
            new_name (str): value to change to
        """
        # cast to strings
        gsv = str(gsv)
        new_name = str(new_name)

        # get widget
        widget = self.widgets()[gsv]

        # update widget
        widget.viewWidget().setText(new_name)
        widget.gsv = new_name

        # update widgets dict
        self.widgets()[new_name] = widget
        del self.widgets()[gsv]

    def widgets(self):
        return self._widget_list


class ViewGSVWidget(LabelledInputWidget):
    """
    One singular GSV view that is displayed in the ViewWidget.

    This will consist of one label showing which GSV it is, and one
    ListInputWidget that will have all of the GSV's
    """
    def __init__(
        self,
        parent=None,
        name="None",
        direction=Qt.Horizontal,
        default_label_length=100
    ):
        delegate_widget = ListInputWidget()
        super(ViewGSVWidget, self).__init__(
            parent,
            name=name,
            default_label_length=default_label_length,
            direction=direction,
            delegate_widget=delegate_widget
        )
        # setup label
        self.gsv = self.name()

        # self.viewWidget().setDisplayMode(OverlayInputWidget.DISABLED)

        # setup view
        view_widget = StringInputWidget(self)
        view_widget.setText(self.gsv)
        self.setViewWidget(view_widget)
        self.viewWidget().setUserFinishedEditingEvent(self.renameGSV)

        # setup delegate
        self.delegateWidget().dynamic_update = True
        self.delegateWidget().setUserFinishedEditingEvent(self.setGSVOption)
        self.delegateWidget().populate(self.update())
        self.delegateWidget().setCleanItemsFunction(self.update)

    def renameGSV(self, widget, value):
        """
        Changes the GSV name to the one provided by the user.
        Args:
            widget:
            value:

        Returns:

        """
        # preflight
        if self.gsv == value: return

        # rename GSV
        gsvutils.renameGSV(self.gsv, value)
        view_widget = getWidgetAncestor(self, ViewWidget)
        view_widget.renameWidget(self.gsv, str(value))

    def update(self):
        return [[option] for option in gsvutils.getGSVOptions(self.gsv, return_as=gsvutils.STRING)]

    def setGSVOption(self, widget, value):
        """
        Sets the current GSV to the option provided

        Args:
            widget (QWidget): widget sending signal
            value (str): option the user has changed to

        Returns:

        """
        gsvutils.setGSVOption(self.gsv, value)


""" EDIT WIDGET """
class EditWidget(QWidget):
    """
    Widget to hold the view where the users can edit GSVs

    Hierarchy:
        VBoxLayout:
            |- editGSVNamesWidget --> (ListInputWidget)
            |- line_edit --> (EditGSVOptionsWidget --> QLineEdit)
            |- displayEditableOptionsWidget --> (ModelViewWidget)
    """
    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)

        # Set attrs
        self._display_mode = gsvutils.VARIABLES

        # Create Widgets
        self._create_new_gsv_option_widget = EditGSVOptionsWidget(parent=self)
        self._edit_gsv_names_widget = EditGSVNamesWidget(parent=self)
        self._display_editable_options_widget = DisplayEditableOptionsWidget(parent=self)
        self._display_editable_options_widget.show()
        #self._display_editable_options_widget.setAlternatingRowColors(True)
        #self._display_editable_options_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Setup Layout
        QVBoxLayout(self)
        self.layout().addWidget(self._edit_gsv_names_widget)
        self.layout().addWidget(self._create_new_gsv_option_widget)
        self.layout().addWidget(self._display_editable_options_widget)

        # populate
        # self.populate()

    """ UTILS """
    def text(self):
        return str(self.editGSVNamesWidget().text())

    def setText(self, text):
        self.editGSVNamesWidget().setText(text)

    """ PROPERTIES """
    def displayMode(self):
        return self._display_mode

    def setDisplayMode(self, _display_mode):
        self._display_mode = _display_mode

    """ WIDGETS """
    def editGSVOptionWidget(self):
        return self._edit_gsv_names_widget

    def editGSVNamesWidget(self):
        return self._edit_gsv_names_widget

    def displayEditableOptionsWidget(self):
        return self._display_editable_options_widget

    def update(self):
        # update list widget
        self.displayEditableOptionsWidget().update()


class EditGSVNamesWidget(ListInputWidget):
    """This will display the currently active GSV to the user

    Changing this drop down will change the edit widgets display of the currently available
    options based off of the GSV selected.

    Setting this to <variables> is a special case, that will allow the user to manipulate
    the GSV's instead of their individual options.
    """

    def __init__(self, parent=None):
        super(EditGSVNamesWidget, self).__init__(parent)
        # set default attrs
        self.dynamic_update = True
        self.filter_results = False
        self.setText("<variables>")

        # setup events
        self.setUserFinishedEditingEvent(self.changedGSV)
        self.populate(self.getAllGSVNames())
        self.setCleanItemsFunction(self.getAllGSVNames)

    def getAllGSVNames(self):
        """
        Returns a list of lists of all of the GSV names
        Returns (list): of lists
            [['var1'], ['var2'], ['var3']]

        """
        variables = ['<variables>'] + gsvutils.getAllGSV(return_as=gsvutils.STRING)
        gsv_keys = [[variable] for variable in variables]
        return gsv_keys

    def setOptionsDisplayMode(self):
        """When the GSV is changed, this will show the OPTIONS available in the displayEditableOptionsWidget

        Args:
            gsv (str): name of GSV
        """

        main_widget = getWidgetAncestor(self, GSVManager)

        if main_widget:
            gsv = str(self.text())
            edit_widget = main_widget.editWidget()
            edit_widget.setDisplayMode(gsvutils.OPTIONS)
            gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
            # create new GSV if it doesn't exist
            if gsv not in gsv_list:
                # create new GSV in katana
                gsvutils.createNewGSV(gsv)

                # create new entry in the view widget
                main_widget.viewWidget().addWidget(gsv)

            # Update options available to the user
            if hasattr(main_widget, '_edit_widget'):
                edit_widget.displayEditableOptionsWidget().update()

    def setVariablesDisplayMode(self):
        """When the GSV is changed, this will show the VARIABLES available in the displayEditableOptionsWidget

        Args:
            gsv (str): name of GSV
        """
        edit_widget = getWidgetAncestor(self, EditWidget)
        if hasattr(edit_widget, '_display_editable_options_widget'):
            # edit_widget = getWidgetAncestor(self, EditWidget)
            edit_widget.setDisplayMode(gsvutils.VARIABLES)
            # update edit widget
            edit_widget.displayEditableOptionsWidget().update()

    def changedGSV(self, widget, value):
        """ Combo box that will update what is displayed in the list widget
        if it is set to <variables> it will show all the GSVs, if it is something
        else, then it will show the options of that variable"""
        # preflight
        if str(self.text()) == "": return

        # set modes
        if str(self.text()) == '<variables>':
            self.setVariablesDisplayMode()
        else:
            self.setOptionsDisplayMode()


class EditGSVOptionsWidget(QLineEdit):
    """Line Edit widget that creates new GSV options when enter is pressed"""
    def __init__(self, parent=None):
        super(EditGSVOptionsWidget, self).__init__(parent)
    
    def keyPressEvent(self, event, *args, **kwargs):
        # Enter Pressed
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            main_widget = getWidgetAncestor(self, GSVManager)
            edit_widget = main_widget.editWidget()
            current_gsv_text = str(edit_widget.text())


            # Pre flight
            if self.text() == "": return
            if current_gsv_text == "": return

            # Create new GSV Option
            elif current_gsv_text != '<variables>':
                option = str(self.text())
                if current_gsv_text in gsvutils.getAllGSV(return_as=gsvutils.STRING):
                    param = gsvutils.addGSVOption(current_gsv_text, option)
                    new_entry_text = option

            # Create new GSV
            elif current_gsv_text == '<variables>':
                gsv = str(self.text())
                gsv_list = gsvutils.getAllGSV(return_as=gsvutils.STRING)
                # create new GSV if it doesn't exist
                if gsv not in gsv_list:
                    # create new GSV in katana
                    param = gsvutils.createNewGSV(gsv)

                    # create new entry in the view widget
                    main_widget.viewWidget().addWidget(gsv)

                    # get new entry text
                    new_entry_text = gsv

            # create new list entry
            model = main_widget.editWidget().displayEditableOptionsWidget().model()
            root_item = model.getRootItem()
            num_children = len(root_item.children())
            main_widget.editWidget().displayEditableOptionsWidget().createNewItem(new_entry_text, param, index=num_children)

            # reset text
            self.setText('')

        return QLineEdit.keyPressEvent(self, event, *args, **kwargs)


class DisplayEditableOptionsItem(AbstractModelViewItem):
    def __init__(self, parent=None, parameter=None):
        super(DisplayEditableOptionsItem, self).__init__(parent)
        self.setParameter(parameter)

    def parameter(self):
        return self._parameter

    def setParameter(self, parameter):
        self._parameter = parameter


class DisplayEditableOptionsWidget(ModelViewWidget):
    def __init__(self, parent=None):
        super(DisplayEditableOptionsWidget, self).__init__(parent)
        self.model().setItemType(DisplayEditableOptionsItem)

        # setup events
        self.setItemDeleteEvent(self.deleteSelection)
        self.setTextChangedEvent(self.renameSelectedItem)
        self.setDropEvent(self.moveSelectedItems)

        # setup attrs
        self.setMultiSelect(True)

        # populate
        self.populate()

    def createNewItem(self, name, parameter, index=0):
        index = self.model().insertNewIndex(index, name=str(name))
        item = index.internalPointer()
        item.setParameter(parameter)

    def populate(self):
        """
        Creates all of the corresponding items provided

        Args:
            gsv_list (list): of parameters to be populated
        """
        #

        edit_widget = getWidgetAncestor(self, EditWidget)

        # populate editable options
        if edit_widget:
            # populate ALL options, if no gsv_list provided,
            if edit_widget.displayMode() == gsvutils.OPTIONS:
                self.populateOptions()
            # populate GSV names
            elif edit_widget.displayMode() == gsvutils.VARIABLES:
                self.populateGSV()

    def populateGSV(self):
        """
        Creates the items for all of the GSV available in the scene
        """
        gsv_list = gsvutils.getAllGSV(return_as=gsvutils.PARAMETER)

        # create entries
        for gsv_param in reversed(gsv_list):
            gsv_param = gsv_param.getName()
            if gsv_param.rstrip() != '':
                self.createNewItem(gsv_param, gsv_param)

    def populateOptions(self):
        """
        Creates the items for all of the options available in the current GSV
        """
        # get edit widget
        edit_widget = getWidgetAncestor(self, EditWidget)

        # get all GSVs
        gsv_keys = gsvutils.getAllGSV(return_as=gsvutils.STRING)
        gsv = edit_widget.text()

        # if GSV is valid, populate all options
        if gsv in gsv_keys:
            options_list = gsvutils.getGSVOptions(gsv, return_as=gsvutils.PARAMETER)
            for option_param in reversed(options_list):
                option_name = option_param.getValue(0)
                if option_name.rstrip() != '':
                    self.createNewItem(option_name, option_param)

    def update(self):
        """
        Updates the current display based on the list provided.

        If no list is provided, then by default this will populate the options for the current GSV

        Args:
            gsv_list (list): of parameters to be populated

        Returns:

        """
        self.clearModel()
        self.populate()

    """ EVENTS """
    def moveSelectedItems(self, data, items, model, row, parent):
        """
        Changes the GSV/Option name to the values provided

        Args:
            items (list): of DisplayEditableOptionsItem currently being dropped
            row (int): row being dropped on


        Note:
            When the user Drag/Drops items in the display

        """
        edit_widget = getWidgetAncestor(self, EditWidget)

        for item in items:
            # Rename Option
            if edit_widget.displayMode() == gsvutils.OPTIONS:
                gsv = edit_widget.text()
                option = item.columnData()['name']
                gsvutils.moveGSVOptionToNewIndex(gsv, option, row)

            # Rename GSV
            if edit_widget.displayMode() == gsvutils.VARIABLES:
                gsv = item.columnData()['name']
                gsvutils.moveGSVtoNewIndex(gsv, row)

                # update view
                main_widget = getWidgetAncestor(self, GSVManager)
                view_widget = main_widget.viewWidget()
                view_widget.update()

    def deleteSelection(self, item):
        """ Deletes the specified item, and removes the relevant data.

        Args:
            item (DisplayEditableOptionsItem): currently selected
        """
        edit_widget = getWidgetAncestor(self, EditWidget)
        # Remove Option
        if edit_widget.displayMode() == gsvutils.OPTIONS:
            # get attrs
            gsv = edit_widget.text()
            option = item.columnData()['name']

            # remove param
            gsvutils.deleteGSVOption(gsv, option)

        # Remove Variable
        if edit_widget.displayMode() == gsvutils.VARIABLES:
            # get attrs
            main_widget = getWidgetAncestor(self, GSVManager)
            view_widget = main_widget.viewWidget()
            gsv = item.columnData()['name']

            # remove param
            gsvutils.deleteGSV(gsv)

            # remove widget
            view_widget.removeWidget(gsv)

    def renameSelectedItem(self, item, old_value, new_value):
        """
        Changes the GSV/Option name to the values provided

        Args:
            item (DisplayEditableOptionsItem): current item selected
            old_value (str): current value of item
            new_value (str): new value that is being set

        Note:
            When the user Double Clicks to enter the item's text field.

        """
        edit_widget = getWidgetAncestor(self, EditWidget)

        # Rename Option
        if edit_widget.displayMode() == gsvutils.OPTIONS:
            # get attrs
            gsv = edit_widget.text()
            gsvutils.renameGSVOption(gsv, old_value, new_value)

        # Rename GSV
        if edit_widget.displayMode() == gsvutils.VARIABLES:
            # rename
            gsvutils.renameGSV(old_value, new_value)

            # update view widget
            main_widget = getWidgetAncestor(self, GSVManager)
            view_widget = main_widget.viewWidget()
            view_widget.renameWidget(old_value, new_value)

            # print(view_widget.widgets())
            # print(old_value)
            # view_widget.widgets()[old_value].setName(new_value)
