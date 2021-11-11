# Global Events Tab
The Global Events Tab allows user to create Python events that can be run at the global
of their projects.  These Python events will be stored on the Katana scene itself, and will
be installed/uninstalled when the scene is loaded/closed

This tab is actually a widget that is stored on Katana's main instance located at 
`UI4.App.MainWindow.GetMainWindow()` as the attribute `global_events_widget`.  This means
that if there are multiple tabs of this type open, it will automagically only be displayed
in one Tab.  The reason behind this is due to the fact that when these events are installed,
in order to destroy them correctly, we need to track the original event.  Without a singular widget
to track these, it would be nearly impossible to install/uninstall the correct events.

There will be two main areas of this widget, the event's creation portion on the top, and the
python editor on the bottom.  Either area can consume the entire space of this widget by
pressing &nbsp;\`&nbsp; key located above `tab`, and can return back to split view mode
by pressing the `escape` key.

# Data
Data for each event is stored as a dictionary on the root node under the parameter 
`KatanaBebop.GlobalEventsData.data`.

When the user creates a new python event, a new script will be created at 
`KatanaBebop.GlobalEventsData.scripts.{event_name}`.

# How to use
1. `Click` "New Event (Q)" button at the bottom left of the interface.
2. `Double click` on new item created with the text `<New Event>` to select the event type.
        You can only have one of each event type.
3. To the right press the `file/script` button to change the type of executable between a script and a file
4. Type code into the python editor and press **save**
