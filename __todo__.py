"""
TODO: Enhancement
    *   PopupBar Widget fix image overlays on show
    *   PopupBar Widget slow
            1. ) Test with a StackedWidget that shows/hides on hover.
                Rather than moving the widgets
            2.) Freeze handler on event filter
                    So that all events are bypassed before close, and until after open
    *   PopupBar Widget closing nodegraphs
            Closing tabs in general needs to run some sort of cleanup handler
    *   VariableManager | Can load multiple patterns
            Remake this?
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


"""
