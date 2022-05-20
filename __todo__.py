"""
TODO: Enhancement
    *   PopupBar Widget fix image overlays on show
    *   PopupBar Widget slow
            Move this to a StackWidget that hides/shows on hover
    *   PopupBar Widget closing nodegraphs
            Closing tabs in general needs to run some sort of cleanup handler
    *   VariableManager | Can load multiple patterns
            Remake this?
TODO: cgwidgets
    *   List handler is driving me up the walls
TODO: BUGS
    *   Node Graph
            If no nodegraphs found, will fail on init
    *   Gesture Layers
            - NMC
                Hit box detection
                Not sure if this is worth supporting.  The API is very closed off.
            - Extract API
                    1 Layer
                    Do x on hit
                    Do x on release
    *   Popup Tabs
            - Pin widget for some reason doesn't disappear all the time
                    Can't replicate...
    *   Node Graph Pins
            - Deleting a reference and re adding the same reference does not work
                probably needs to update internal meta data
    *   GSV Manager
            - Events doesn't properly show new scripts
            View didn't update?
            [ERROR python.root]: A TypeError occurred in "GSVManagerTab.py": 'str' object is not callable
            Traceback (most recent call last):
              File "/media/ssd01/dev/python/cgwidgets/cgwidgets/widgets/AbstractWidgets/AbstractListInputWidget.py", line 187, in keyPressEvent
                super(AbstractStringInputWidget, self).keyPressEvent(event)
              File "/media/ssd01/dev/python/cgwidgets/cgwidgets/widgets/AbstractWidgets/AbstractBaseInputWidgets.py", line 59, in keyPressEvent
                self.userFinishedEditing()
              File "/media/ssd01/dev/python/cgwidgets/cgwidgets/widgets/InputWidgets/InputWidgets.py", line 102, in userFinishedEditing
                return AbstractListInputWidget.userFinishedEditing(self)
              File "/media/ssd01/dev/python/cgwidgets/cgwidgets/widgets/AbstractWidgets/AbstractInputInterface.py", line 132, in userFinishedEditing
                is_valid = self.checkInput()
              File "/media/ssd01/dev/python/cgwidgets/cgwidgets/widgets/AbstractWidgets/AbstractInputInterface.py", line 109, in checkInput
                validation = self._validate_user_input()
              File "/media/ssd01/dev/katana/KatanaWidgets/MultiTools/StateManagerTabs/GSVManagerTab/Tab/GSVManagerTab.py", line 338, in validateGSVEntry
                if option in gsvutils.getGSVOptions(self.gsv(), return_as=gsvutils.STRING):
            TypeError: 'str' object is not callable
"""
