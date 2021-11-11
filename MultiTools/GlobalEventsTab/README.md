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

# Data
Data for each event is stored as a dictionary on the root node under the parameter 
`KatanaBebop.GlobalEventsData.data`.

When the user creates a new python event, a new script will be created at 
`KatanaBebop.GlobalEventsData.scripts.{event_name}`.  Which can be used