"""
TODO: BUGS
    *   NetworkMaterialCreate | segfault after closing a custom Nodegraph
            Has something to do with the clean up event on the AbstractNodegraphWidget
    *   PopupWidgets | Having issue with popups and closing.
            1.) Seems to close the widget when the popup happens under the cursor when using the keyboard.
                Python widgets auto completer
            2.) Selecting an item in the popup when not hovering over the widget closes.
                View, select camera
    *   VariableManager | Can load multiple patterns
            When loading blocks, if it has a pattern that already exists, it will create a duplicate pattern.




"""

# AbstractParametersDisplayWidget | Error Log
"""
[ERROR python.root]: An AttributeError occurred in "Node2DGroup.py": 'Node2DGroupFormWidget' object has no attribute '_Node2DGroupFormWidget__originalPopdownIndent'
    Traceback (most recent call last):
      File "software_python/QT4FormWidgets/v0/ValuePolicy.py", line 401, in _HandleQueuedChanges
      File "Utils/v5/WeakMethod.py", line 37, in __call__
      File "FormMaster/Editors/Teleparam.py", line 135, in valueChangedEvent
      File "FormMaster/Editors/Teleparam.py", line 101, in __buildHostedWidget
      File "FormMaster/KatanaFactory.py", line 341, in buildWidget
      File "software_python/QT4FormWidgets/v0/WidgetFactory.py", line 107, in buildWidget
      File "FormMaster/Editors/Node2DGroup.py", line 30, in __init__
      File "FormMaster/Editors/NodeGroup.py", line 104, in __init__
      File "FormMaster/Editors/HideTitleGroup.py", line 35, in __init__
      File "/media/ssd01/dev/katana/KatanaWidgets/ParameterMenu/CreateParametersMenu.py", line 29, in showPopdownWithCustomMenu
        QT4FormWidgets.GroupFormWidget.originalShowPopdown(self, value)
      File "software_python/QT4FormWidgets/v0/GroupFormWidget.py", line 109, in showPopdown
      File "software_python/QT4FormWidgets/v0/FormWidget.py", line 830, in showPopdown
      File "software_python/QT4FormWidgets/v0/FormWidget.py", line 792, in __buildPopdownArea
      File "FormMaster/Editors/Node2DGroup.py", line 76, in _popdownCreated
    AttributeError: 'Node2DGroupFormWidget' object has no attribute '_Node2DGroupFormWidget__originalPopdownIndent'
"""