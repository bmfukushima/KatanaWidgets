import math
import os
try:
    from Katana import Utils, UI4
except ImportError:
    import Utils, UI4


def createUniqueHash(thash, location):
    thash = int(math.fabs(hash(str(thash))))
    if str(thash) in os.listdir(location):
        thash = int(math.fabs(hash(str(thash))))
        return createUniqueHash(str(thash), location)
    return thash


def getMainWidget(widget):
    try:
        name = widget.__name__()
        if name == 'VariableManagerMainWidget':
            return widget
        else:
            return getMainWidget(widget.parent())
    except AttributeError:
        return getMainWidget(widget.parent())


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
    node = main_widget.node

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
