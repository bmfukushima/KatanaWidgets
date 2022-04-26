import math
import os
import re

try:
    from Katana import Utils, UI4
except ModuleNotFoundError:
    pass

NODE = "node"
PARAM = "param"

def createValueParam(self, name):
    """Create a katana param"""
    factory = UI4.FormMaster.KatanaFactory.ParameterWidgetFactory
    locationPolicy = UI4.FormMaster.CreateParameterPolicy(None, self.node.getParameter(name))
    w = factory.buildWidget(self, locationPolicy)
    return w


def createUniqueHash(unique_hash, location):
    """
    Looks at a specific directory on disk and creates a unique hash
    for that location.

    unique_hash (str): original hash to look for.  If it is found it will continue
        hashing itself until a unique one is found.
    location (str): path on disk to where to find the unique hash
    """
    unique_hash = int(math.fabs(hash(str(unique_hash))))
    if str(unique_hash) in os.listdir(location):
        unique_hash = int(math.fabs(hash(str(unique_hash))))
        return createUniqueHash(str(unique_hash), location)
    return unique_hash


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


def getAllVisibleTabs():
    """ Gets all of the current top level tabs

    Returns (list): of KatanaTabs """
    from Katana import UI4
    tabs = UI4.App.Tabs.GetAllTabs()
    visible_tab_list = []
    for tab in tabs:
        if hasattr(tab, 'isVisible'):
            try:
                if tab.isVisible():
                    visible_tab_list.append(tab)
            except RuntimeError:
                # tab deleted?
                pass
    return visible_tab_list


def getCurrentTab():
    """ Returns the current tab that is under the cursor

    Note:
        Doing a positional check, as when suing the ScriptEditor,
        the PopupDisplay will block the underCursor from registering.
    Returns (KatanaTab)"""
    from qtpy.QtGui import QCursor
    for tab in getAllVisibleTabs():
        tab_xpos = tab.parent().mapToGlobal(tab.pos()).x()
        tab_ypos = tab.parent().mapToGlobal(tab.pos()).y()
        tab_w = tab.width()
        tab_h = tab.height()

        cursor_pos = QCursor.pos()
        cursor_xpos = cursor_pos.x()
        cursor_ypos = cursor_pos.y()

        # check ypos
        if (tab_ypos < cursor_ypos < tab_ypos + tab_h
            and tab_xpos < cursor_xpos < tab_xpos + tab_w
        ):
            return tab

        # if tab.underMouse():
        #     return tab

    return None


def getFontSize():
    """
    Gets the current font size in Katana.  This is useful for dynamically resizing the application.

    """
    from qtpy.QtWidgets import QApplication
    from cgwidgets.utils import getFontSize

    font_size = getFontSize(QApplication.instance())
    return font_size


def getValidName(name):
    return re.sub('(^[0-9]+|[^a-zA-Z0-9_])', '_', name)


def isLicenseValid():
    """ Determines if there is a valid license located at either
        $KATANABEBOP/license.txt
            or
        $KATANABEBOPLICENSEFILE
    """
    if "KATANABEBOPISVALID" in os.environ:
        if os.environ["KATANABEBOPISVALID"] == ":)": return True
        else: return False

    else:
        from cgwidgets.utils import checkLicenseFiles, licenseDate
        license_files = []
        # current_dir = os.path.dirname(os.path.realpath(__file__))
        # local_license_file = f"{current_dir}/license.txt"
        local_license_file = os.environ["KATANABEBOP"] + "/license.txt"
        license_files.append(local_license_file)
        try:
            license_files.append(os.environ["KATANABEBOPLICENSE"])
        except KeyError:
            pass
        print(license_files)
        is_license_valid, filepath = checkLicenseFiles(license_files)
        if is_license_valid:
            expiry_date = licenseDate(filepath)
            print(f"Katana Bebop license found at {filepath} \n\t |- Valid until {expiry_date}")
            os.environ["KATANABEBOPISVALID"] = ":)"
        else:
            print(f"No valid licenses found for Katana Bebop")
            os.environ["KATANABEBOPISVALID"] = ":("
        return is_license_valid


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


def makeUndoozable(func, main_widget, _action_string, _undo_type, *args, **kwargs):
    """
    This will encapsulate the function as an undo stack.

    Args:
        func (function): the function to encapsulate as an undoable operation
        _action_string (str): the name of the item acted on to be displayed
        _undo_type (str): The type of undo operation that just happened
        main_widget (VariableManagerWidget): The main widget called
            with the getMainWidget() util...

    """
    main_widget.suppress_updates = True
    node = main_widget.node()

    # start recording undo operation
    Utils.UndoStack.OpenGroup(
        "{node} | {undo_type} | {action}".format(
            node=node.getName(),
            undo_type=_undo_type,
            action=_action_string
        )
    )

    # register undo hack...
    if Utils.UndoStack.IsUndoEnabled():
        node.getParameter('undoozable').setValue('my oh my what a hack2', 0)

    # All of this shit so I can literally do this...
    func(*args, **kwargs)

    # register undo hack...
    if Utils.UndoStack.IsUndoEnabled():
        node.getParameter('undoozable').setValue('my oh my what a hack1', 0)

    # stop recording
    Utils.UndoStack.CloseGroup()

    # disable capture for remaining updates
    Utils.UndoStack.DisableCapture()
    Utils.EventModule.ProcessAllEvents()
    Utils.UndoStack.EnableCapture()

    main_widget.suppress_updates = False


def suppressUndooz(func, *args, **kwargs):
    """
    Suppresses the undo stack for the function provided:

    func (function): function to have the undo stack disable
    """
    Utils.UndoStack.DisableCapture()
    func(*args, **kwargs)
    Utils.EventModule.ProcessAllEvents()
    Utils.UndoStack.EnableCapture()


def makeUndoozDisappear(index=0):
    """
    Clears an undo event from the undo stack.  This will most
    notably be used in the cancel events for the gsv menus.

    Note:
        The undo stack is popped in the reverse order.  So the index 0
        will actually remove the last undo operation
    """
    Utils.UndoStack._UndoStack.pop(index)
    Utils.UndoStack._TriggerUndoCallbacks()





