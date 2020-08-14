# uncompyle6 version 3.2.5
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.12 (default, Jul 21 2020, 15:19:50) 
# [GCC 5.4.0 20160609]
# Embedded file name: software_python/QT4Widgets/v0/PythonConsole.py
# Compiled at: 2020-04-28 06:32:12
"""A widget that provides an interactive Python session

Provides two widgets for interacting with the Python session.
InteractivePython, provides a bare bones simple entry and output text widget
FullInteractivePython, provides a full menu and bigger editor
"""
"""
/opt/katana/3.6v1/bin/python/UI4/Manifest.pyc
/opt/katana/3.6v1/bin/python/UI4/software_python/QT4Widgets/v0/TestIndent.pyc
"""
from UI4.Manifest import NodegraphAPI, QtCore, QtGui, QtWidgets
import UI4, sys, code, os, traceback, weakref, re
from TextIndent import Reindent, CountWhitespaceToTabStop
import rlcompleter

__all__ = [
    'InteractivePython', 'FullInteractivePython']
_TAB_WIDTH = 4


class FullInteractivePython(QtWidgets.QFrame):
    """A frame with a menu and a script widget."""

    def __init__(self, *args, **kwargs):
        env = None
        if kwargs.has_key('environment'):
            env = kwargs['environment']
            del kwargs['environment']
        QtWidgets.QFrame.__init__(self, *args)
        self.__layout = QtWidgets.QVBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__buildChildren()
        self.__buildCommands()
        self.__buildMenuBar()
        if env:
            self.scriptWidget().setEnvironment(env)
        return

    def getMenuBar(self):
        """
        @rtype: C{QtWidgets.QMenuBar}
        @return: The widget's menu bar.
        """
        return self.__menuBar

    def scriptWidget(self):
        """
        @rtype: C{InteractivePython}
        @return: The widget that is contained in this frame to implement its
            Python scripting functionality.
        """
        return self.__scriptWidget

    def __buildChildren(self):
        self.__scriptWidget = InteractivePython(self)
        self.__layout.addWidget(self.__scriptWidget, 1)

    def __buildCommands(self):
        cutShortcut = QtGui.QKeySequence(QtGui.QKeySequence.Cut).toString()
        copyShortcut = QtGui.QKeySequence(QtGui.QKeySequence.Copy).toString()
        pasteShortcut = QtGui.QKeySequence(QtGui.QKeySequence.Paste).toString()
        self.editClearAction = QtWidgets.QAction('Clear', self)
        self.editCutAction = QtWidgets.QAction('Cut\t%s' % cutShortcut, self)
        self.editCopyAction = QtWidgets.QAction('Copy\t%s' % copyShortcut, self)
        self.editPasteAction = QtWidgets.QAction('Paste\t%s' % pasteShortcut, self)
        self.preferencesAction = QtWidgets.QAction('Preferences', self)
        self.sourceFileAction = QtWidgets.QAction('Source File...', self)
        self.prevHistoryAction = QtWidgets.QAction('History Previous', self)
        self.prevHistoryAction.setShortcut(QtGui.QKeySequence('Alt+Up'))
        self.prevHistoryAction.setShortcutContext(QtCore.Qt.WidgetShortcut)
        self.__scriptWidget.commandWidget().addAction(self.prevHistoryAction)
        self.nextHistoryAction = QtWidgets.QAction('History Next', self)
        self.nextHistoryAction.setShortcut(QtGui.QKeySequence('Alt+Down'))
        self.nextHistoryAction.setShortcutContext(QtCore.Qt.WidgetShortcut)
        self.__scriptWidget.commandWidget().addAction(self.nextHistoryAction)
        self.editClearAction.triggered.connect(self.__scriptWidget.clear)
        self.editCutAction.triggered.connect(self.__scriptWidget.cut)
        self.editCopyAction.triggered.connect(self.__scriptWidget.copy)
        self.editPasteAction.triggered.connect(self.__scriptWidget.paste)
        self.preferencesAction.triggered.connect(self.__on_preferencesAction_triggered)
        self.prevHistoryAction.triggered.connect(self.__scriptWidget.prevHist)
        self.nextHistoryAction.triggered.connect(self.__scriptWidget.nextHist)
        self.sourceFileAction.triggered.connect(self.__sourceFileCallback)

    def __buildMenuBar(self):
        """Build the menu bar for the ScriptWidget.
        Returns a new QtWidgets.QMenuBar parented to self."""
        self.__menuBar = QtWidgets.QMenuBar(self)
        self.__layout.setMenuBar(self.__menuBar)
        self.__scriptMenu = QtWidgets.QMenu('Script')
        self.__menuBar.addMenu(self.__scriptMenu)
        self.__scriptMenu.addAction(self.sourceFileAction)
        self.__scriptMenu.addSeparator()
        self.__scriptMenu.addAction(self.prevHistoryAction)
        self.__scriptMenu.addAction(self.nextHistoryAction)
        self.__editMenu = QtWidgets.QMenu('Edit')
        self.__menuBar.addMenu(self.__editMenu)
        self.__editMenu.addAction(self.editClearAction)
        self.__editMenu.addSeparator()
        self.__editMenu.addAction(self.editCutAction)
        self.__editMenu.addAction(self.editCopyAction)
        self.__editMenu.addAction(self.editPasteAction)
        self.__editMenu.addSeparator()
        self.__editMenu.addAction(self.preferencesAction)

    def __on_preferencesAction_triggered(self):
        from UI4.KatanaPrefs import PrefNames
        UI4.App.Preferences.ShowPreferencesDialog(category=PrefNames.TERMINAL)

    def __sourceFileCallback(self):
        """Callback for File/Source menu command.
        Uses a QFileDialog to get the filename, then reads in the file,
        and executes it in the running session."""
        filePicker = QtWidgets.QFileDialog(self, 'Run a script')
        if QtWidgets.QDialog.Rejected == filePicker.exec_():
            return
        filename = str(filePicker.selectedFiles()[0])
        self.__scriptWidget.printMessage('Sourcing %s\n' % filename)
        commandString = file(filename, 'rt').read()
        self.__scriptWidget.runCommand(commandString)


class InteractivePython(QtWidgets.QFrame):
    """A general Python scripting GUI using QT."""

    class CustomInterp(code.InteractiveInterpreter):

        def __init__(self, outputwidget):
            self.output = outputwidget

    def __init__(self, *args):
        """Construct a ScriptWidget"""
        QtWidgets.QFrame.__init__(self, *args)
        self.__useAutoCompletionPopup = False
        self.__layout = QtWidgets.QVBoxLayout(self)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__environment = {}
        self.interp = code.InteractiveInterpreter(self.__environment)
        self.historyPos = 0
        self.history = []
        self.__splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        self.__splitter.setHandleWidth(10)
        self.__layout.addWidget(self.__splitter)
        self.__buildResultWidget()
        self.__buildCommandWidget()
        self.__splitter.setSizes([3, 2])
        self.stdout = self._ScriptStdout(self.__resultWidget)
        self.stderr = self._ScriptStderr(self.__resultWidget, sys.stdout)
        self.stdin = self._ScriptStdin(self)
        palette = self.__resultWidget.palette()
        self.__promptTextFormat = QtGui.QTextCharFormat()
        self.__promptTextFormat.setFontWeight(QtGui.QFont.Bold)
        self.__promptTextFormat.setForeground(palette.color(QtGui.QPalette.BrightText))
        resultWidgetCharFormat = self.__resultWidget.currentCharFormat()
        self.__cmdTextFormat = QtGui.QTextCharFormat(resultWidgetCharFormat)
        self.__msgTextFormat = QtGui.QTextCharFormat(resultWidgetCharFormat)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def setUseAutoCompletionPopup(self, useAutoCompletionPopup):
        self.__useAutoCompletionPopup = useAutoCompletionPopup

    def setEnvironment(self, env):
        """Set the global symbol table used when executing commands."""
        self.__environment.clear()
        self.__environment.update(env)

    def getEnvironment(self):
        """Returns the current execution environment"""
        return self.__environment

    def printMessage(self, messageString):
        """Print a message to the result area."""
        self.__resultWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        self.__resultWidget.textCursor().insertText(messageString, self.__msgTextFormat)

    def cut(self):
        if self.__commandWidget.textCursor().selectedText() is not None:
            self.__commandWidget.cut()
        else:
            self.__resultWidget.cut()
        return

    def copy(self):
        if self.__commandWidget.textCursor().selectedText() is not None:
            self.__commandWidget.copy()
        else:
            self.__resultWidget.copy()
        return

    def paste(self):
        self.__commandWidget.paste()

    def clear(self):
        self.__resultWidget.clear()

    def prevHist(self):
        self.historyPos = min(self.historyPos + 1, len(self.history))
        if not self.historyPos:
            self.__commandWidget.clear()
        else:
            self.__commandWidget.setText(self.history[-self.historyPos])
            self.__commandWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def nextHist(self):
        self.historyPos = max(self.historyPos - 1, 0)
        if not self.historyPos:
            self.__commandWidget.clear()
        else:
            self.__commandWidget.setText(self.history[-self.historyPos])
            self.__commandWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    assMidgetCmd = re.compile('^[iI] want an (a(ss|rse)midget)$')

    def runCommand(self, commandString):
        eggmatch = self.assMidgetCmd.match(commandString)
        if eggmatch:
            node = NodegraphAPI.CreateNode('PrimitiveCreate', NodegraphAPI.GetRootNode())
            if not node:
                return
            node.setName(eggmatch.group(1))
            p = node.getParameter('type')
            p.setValue('gnome', 0)
            NodegraphAPI.SetNodePosition(node, (100, -50))
            return
        self.history.append(commandString)
        self.history = self.history[-20:]
        self.historyPos = 0
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        sys.stdin = self.stdin
        try:
            self.__resultWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
            try:
                result = None
                with NodegraphAPI.SynchronousContext():
                    try:
                        result = eval(commandString, self.__environment, self.__environment)
                    except SyntaxError:
                        exec
                        commandString in self.__environment

                if result is not None:
                    outputMessage = str(result)
                    self.__environment['_'] = outputMessage
                    self.stdout.write(outputMessage + '\n')
            except:
                exceptionType, exception, tb = sys.exc_info()
                entries = traceback.extract_tb(tb)
                entries.pop(0)
                if entries:
                    filename, lineNumber, functionName, text = entries[0]
                    if filename == '<string>' and functionName == '<module>' and text is None:
                        if lineNumber == 1:
                            entries.pop(0)
                        else:
                            commandLines = commandString.splitlines()
                            if lineNumber >= 1 and lineNumber <= len(commandLines):
                                errorLine = commandLines[lineNumber - 1]
                                entries[0] = (filename, lineNumber,
                                              functionName, errorLine)
                errorLines = list()
                if entries:
                    errorLines += traceback.format_list(entries)
                errorLines += traceback.format_exception_only(exceptionType, exception)
                self.stderr.write(('').join(errorLines).strip() + '\n')

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin
            self.__resultWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

        return

    def commandWidget(self):
        return self.__commandWidget

    def resultWidget(self):
        return self.__resultWidget

    def __buildResultWidget(self):
        """Build the result widget; where the stdout and stderr are printed."""
        self.__resultWidget = self._ResultWidget(self.__splitter)
        self.__resultWidget.setForegroundRole(QtGui.QPalette.Text)
        self.__resultWidget.setProperty('fixedWidthFont', True)
        self.__resultWidget.setMinimumHeight(40)

    def __buildCommandWidget(self):
        """Build the command widget; where the commands come from."""
        self.__commandWidget = self._CommandEntryWidget(self.__splitter)
        self.__commandWidget.setProperty('fixedWidthFont', True)
        self.__commandWidget.setMinimumHeight(28)
        self.__commandWidget.enterPressed.connect(self._enterCommand)
        self.__commandWidget.tabPressed.connect(self.on_commandWidget_tabPressed)
        self.__commandWidget.backtabPressed.connect(self._unindentCommand)

    def __echoCommand(self, commandString):
        """
        Prints the given command string to the result area.

        Formats the command string (including insertion of > characters)
        automagically.
        """
        lines = commandString.splitlines()
        if lines and not lines[-1].strip():
            del lines[-1]
        self.__resultWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
        for line in lines:
            textCursor = self.__resultWidget.textCursor()
            textCursor.insertText('>>> ', self.__promptTextFormat)
            textCursor.insertText('%s\n' % line, self.__cmdTextFormat)

    def _enterCommand(self):
        """Callback from QT when the command entry area has the enter key pressed."""
        cursor = self.__commandWidget.textCursor()
        commandString = str(self.__commandWidget.toPlainText())
        if cursor.hasSelection():
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            commandString = commandString[start:end]
        else:
            self.__commandWidget.setText('')
            self.__commandWidget.textCursor().setPosition(0)
        self.__echoCommand(commandString)
        self.runCommand(commandString)

    __identifier = re.compile('([a-zA-Z0-9_.]*)$')

    def _autoComplete(self):
        index = self.__commandWidget.textCursor().position()
        text = str(self.__commandWidget.toPlainText())[:index]
        m = self.__identifier.search(text)
        if m is not None:
            text = m.group(1)
        if not text:
            return False
        orig_len = len(text)
        completer = rlcompleter.Completer(self.__environment).complete
        opts = []
        seen = {}
        try:
            state = 0
            while True:
                r = completer(text, state)
                state += 1
                if r is None:
                    break
                if r in seen:
                    continue
                seen[r] = True
                opts.append(r)

        except TypeError:
            pass

        if len(opts) == 1:
            if opts[0] != text:
                self.__commandWidget.insertPlainText(opts[0][orig_len:])
        else:
            if len(opts) > 1:
                cp = os.path.commonprefix(opts)
                if len(cp) > orig_len:
                    self.__commandWidget.insertPlainText(cp[orig_len:])
                self.__resultWidget.textCursor().insertText('[' + ('  ').join(opts) + ']\n', self.__msgTextFormat)
                self.__resultWidget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
            else:
                return False
        return True

    def _unindentCommand(self):
        Reindent(self.__commandWidget, True, spacing=_TAB_WIDTH)

    def _indentCommand(self):
        """Callback from QT when the command entry area has the tab key pressed."""
        Reindent(self.__commandWidget, False, spacing=_TAB_WIDTH)

    def on_commandWidget_tabPressed(self):
        if not self.__useAutoCompletionPopup:
            cursor = self.__commandWidget.textCursor()
            if not cursor.hasSelection() and cursor.positionInBlock() > 0:
                if self._autoComplete():
                    return
        self._indentCommand()

    class _ScriptStdout:

        def __init__(self, resultWidget):
            self.__resultWidgetRef = weakref.ref(resultWidget)
            self.stdoutTextFormat = QtGui.QTextCharFormat()
            self.stdoutTextFormat.setForeground(resultWidget.palette().color(resultWidget.foregroundRole()))

        def write(self, msg):
            widget = self.__resultWidgetRef()
            if not widget:
                return
            widget.textCursor().insertText(msg, self.stdoutTextFormat)

        def flush(self):
            pass

    class _ScriptStderr:

        def __init__(self, resultWidget, realstderr):
            self.__resultWidgetRef = weakref.ref(resultWidget)
            self.errorTextFormat = QtGui.QTextCharFormat()
            self.errorTextFormat.setFontWeight(QtGui.QFont.Normal)
            self.errorTextFormat.setForeground(QtGui.QColor(221, 30, 30))

        def write(self, msg):
            widget = self.__resultWidgetRef()
            if not widget:
                return
            widget.textCursor().insertText(msg, self.errorTextFormat)
            widget.textCursor().movePosition(QtGui.QTextCursor.End)

        def flush(self):
            pass

    class _ScriptStdin:

        def __init__(self, scriptWidget):
            pass

    class _CommandEntryWidget(QtWidgets.QTextEdit):
        enterPressed = QtCore.pyqtSignal()
        returnPressed = QtCore.pyqtSignal()
        backtabPressed = QtCore.pyqtSignal()
        tabPressed = QtCore.pyqtSignal()

        def __init__(self, *args):
            QtWidgets.QTextEdit.__init__(self, *args)
            self.setAcceptRichText(False)

        def _backspaceSpacesToTabstop(self):
            wsToNextTabStop = CountWhitespaceToTabStop(self, previousTab=True, spacing=_TAB_WIDTH)
            if wsToNextTabStop:
                cursor = self.textCursor()
                for _ in xrange(wsToNextTabStop):
                    cursor.deletePreviousChar()

                self.setTextCursor(cursor)
                return True
            return False

        def _deleteSpacesToTabstop(self):
            wsToNextTabStop = CountWhitespaceToTabStop(self, previousTab=False, spacing=_TAB_WIDTH)
            if wsToNextTabStop:
                cursor = self.textCursor()
                for _ in xrange(wsToNextTabStop):
                    self.textCursor().deleteChar()

                self.setTextCursor(cursor)
                return True
            return False

        def keyPressEvent(self, keyEvent):
            if keyEvent.key() == QtCore.Qt.Key_Enter or keyEvent.key() == QtCore.Qt.Key_Return and keyEvent.modifiers() & QtCore.Qt.ControlModifier:
                self.enterPressed.emit()
            else:
                if keyEvent.key() == QtCore.Qt.Key_Return and keyEvent.modifiers() & QtCore.Qt.ShiftModifier:
                    returnKeyEvent = QtGui.QKeyEvent(keyEvent.type(), QtCore.Qt.Key_Return, QtCore.Qt.NoModifier)
                    keyEvent.accept()
                    QtWidgets.QTextEdit.keyPressEvent(self, returnKeyEvent)
                    self.returnPressed.emit()
                else:
                    if keyEvent.key() == QtCore.Qt.Key_Return:
                        QtWidgets.QTextEdit.keyPressEvent(self, keyEvent)
                        self.returnPressed.emit()
                    else:
                        if keyEvent.key() == QtCore.Qt.Key_Backtab:
                            self.backtabPressed.emit()
                        else:
                            if keyEvent.key() == QtCore.Qt.Key_Tab:
                                keyEvent.accept()
                                if keyEvent.modifiers() == QtCore.Qt.NoModifier:
                                    self.tabPressed.emit()
                            else:
                                if keyEvent.key() == QtCore.Qt.Key_Space and keyEvent.modifiers() == QtCore.Qt.ControlModifier:
                                    keyEvent.ignore()
                                else:
                                    if keyEvent.key() == QtCore.Qt.Key_Backspace and keyEvent.modifiers() == QtCore.Qt.NoModifier and not self.textCursor().hasSelection():
                                        if self._backspaceSpacesToTabstop():
                                            keyEvent.accept()
                                        else:
                                            QtWidgets.QTextEdit.keyPressEvent(self, keyEvent)
                                    else:
                                        if keyEvent.key() == QtCore.Qt.Key_Delete and keyEvent.modifiers() == QtCore.Qt.NoModifier and not self.textCursor().hasSelection():
                                            if self._deleteSpacesToTabstop():
                                                keyEvent.accept()
                                            else:
                                                QtWidgets.QTextEdit.keyPressEvent(self, keyEvent)
                                        else:
                                            QtWidgets.QTextEdit.keyPressEvent(self, keyEvent)

        def keyReleaseEvent(self, keyEvent):
            if keyEvent.key() == QtCore.Qt.Key_Alt:
                self.setFocus()

        def dragEnterEvent(self, event):
            if event.mimeData().hasFormat('python/text'):
                event.accept()
                return
            return QtWidgets.QTextEdit.dragEnterEvent(self, event)

        def dragMoveEvent(self, event):
            if event.mimeData().hasFormat('python/text'):
                event.accept()
                return
            return QtWidgets.QTextEdit.dragMoveEvent(self, event)

        def dropEvent(self, event):
            if event.mimeData().hasFormat('python/text'):
                text = [
                    None]
                if event.keyboardModifiers() & QtCore.Qt.ControlModifier:
                    menu = QtWidgets.QMenu(None)
                    formatCount = 0
                    for format in event.mimeData().formats():
                        format = str(format)
                        if format.startswith('python/'):
                            formatCount += 1
                            myText = str(event.mimeData().data(format))

                            def go(myText=myText):
                                text[0] = myText

                            menu.addAction(myText, go)

                    if formatCount > 1:
                        text[0] = ''
                        menu.exec_(self.mapToGlobal(event.pos()))
                data = QtCore.QMimeData()
                if isinstance(text[0], str):
                    data.setText(text[0])
                else:
                    data.setText(str(event.mimeData().data('python/text')))
                newEvent = QtGui.QDropEvent(event.pos(), event.possibleActions(), data, event.mouseButtons(),
                                            event.keyboardModifiers(), event.type())
                return QtWidgets.QTextEdit.dropEvent(self, newEvent)
            return QtWidgets.QTextEdit.dropEvent(self, event)

        def _sanitiseMimeData(self, mimeData):
            if mimeData.hasText():
                tabbedString = unicode(mimeData.text()).expandtabs(_TAB_WIDTH)
                mimeData = QtCore.QMimeData()
                mimeData.setText(tabbedString)
            return mimeData

        def insertFromMimeData(self, mimeData):
            sanitised = self._sanitiseMimeData(mimeData)
            return QtWidgets.QTextEdit.insertFromMimeData(self, sanitised)

    class _ResultWidget(QtWidgets.QTextEdit):

        def __init__(self, *args):
            QtWidgets.QTextEdit.__init__(self, *args)
            self.setReadOnly(True)

        def keyPressEvent(self, keyEvent):
            if keyEvent.key() == QtCore.Qt.Key_Space:
                if keyEvent.modifiers() in (QtCore.Qt.NoModifier,
                                            QtCore.Qt.ControlModifier):
                    keyEvent.ignore()
                    return
            else:
                if keyEvent.matches(QtGui.QKeySequence.Cut):
                    self.copy()
                    return
            QtWidgets.QTextEdit.keyPressEvent(self, keyEvent)


if __name__ == '__main__':
    theApp = QtWidgets.QApplication(sys.argv)
    w = FullInteractivePython(None)
    w.show()
    theApp.lastWindowClosed.connect(theApp.quit)
    theApp.exec_()