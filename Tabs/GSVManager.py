from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QAbstractItemView, QCompleter, QComboBox, QSplitter, QTabWidget)
from qtpy.QtCore import Qt, QEvent, QSortFilterProxyModel
from qtpy.QtGui import QStandardItemModel, QStandardItem, QCursor

from Katana import UI4, NodegraphAPI, Utils


class GSVManager(UI4.Tabs.BaseTab):
    """

    Attributes:
        gsv_list (list): of all GSVs that are currently in this widget.
            This is separate from Katanas internal GSV's


    """
    NAME = "GSVManager"

    def __init__(self, parent=None):
        super(GSVManager, self).__init__(parent)
        self.setGSVList(GSVUtils().getAllGSVNames())
        self.createGUI()
        Utils.EventModule.RegisterCollapsedHandler(self.gsvChanged, 'parameter_finalizeValue', None)
        Utils.EventModule.RegisterCollapsedHandler(self.nodeGraphLoad, 'nodegraph_loadEnd', None)
        Utils.EventModule.RegisterCollapsedHandler(self.paramChildDeleted, 'parameter_deleteChild', None)

    def rename(self, args):
        pass

    """ CREATE GUI"""
    def createGUI(self):
        """ Creates the main layout"""

        # create widgets
        self._display_tab = DisplayTab(parent=self)
        self._view_widget = ViewWidget(parent=self)
        self._edit_widget = EditWidget(parent=self)
        self._display_tab.addTab(self.viewWidget(), "View")
        self._display_tab.addTab(self.editWidget(), "Edit")

        # setup layout
        QVBoxLayout(self)
        self.layout().addWidget(self._display_tab)

    """ WIDGETS """
    def viewWidget(self):
        return self._view_widget

    def editWidget(self):
        return self._edit_widget

    """ PROPERTIES"""
    def getGSVList(self):
        """List of current GSV patterns.

        Not to be confused with getAllGSVNames, which will search for the
        currently available patterns based off of the Katana params.
        """

        return self.gsv_list
    
    def setGSVList(self, gsv_list):
        self.gsv_list = gsv_list

    """ EVENTS """
    def update(self, gsv='', value=''):
        """because you can't delete rows...and have to modify them... yay?"""
        def updateGSVs():
            # get current GSVs in widget
            current_gsvs = self.getGSVList()

            # get current GSVs available
            available_gsvs = GSVUtils().getAllGSVNames()
            # append to gsv_list
            # set gsv list
            self.setGSVList(available_gsvs)

            # get difference
            new_gsvs = list(set(available_gsvs) - set(current_gsvs))

            layout = self.viewWidget().layout()
            for gsv in new_gsvs:
                # add to main widget (form layout)
                options = GSVUtils().getGSVOptions(gsv)
                label = QLabel(gsv)
                default_value = NodegraphAPI.GetRootNode().getParameter('variables.%s.value' % gsv).getValue(0)
                combobox = GSVOptionsComboBox(item_list=options, default_value=default_value)
                layout.addRow(label, combobox)

                # add to edit widget (combo_box)
                model = self.editWidget().editGSVNamesWidget().getModel()
                item = QStandardItem(gsv)
                model.setItem(model.rowCount(), 0, item)

                if str(self.editWidget().editGSVNamesWidget().currentText()) == '<variables>':
                    item = QListWidgetItem(gsv)

                    self.editWidget().viewEditableGSVWidget().addItem(item)

        def updateOptions():
            #=======================================================================
            # updates if there is a change to the GSV Options
            #=======================================================================
            ## get the corret main combo_box to add to
            if value == '':
                return
            layout = self.viewWidget().layout()
            combo_box = None
            for index in range(layout.count()):
                child = layout.itemAt(index).widget()
                if hasattr(child,'text'):
                    if child.text() == gsv:
                        combo_box = layout.itemAt(index+1).widget()
            #=======================================================================
            # add the new GSV to the combo_box on the main_widget and the list on the
            # edit widget, if the edit widget is curently set to that gsv
            #=======================================================================
            # get combo box
            item_list = []

            if combo_box != None:
                model =  combo_box.getModel()
                row_count = model.rowCount()
                
                # get list of currently available options in the combo box
                for index in range( row_count ):
                    item = model.item(index)
                    item_list.append(str(item.text()))
                
                
                #add new items to the combo box + list widget
                #set the graph state variable parameter
                #for some reason setting this below is making it so it doesnt set the combo box for the FIRST 
                # gsv creation...

                if value not in item_list:
    
                    param = NodegraphAPI.GetRootNode().getParameter('variables.%s.value'%gsv)
                    if not param:
                        param = NodegraphAPI.GetRootNode().getParameter('variables.%s').createChildString('value')
                    if param:
                        param.setValue(value, 0)
                        #if value.rstrip() != '':
                        new_item = QStandardItem(value)
                        model.setItem(row_count, 0, new_item)
                        #check to make sure its the right gsv
                        edit_gsv = str(self.editWidget().editGSVNamesWidget().currentText())
                        if edit_gsv == gsv:
                            #add to list widget
                            list_widget = self.editWidget().viewEditableGSVWidget()
                            item = QListWidgetItem(value)
                            list_widget.addItem(item)
                    combo_box.setEditText(value)

        updateGSVs()
        updateOptions()
        
    def nodeGraphLoad(self, args):
        # repopulate everything...
        # meta data loading... essentially creating random GSV's
        # creates blank GSV on new scene --> file load
        # creates first GSV on loaded file --> new scene
        self.viewWidget().populate()
        self.editWidget().populate()
        self.setGSVList(GSVUtils().getAllGSVNames())

    def gsvChanged(self, args):
        """ When  GSV is changed, this will updated the main display for the user"""

        root_node = NodegraphAPI.GetRootNode()
        ## NEW
        try:
            if args[2][2]:
                test_param = args[2][2]['param'].getParent().getParent().getName()
                if args[2][2]['node'] == root_node and test_param == 'variables':
                    gsv = args[2][2]['param'].getParent().getName()
                    value = args[2][2]['param'].getValue(0)
                    self.update(gsv=gsv, value=value)
        except:
            pass

        ## MUTATED
        try:
            if args[0][2]:
                test_param = args[0][2]['param'].getParent().getParent().getName()
                if args[0][2]['node'] == root_node and test_param == 'variables':
                    gsv = args[0][2]['param'].getParent().getName()
                    value = args[0][2]['param'].getValue(0)
                    self.update(gsv=gsv, value=value)
        except:
            pass

    def paramChildDeleted(self, args):
        '''
        event when the user uses the "Clear Menu Options" from the GSV menu to update
        this GUI
        '''
        
        def clearMenuOptions():
            param = args[0][2]['param']
            if args[0][2]['node'] == NodegraphAPI.GetRootNode(): 
                if param.getParent().getName() == 'variables':
                    gsv = param.getName()
                    combo_box_gsv = str(self.editWidget().editGSVNamesWidget().currentText())
                    gsv_list = GSVUtils().getGSVOptions(gsv)
                    # update Edit Widgets List View
                    if gsv == combo_box_gsv:
                        self.editWidget().viewEditableGSVWidget().clear()
                        self.editWidget().viewEditableGSVWidget().populate()

                    # update View Widgets ComboBox
                    # get combo box
                    layout = self.viewWidget().layout()
                    for index in range(layout.count()):
                        child = layout.itemAt(index).widget()
                        if hasattr(child, 'text'):
                            if str(child.text()) == gsv:
                                combo_box = layout.itemAt(index+1).widget()
                                model = combo_box.getModel()
                                child_delete_index = index
                    # remove items from main widget combo box
                    for index in reversed(range(model.rowCount())):
                        item = model.item(index)
                        if str(item.text()) not in gsv_list:
                            model.removeRow(index)
                    current_gsv = param.getChild('value').getValue(0)
                    combo_box.setEditText(current_gsv)

        def deleteGSV():
            child_name = args[0][2]['childName']
            current_options_list = [child_name]

            # update list_widget
            new_gsv_list = GSVUtils().getAllGSVNames()

            if self.editWidget().editGSVNamesWidget().currentText() == '<variables>':
                self.editWidget().viewEditableGSVWidget().clear()
                self.editWidget().viewEditableGSVWidget().populate(item_list=new_gsv_list)

            # delete Edit Widget combo box model entry...
            old_gsv_list = self.getGSVList()
            gsv_list_delta = list(set(old_gsv_list) - set(new_gsv_list))
            
            self.setGSVList(new_gsv_list)

            model = self.editWidget().editGSVNamesWidget().getModel()
            for index in reversed(range(model.rowCount())):
                item = model.item(index)
                if str(item.text()) in gsv_list_delta:
                    model.removeRow(index)

            # delete main_widget form widget?
            layout = self.viewWidget().layout()
            for index in reversed(range(layout.count())):
                child = layout.itemAt(index).widget()
                if hasattr(child, 'text'):
                    if child.text() in gsv_list_delta:
                        layout.itemAt(index+1).widget().setParent(None)
                        layout.itemAt(index).widget().setParent(None)

        clearMenuOptions()
        deleteGSV()


class GSVUtils(object):
    STRING = 0
    PARAMETER = 1
    @staticmethod
    def addGSVOption(gsv, new_option, row=None):
        """Adds an option to an already existing GSV

        Args:
            gsv (str):
            new_option (str):

        """
        # get gsv param
        gsv_param = GSVUtils().getGSVParameter(gsv)

        # get options param
        if 'options' not in [child.getName() for child in gsv_param.getChildren()]:
            options = gsv_param.createChildStringArray('options', 0)
        else:
            options = gsv_param.getChild("options")

        # get all options
        options_list = [gsv_param.getValue(0) for gsv_param in options.getChildren()]

        # create new GSV option
        if new_option not in options_list:
            if not row:
                row = options.getNumChildren()

            new_option_param = options.insertArrayElement(row)
            new_option_param.setValue(str(new_option), 0)

    @staticmethod
    def createNewGSV(gsv):
        """
        Creates a new GSV

        Args:
            gsv (str): name of GSV to create

        Returns (str): name of gsv
        """
        variables_param = GSVUtils.getVariablesParameter()
        gsv_param = variables_param.createChildGroup(gsv)
        gsv_param.createChildNumber('enable', 1)
        gsv_param.createChildString('value', '')
        gsv_param.createChildStringArray('options', 0)
        return gsv_param.getName()

    @staticmethod
    def getAllGSVNames():
        """Returns a list of all the possible GSVs in the scene

        Returns (list): of strings
        """
        gsv_list = GSVUtils().getVariablesParameter().getChildren()
        gsv_keys_list = [gsv.getName() for gsv in gsv_list]
        return gsv_keys_list

    @staticmethod
    def getGSVOptions(gsv, return_as=0):
        """Returns a list of all of the options available for the specified GSV

        Args:
            gsv (str): name of GSV to get options for
            return_as (GSVUtils.TYPE): what type of list this should return
        Returns (list): of strings or parameters, depending on value given to "return_as" arg
        """
        gsv_param = GSVUtils.getGSVParameter(gsv)
        options_list = []
        if gsv_param:
            for child in gsv_param.getChildren():
                if child.getName() == 'options':
                    options = gsv_param.getChild("options").getChildren()
                    if return_as == GSVUtils.STRING:
                        options_list = [child.getValue(0) for child in options]
                    elif return_as == GSVUtils.PARAMETER:
                        options_list = options
                    """
                    options_list = []
                        for index in range(options_param.getNumChildren()):
                            option = options_param.getChildByIndex(index).getValue(0)
                            options_list.append(option)
                    """

        return options_list

    @staticmethod
    def getVariablesParameter():
        """
        Gets the GSV Variables parameter on the Root Node

        Returns (Parameter):
        """
        return NodegraphAPI.GetRootNode().getParameter('variables')

    @staticmethod
    def getGSVParameter(gsv):
        """
        Gets the GSV parameter from the string provided
        Args:
            gsv (str): name of GSV to get

        Returns (Parameter):

        """
        return GSVUtils().getVariablesParameter().getChild(gsv)

    @staticmethod
    def getGSVOptionParameter(gsv, option):
        """
        Gets the parameter that the GSV Option is held on
        Args:
            gsv (str):
            option (str):

        Returns (Parameter):

        """
        gsv_options = GSVUtils.getGSVOptions(gsv, return_as=GSVUtils.PARAMETER)
        for gsv_option in gsv_options:
            if gsv_option.getValue(0) == option:
                return gsv_option

        return None

    @staticmethod
    def moveGSVtoNewIndex(gsv, index):
        """
        moves the GSV to the index provided

        Args:
            gsv (str):
            index (int):

        Returns:

        """
        variables_param = GSVUtils.getVariablesParameter()
        gsv_param = GSVUtils.getGSVParameter(gsv)
        variables_param.reorderChild(gsv_param, index)

    @staticmethod
    def moveGSVOptionToNewIndex(gsv, option, index):
        """
        Moves the GSV option parameter provided to a new index

        Args:
            gsv (str): GSV to manipulate
            option (str): Option to move
            index  (int): new index to place the option at

        """

        option_param = GSVUtils.getGSVOptionParameter(gsv, option)
        gsv_options_param = GSVUtils.getGSVParameter(gsv).getChild("options")
        gsv_options_param.reorderChild(option_param, index)

    @staticmethod
    def deleteGSVOption(gsv, option):
        # update Katana GSV params
        """note that in the Project Settings tab, the variables has to be
        expanded/collapsed to refresh teh new list"""

        # get attrs
        gsv_options = GSVUtils().getGSVOptions(gsv)
        #gsv_options = list(set(gsv_list))
        gsv_param = GSVUtils().getGSVParameter(gsv)
        gsv_value_param = gsv_param.getChild("value")
        options_param = gsv_param.getChild("options")
        current_gsv = gsv_value_param.getValue(0)

        # if option remove is current, set to first option available
        if current_gsv == option:
            if len(gsv_options) > 0:
                value = gsv_options[0]
            else:
                value = ''
        else:
            value = ''
        gsv_value_param.setValue(value, 0)

        # remove option
        """ No delete function, so need to remove from array and reset"""
        gsv_options.remove(option)
        options_param.resizeArray(len(gsv_options))
        for options_param, optionValue in zip(options_param.getChildren(), gsv_options):
            options_param.setValue(optionValue, 0)

    @staticmethod
    def deleteGSV(gsv):
        gsv_param = GSVUtils().getGSVParameter(gsv)
        GSVUtils().getVariablesParameter().deleteChild(gsv_param)


class DisplayTab(QTabWidget):
    def __init__(self, parent=None):
        super(DisplayTab, self).__init__(parent)


""" VIEW WIDGET """
class ViewWidget(QWidget):
    def __init__(self, parent=None):
        super(ViewWidget, self).__init__(parent)
        QFormLayout(self)

        self.populate()

    """ POPULATE """
    def populate(self):
        """Creates the display for every GSV.  This is the left side of the display."""
        # clear layout (if it exists)
        if self.layout().count() > 0:
            for index in reversed(range(self.layout().count())):
                self.layout().itemAt(index).widget().setParent(None)

        # create a combobox for each GSV that is available
        gsv_keys = GSVUtils().getAllGSVNames()
        for gsv in gsv_keys:
            self.createGSVDisplayWidget(gsv)

    def createGSVDisplayWidget(self, gsv):
        """ Creates a GSV Display widget

        Args:
            gsv (str): name of gsv to create
        """
        # Get Attrs
        options = GSVUtils().getGSVOptions(gsv)

        label = QLabel(gsv)
        default_value = NodegraphAPI.GetRootNode().getParameter('variables.%s.value' % gsv).getValue(0)
        combobox = GSVOptionsComboBox(item_list=options, default_value=default_value)
        self.layout().addRow(label, combobox)


""" EDIT WIDGET """
class EditWidget(QWidget):
    """
    Widget to hold the view where the users can edit GSVs

    Hierarchy:
        VBoxLayout:
            |- line_edit --> (EditGSVOptionsWidget --> QLineEdit)
            |- combo_box --> (EditGSVNamesWidget --> QComboBox)
            |- list_widget --> (ViewEditableGSVWidget --> QListWidget)"""
    def __init__(self, parent=None):
        super(EditWidget, self).__init__(parent)
        self.main_widget = self.parent()

        # Create Widgets
        self._create_new_gsv_option_widget = EditGSVOptionsWidget(parent=self)
        self._edit_gsv_names_widget = EditGSVNamesWidget(parent=self)
        self._view_editable_gsv_widget = ViewEditableGSVWidget(parent=self)
        self._view_editable_gsv_widget.setAlternatingRowColors(True)
        self._view_editable_gsv_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Setup Layout
        QVBoxLayout(self)
        self.layout().addWidget(self._edit_gsv_names_widget)
        self.layout().addWidget(self._create_new_gsv_option_widget)
        self.layout().addWidget(self._view_editable_gsv_widget)

        # populate
        self.populate()

    """ WIDGETS """
    def editGSVOptionWidget(self):
        return self._edit_gsv_names_widget

    def editGSVNamesWidget(self):
        return self._edit_gsv_names_widget

    def viewEditableGSVWidget(self):
        return self._view_editable_gsv_widget

    def populate(self):
        gsv_keys = ['<variables>'] + GSVUtils().getAllGSVNames()
        # update combo box
        model = self.editGSVNamesWidget().getModel()
        
        if hasattr(model, 'rowCount'):
            for index in range(model.rowCount()):
                model.removeRow(index)
        
        gsv_keys = filter(None, gsv_keys)
        self.editGSVNamesWidget().populate(item_list=gsv_keys)
        
        #update list widget
        self.viewEditableGSVWidget().clear()
        self.viewEditableGSVWidget().populate(item_list=gsv_keys[1:])


class EditGSVOptionsWidget(QLineEdit):
    """Line Edit widget that creates new GSV options when enter is pressed"""
    def __init__(self, parent=None):
        super(EditGSVOptionsWidget, self).__init__(parent)
    
    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            ## Enter Pressed
            gsv = str(self.parent().editGSVNamesWidget().currentText())
            main_widget = self.parent().parent().parent().parent()

            # Do nothing
            if gsv.rstrip() == '':
                return QLineEdit.keyPressEvent(self, event, *args, **kwargs)

            # Create new GSV Option
            elif gsv != '<variables>':
                option = str(self.text())
                print(gsv)
                print(GSVUtils().getAllGSVNames())
                if gsv in GSVUtils().getAllGSVNames():
                    GSVUtils().addGSVOption(gsv, option)
                    main_widget.update(gsv=gsv, value=option)
                    self.setText('')

            # Create new GSV
            elif gsv == '<variables>':
                new_gsv = str(self.text())
                option = str(self.text())
                GSVUtils().createNewGSV(new_gsv)
                main_widget.update(gsv=gsv, value=option)
                self.setText('')
        return QLineEdit.keyPressEvent(self, event, *args, **kwargs)


class AbstractGSVComboBox(QComboBox):
    """ base combo box class to be inherited """
    def __init__(self, parent=None, item_list=[]):
        super(AbstractGSVComboBox, self).__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)
        self.item_list = item_list
        
        self.setLineEdit(QLineEdit("Select & Focus", self))
        self.lineEdit().selectAll()
        self.lineEdit().setFocus()   
        self.setEditable(True)

        self.completer = QCompleter(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setPopup(self.view())
        self.setCompleter(self.completer)
        
        self.pFilterModel = QSortFilterProxyModel(self)

    def getMainWidget(self, widget):
        if isinstance(widget, GSVManager):
            return widget
        else:
            if widget:
                return self.getMainWidget(widget.parent())        
    
    def populate(self, item_list=[]):

        self.model = QStandardItemModel()
        for i, child in enumerate(item_list):
            if child.rstrip() != '':
                item = QStandardItem(child)
                self.model.setItem(i, 0, item)

        self.setModel(self.model)
        self.setModelColumn(0)
        
    def getModel(self):
        return self.model

    def setModel(self, model):
        super(AbstractGSVComboBox, self).setModel( model )
        self.pFilterModel.setSourceModel( model )
        self.completer.setModel(self.pFilterModel)

    def setModelColumn(self, column):
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(AbstractGSVComboBox, self).setModelColumn(column)
        
    def view(self):
        return self.completer.popup()     
           
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

    def event(self, event, *args, **kwargs):
        ## Shift Pressed
        if (event.type() == QEvent.KeyPress) and (event.key() == Qt.Key_Tab):
            self.next_completion()
            return True

        ## Shift Tab Pressed
        elif (event.type() == QEvent.KeyPress) and (event.key() == 16777218):
            self.previous_completion()
            return True

        ## Enter Pressed
        elif (event.type() == QEvent.KeyPress) and (event.key() == 16777220 or event.key() == 16777221):
            pass

        return QComboBox.event(self, event, *args, **kwargs)


class EditGSVNamesWidget(AbstractGSVComboBox):
    """Main combo box on the Edit Widget.  This will display all of the GSV's available
    to the user.

    Changing this drop down will change the edit widgets display of the currently available
    options based off of the GSV selected.

    Setting this to <variables> is a special case, that will allow the user to manipulate
    the GSV's instead of their individual options.
    """

    def __init__(self, parent=None):
        super(EditGSVNamesWidget, self).__init__(parent)
        self.currentIndexChanged.connect(self.changedGSV)

    def showOptions(self, gsv):
        # check to see if new
        # list current variables available
        main_widget = self.getMainWidget(self)
        if main_widget:
            gsv_list = [''] + main_widget.getGSVList()

            if gsv not in gsv_list:
                # update GSV List
                gsv_list.append(gsv)
                main_widget.setGSVList(gsv_list)

                # create new GSV in katana
                GSVUtils.createNewGSV(gsv)

                # Update Main Widget
                layout = main_widget.viewWidget().layout()
                label = QLabel(gsv)
                default_value = ''
                combobox = GSVOptionsComboBox(item_list=[], default_value=default_value)
                layout.addRow(label, combobox)

            # Update options available to the user
            self.parent().viewEditableGSVWidget().clear()
            if hasattr(main_widget, '_edit_widget'):
                self.parent().viewEditableGSVWidget().populate()

    def showVariables(self):
        if hasattr(self.parent(), '_view_editable_gsv_widget'):
            # update edit widget
            self.parent().viewEditableGSVWidget().clear()
            variables_list = GSVUtils().getAllGSVNames()
            if hasattr(self.main_widget, '_edit_widget'):
                self.parent().viewEditableGSVWidget().populate(item_list=variables_list)

    def changedGSV(self):
        """ Combo box that will update what is displayed in the list widget
        if it is set to <variables> it will show all the GSVs, if it is something
        else, then it will show the options of that variable"""

        self.main_widget = self.getMainWidget(self)
        gsv = str(self.currentText())
        if gsv != '<variables>':
            self.showOptions(gsv)
        else:
            self.showVariables()


class GSVOptionsComboBox(AbstractGSVComboBox):
    """ Main display for viewing all of the options in a GSV.  In the create widget,
    this will be the dropdown menu that displays all of the GSV options to the user"""

    def __init__(self, parent=None, item_list=[], default_value=''):
        super(GSVOptionsComboBox,self).__init__(parent)
        #self.setEditable(False)
        self.currentIndexChanged.connect(self.changeGSV)
        self.populate(item_list)
        self.setEditText(default_value)

    def changeGSV(self):
        """ sets the current GSV[option] in the Project Settings to the one the user just changed this too"""

        main_widget = self.getMainWidget(self)
        
        option = str(self.currentText())
        
        if self.parent():
            # get gsv name 
            layout = self.parent().layout()
            for index in range(layout.count()):
                child = layout.itemAt(index).widget()
                if hasattr(child,'currentText'):
                    if child.currentText() == self.currentText():
                        gsv = str(layout.itemAt(index-1).widget().text())
            # get gsv param
            param = NodegraphAPI.GetNode('rootNode').getParameter('variables.%s'%gsv)
            value_param = param.getChild('value')
            value_param.setValue(option, 0)
            try:
                options_list = [child.getValue(0) for child in param.getChild('options').getChildren()]
            except:
                options_list = []

            # Create new GSV
            """ If the user input does not exist, create a new GSV """
            if option not in options_list:
                if main_widget:
                    # create new GSV Option
                    GSVUtils().addGSVOption(gsv, option)
                    #get edit combo text?
                    edit_combo_box = main_widget.editWidget().editGSVNamesWidget()
                    if str(edit_combo_box.currentText()) != '<variables>':
                        list_widget = main_widget.editWidget().viewEditableGSVWidget()
                        list_widget.clear()
                        list_widget.populate()

    def getMainWidget(self, widget):
        if isinstance(widget, GSVManager):
            return widget
        else:
            if widget:
                return self.getMainWidget(widget.parent())        

    def update(self, item_list=[]):
        self.populate(item_list)


class ViewEditableGSVWidget(QListWidget):
    '''
    list widget that is parented to the EditWidget.  This list will display to the user all of the current
    options that are available for the particular GSV that is being displayed in the "EditGSVNamesWidget"
    widget.
    '''
    def __init__(self, parent=None, combo_box=None):
        super(ViewEditableGSVWidget, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)

    """ UTILS """
    def deleteOptions(self):
        """
        Removes all of the currently selected GSV options
        """
        # get attrs
        main_widget = self.getMainWidget(self)
        gsv = str(self.parent().editGSVNamesWidget().currentText())
        current_items_list = self.selectedItems()
        current_options_list = [str(item.text()) for item in current_items_list]
        gsv_list = GSVUtils().getGSVOptions(gsv)
        new_options = list(set(gsv_list) - set(current_options_list))

        # delete GSV Options
        for option in current_options_list:
            GSVUtils().deleteGSVOption(gsv, option)

        # update list widget (edit_widget)
        self.clear()
        self.populate()

        # update main_widget

        # get combo box
        layout = main_widget.viewWidget().layout()
        for index in range(layout.count()):
            child = layout.itemAt(index).widget()
            if hasattr(child, 'text'):
                if child.text() == gsv:
                    combo_box = layout.itemAt(index + 1).widget()
                    model = combo_box.getModel()

        # update combo box options
        for option in current_options_list:
            row_count = model.rowCount()
            for index in range(row_count):
                item = model.item(index)
                # no attribute item.text()
                if item:
                    if str(item.text()) == option:
                        model.removeRow(index)

        # reset Katana GSV
        combo_box.populate(item_list=new_options)

    def deleteGSVs(self):
        """
        Removes the currently selected GSVs
        Returns:

        """
        # get attrs
        main_widget = self.getMainWidget(self)
        current_items_list = self.selectedItems()
        current_options_list = [str(item.text()) for item in current_items_list]

        # delete gsv
        for gsv in current_options_list:
            GSVUtils.deleteGSV(gsv)
            # variables_param = NodegraphAPI.GetRootNode().getParameter('variables')
            # variables_param.deleteChild(variables_param.getChild(item))

        # update list_widget
        new_gsv_list = GSVUtils().getAllGSVNames()

        self.clear()
        self.populate(item_list=new_gsv_list)

        # delete edit_widget combo box model entry...
        old_gsv_list = main_widget.getGSVList()
        gsv_list_delta = list(set(old_gsv_list) - set(new_gsv_list))

        main_widget.setGSVList(new_gsv_list)

        model = self.parent().editGSVNamesWidget().getModel()
        for index in reversed(range(model.rowCount())):
            item = model.item(index)
            if str(item.text()) in gsv_list_delta:
                model.removeRow(index)

        # delete main_widget form widget?
        layout = self.main_widget.viewWidget().layout()
        for index in reversed(range(layout.count())):
            child = layout.itemAt(index).widget()
            if hasattr(child, 'text'):
                if child.text() in gsv_list_delta:
                    layout.itemAt(index + 1).widget().setParent(None)
                    layout.itemAt(index).widget().setParent(None)

    def populate(self, item_list=None):
        #
        self.main_widget = self.getMainWidget(self)
        # populate GSV options
        if self.main_widget:
            if not item_list:
                gsv_keys = GSVUtils().getAllGSVNames()
                gsv = self.parent().editGSVNamesWidget().currentText()
                if gsv in gsv_keys:
                    options_list = GSVUtils().getGSVOptions(gsv)
                    for option in options_list:
                        if option.rstrip() != '':
                            item = QListWidgetItem(option)
                            self.addItem(item)
            else:
                #      # populate GSV
                for option in item_list:
                    if option.rstrip() != '':
                        item = QListWidgetItem(option)
                        self.addItem(item)
        
    def getMainWidget(self, widget):
        
        if isinstance(widget, GSVManager):
            return widget
        else:
            return self.getMainWidget(widget.parent())        

    """ EVENTS """
    def keyPressEvent(self, event, *args, **kwargs):
        if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
            # delete an option (basically if the param on the editWidget().editGSVNamesWidget() != <variables>)
            main_widget = self.getMainWidget(self)
            # get gsv (edit combobox)
            gsv = str(self.parent().editGSVNamesWidget().currentText())
            if gsv != '<variables>':
                self.deleteOptions()
            else:
                self.deleteGSVs()

        return QListWidget.keyPressEvent(self, event, *args, **kwargs)

    def dropEvent(self, event):

        # get attrs
        current_text = self.parent().editGSVNamesWidget().currentText()

        # resolve drop event
        return_val = super(ViewEditableGSVWidget, self).dropEvent(event)

        # move GSV
        if current_text == "<variables>":
            for index in self.selectedIndexes():
                gsv = str(index.data())
                row = index.row()

                # move GSV to new index
                GSVUtils().moveGSVtoNewIndex(gsv, row)

                main_widget = self.getMainWidget(self)
                main_widget.viewWidget().populate()

        # move GSV Option
        else:
            gsv = current_text
            for index in self.selectedIndexes():
                option = index.data()
                row = index.row()
                # todo fix this
                GSVUtils.moveGSVOptionToNewIndex(gsv, option, row)
                # remove old
                # GSVUtils().deleteGSVOption(gsv, option)
                #
                # # insert new
                # GSVUtils().addGSVOption(gsv, option, row=row)

        return return_val


PluginRegistry = [("KatanaPanel", 2, "GSVManager", GSVManager)]
