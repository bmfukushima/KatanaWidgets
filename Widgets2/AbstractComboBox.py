from PyQt5.QtWidgets import (
    QComboBox, QLineEdit, QCompleter, QSizePolicy
)

from PyQt5.QtCore import (
    QEvent, Qt, QSortFilterProxyModel
)


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
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setPopup(self.view())
        self.setCompleter(self.completer)
        self.pFilterModel = QSortFilterProxyModel(self)

        # set size policy ( this will ignore the weird resizing effects)
        size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setSizePolicy(size_policy)

    def userFinishedEditing(self):
        is_input_valid = self.isUserInputValid()
        if is_input_valid:
            self.__selectionChangedEmit()
            self._previous_text = self.currentText()
        else:
            self.setCurrentIndexToText(self._previous_text)

    def setCurrentIndexToText(self, text):
        """
        Sets the current index to the text provided.  If no
        match can be found, this will default back to the
        first index.

        If no first index... create '' ?
        """
        self.setExistsFlag(False)

        # get all matches
        items = self.model().findItems(text, Qt.MatchExactly)

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
        # somehow this super makes the node type not resize...
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
        items = self.model().findItems(self.currentText(), Qt.MatchExactly)
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
    def resizeEvent(self, event):
        width = self.width()
        dropdown_width = int(width * 0.35)
        style_sheet = """
        QComboBox {
            border: 1px solid;
            border-color: rgba(0,0,0,0);
            }
            QComboBox::drop-down {
                width: %spx;
            }
        """ % (dropdown_width)
        self.setStyleSheet(style_sheet)
        return QComboBox.resizeEvent(self, event)

    def event(self, event, *args, **kwargs):
        """
        Registering key presses in here as for some reason
        they don't work in the keyPressEvent method...
        """
        if event.type() == QEvent.KeyPress:
            # tab
            if event.key() == Qt.Key_Tab:
                self.next_completion()
                return True

            # shift tab
            elif event.key() == Qt.Key_Tab + 1:
                self.previous_completion()
                return True

            # enter pressed
            elif event.key() in [
                Qt.Key_Return,
                Qt.Key_Enter,
                Qt.Key_Down
            ]:
                self.__selectionChangedEmit()

        return QComboBox.event(self, event, *args, **kwargs)

    def next_completion(self):
        row = self.completer.currentRow()

        # if does not exist reset
        if not self.completer.setCurrentRow(row + 1):
            self.completer.setCurrentRow(0)

        # if initializing
        if self.completer.popup().currentIndex().row() == -1:
            self.completer.setCurrentRow(0)

        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)

    def previous_completion(self):
        row = self.completer.currentRow()
        numRows = self.completer.completionCount()

        # if wrapping
        if not self.completer.setCurrentRow(row - 1):
            self.completer.setCurrentRow(numRows - 1)
        # if initializing
        if self.completer.popup().currentIndex().row() == -1:
            self.completer.setCurrentRow(numRows - 1)

        index = self.completer.currentIndex()
        self.completer.popup().setCurrentIndex(index)
