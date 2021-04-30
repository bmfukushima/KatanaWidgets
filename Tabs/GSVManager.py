
from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QAbstractItemView, QCompleter, QComboBox, QSplitter)
from qtpy.QtCore import Qt, QEvent, QSortFilterProxyModel
from qtpy.QtGui import QStandardItemModel, QStandardItem, QCursor

from Katana import UI4 , NodegraphAPI, Utils


'''
BUGS
paramChildDeleted
Error in collapsed event handler paramChildDeleted(): AttributeError: 'NoneType' object has no attribute 'parent'
    2.) GUI Exists... 
        store combo box size


FEATURES     
    1.) Rename (Project Settings) / GUI
            GUI is easier... 
                Change Label to to double click --> line edit?
                Line edit signal/event to delete/create GSV
                
CLEANUP!!
    Main Widget:
        Name --> view_widget
        store data as    {
                                    'gsv' : {'label':<label>, 'combo_box':<combo_box>} ,
                                    'gsv' : {'label':<label>, 'combo_box':<combo_box>} ,
                                }
BaseTab --> VBox Layout    --> Swappable Layout (create/edit)
                                            --> Toggle Button
'''

class GSVManager(UI4.Tabs.BaseTab):
    """

    Attributes:
        gsv_list (list): of all GSVs
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
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.splitter = DisplaySplitter(parent=self)
        self._create_widget = self.createCreateWidget()
        self._edit_widget = self.createEditWidget()
        self.splitter.addWidget(self.createWidget())
        self.splitter.addWidget(self.editWidget())
        layout.addWidget(self.splitter)

        self.populateMainWidget()

        # setup default sizes
        if self.splitter.underMouse() is True:
            self.splitter.setSizes([500, 500])
            self.splitter.setHandleWidth(50)

        elif self.splitter.underMouse() is False:
            self.splitter.setSizes([500, 0])
            self.splitter.setHandleWidth(0)
        self.splitter.update()

    """ WIDGETS """
    def createWidget(self):
        return self._create_widget

    def createCreateWidget(self):
        """Creates the main widget that will be displayed on the stackedLayout"""

        widget = QWidget(parent=self)
        layout = QFormLayout()
        widget.setLayout(layout)
        return widget

    def editWidget(self):
        return self._edit_widget

    def createEditWidget(self):
        """Creates the edit_widget to be held on 1st index of the stackedLayout"""

        widget = EditWidget(parent=self)
        widget.populate()
        return widget

    """ POPULATE """
    def populateMainWidget(self):
        """Creates the display for every GSV.  This is the left side of the display."""
        #get attrs
        widget = self.createWidget()
        layout = widget.layout()
        
        # clear layout (if it exists)
        if layout.count() > 0:
            for index in reversed(range(layout.count())):
                layout.itemAt(index).widget().setParent(None)
        
        # create a combobox for each GSV that is available
        gsv_keys = GSVUtils().getAllGSVNames()
        for gsv in sorted(gsv_keys):
            options = GSVUtils().getGSVOptions(gsv)
            
            label = QLabel(gsv)
            default_value = NodegraphAPI.GetRootNode().getParameter('variables.%s.value'%gsv).getValue(0)
            combobox = GSVOptionsComboBox(item_list=options, default_value=default_value)
            layout.addRow(label, combobox)

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

            layout = self.createWidget().layout()
            for gsv in sorted(new_gsvs):
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
            layout = self.createWidget().layout()
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
        self.populateMainWidget()
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
                    combo_box_gsv = str(self.parent().editGSVNamesWidget().currentText())
                    gsv_list = GSVUtils().getGSVOptions(gsv)
                    #===============================================================
                    # update list widget 
                    #===============================================================
                    if gsv == combo_box_gsv:
                        self.editWidget().viewEditableGSVWidget().clear()
                        self.editWidget().viewEditableGSVWidget().populate()
                    
                    #===============================================================
                    # update main widget combo box
                    #===============================================================
                    #get combo box
                    layout = self.createWidget().layout()
                    for index in range(layout.count()):
                        child = layout.itemAt(index).widget()
                        if hasattr(child,'text'):
                            if str(child.text()) == gsv:
                                combo_box = layout.itemAt(index+1).widget()
                                model = combo_box.getModel()
                                child_delete_index = index
                    #remove items from main widget combo box
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

            if self.parent().editGSVNamesWidget().currentText() == '<variables>':
                self.editWidget().viewEditableGSVWidget().clear()
                self.editWidget().viewEditableGSVWidget().populate(item_list=new_gsv_list)
            #===================================================================
            # delete edit_widget combo box model entry...
            #===================================================================
            old_gsv_list = self.getGSVList()
            gsv_list_delta = list(set(old_gsv_list) - set(new_gsv_list))
            
            self.setGSVList(new_gsv_list)

            model = self.parent().editGSVNamesWidget().getModel()
            for index in reversed(range(model.rowCount())):
                item = model.item(index)
                if str(item.text()) in gsv_list_delta:
                    model.removeRow(index)

            # delete main_widget form widget?
            layout = self.createWidget().layout()
            for index in reversed(range(layout.count())):
                child = layout.itemAt(index).widget()
                if hasattr(child,'text'):
                    if child.text() in gsv_list_delta:
                        #pos = (layout.getWidgetPosition(child)[0] * 2) + 1
                        #combo_box = layout.itemAt(pos).widget()
                        layout.itemAt(index+1).widget().setParent(None)
                        layout.itemAt(index).widget().setParent(None)
            pass
        clearMenuOptions()
        deleteGSV()

    def enterEvent(self, *args, **kwargs):
        stored_sizes = self.splitter.getStoredSizes()
        self.splitter.setSizes(stored_sizes)
        self.splitter.setHandleWidth(50)
        self.splitter.update()

    def leaveEvent(self, *args, **kwargs):

        tl = self.mapToGlobal(self.geometry().topLeft())
        br = self.mapToGlobal(self.geometry().bottomRight())

        x = QCursor().pos().x()
        y = QCursor().pos().y()
        l = tl.x()
        r = br.x()
        t = tl.y()
        b = br.y()

        if x > r or x < l or y < t or y > b:
            self.splitter.setSizes([500, 0])
            self.splitter.setHandleWidth(0)


class GSVUtils(object):
    @staticmethod
    def addGSVOption(gsv, new_option):
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
            # resize array to fit new child
            num_children = options.getNumChildren()
            options.resizeArray(num_children+1)

            # create new GSV option
            child = options.getChildByIndex(num_children)
            child.setValue(new_option, 0)

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
    def getGSVOptions(gsv):
        """Returns a list of all of the options available for the specified GSV

        Args:
            gsv (str): name of GSV to get options for

        Returns (list): of strings
        """
        gsv_param = GSVUtils.getGSVParameter(gsv)
        options_list = []
        if gsv_param:
            for child in gsv_param.getChildren():
                if child.getName() == 'options':
                    options = gsv_param.getChild("options").getChildren()
                    options_list = [child.getValue(0) for child in options]

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
    def deleteGSVOption(gsv, option):
        # update Katana GSV params
        """note that in the Project Settings tab, the variables has to be
        expanded/collapsed to refresh teh new list"""

        # get attrs
        gsv_list = GSVUtils().getGSVOptions(gsv)
        new_options = list(set(gsv_list) - list(option))
        gsv_param = GSVUtils().getGSVParameter(gsv)
        gsv_value_param = gsv_param.getChild("value")
        options_param = gsv_param.getChild("options")
        current_gsv = gsv_value_param.getValue(0)

        # if option remove is current, set to first option available
        if current_gsv == option:
            if len(new_options) > 0:
                value = new_options[0]
            else:
                value = ''
        else:
            value = ''
        gsv_value_param.setValue(value, 0)

        # remove option
        """ No delete function, so need to remove from array and reset"""
        options_param.resizeArray(len(new_options))
        for options_param, optionValue in zip(options_param.getChildren(), new_options):
            options_param.setValue(optionValue, 0)

    @staticmethod
    def deleteGSV(gsv):
        gsv_param = GSVUtils().getGSVParameter(gsv)
        GSVUtils().getVariablesParameter.deleteChild(gsv_param)


class DisplaySplitter(QSplitter):
    def __init__(self, parent=None):
        super(DisplaySplitter, self).__init__(parent)
        #will need to find a "cursor under"
        self.stored_sizes = [500, 0]
        self.setSizes(self.stored_sizes)
        self.setHandleWidth(0)
        self.update()

        self.splitterMoved.connect(self.setStoredSizes)
    
    def setStoredSizes(self):
        self.stored_sizes = self.sizes()

    def getStoredSizes(self):
        return self.stored_sizes


""" CREATE EDIT WIDGET """
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
            if gsv.rstrip() == '':
                return QLineEdit.keyPressEvent(self, event, *args, **kwargs)
            elif gsv != '<variables>':
                option = str(self.text())
                GSVUtils().addGSVOption(gsv, option)

                self.parent().parent().parent().update(gsv=gsv, value=option)
                self.setText('') 
            elif gsv == '<variables>':
                new_gsv = str(self.text())
                option = str(self.text())
                GSVUtils().createNewGSV(new_gsv)
    
                self.parent().parent().parent().update(gsv=gsv, value=option)
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
        for i, child in enumerate(sorted(item_list)):
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
                layout = main_widget.createWidget().layout()
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
        layout = main_widget.createWidget().layout()
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
        layout = self.main_widget.createWidget().layout()
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


PluginRegistry = [("KatanaPanel", 2, "GSVManager", GSVManager)]
