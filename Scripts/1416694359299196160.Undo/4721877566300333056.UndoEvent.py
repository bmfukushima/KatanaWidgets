""" Example of how to register a callback when an undo stack event happens """

def undo_openGroup(args):
    print(args)

Utils.EventModule.RegisterCollapsedHandler(undo_openGroup, 'undo_end')