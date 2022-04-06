""" Example of how to register an event in the undo stack """

Utils.UndoStack.OpenGroup("Undo Example")

NodegraphAPI.CreateNode("PrimitiveCreate", NodegraphAPI.GetRootNode())

Utils.UndoStack.CloseGroup()