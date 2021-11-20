# Simple Tool
The Simple Tool is designed to allow users to create their own Super Tools inside of
the Katana UI.  Simple Tools are essentially a group node with option of being able
to install events through Katanas
[callbacks/events](https://learn.foundry.com/katana/dev-guide/Scripting/CallbacksAndEvents.html)
system.

There will be two main tabs, `Parameters` and `Events`.  The `parameters` tab will be
a new type of Group display that will show the user a Nodegraph on the top which will
be the interior of this tool, and the parameters on the bottom.  The parameters
will show any node inside of the group that is selected.  The `events` section
will be where the user can set up Python events.

As this node is more designed for advanced users, the editing UI can be disabled
by going up to the top `Bebop Parameter Menu` and selecting
`Toggle Two Face Node Appearance`.  Doing this will show the user only the parameters
that have been created using Katana's internal mechanism for creating custom
parameters on nodes.

# Events
When a new event is created, it will only have one parameter by default `script/file`.
Which will determine if this should be executed as a script, or a file.  There  may be
additional parameters added below the **script/file** parameter.  Each parameter
below this point can be considered as a dynamic arg for that specific event, and will
be passed to the actual **script/file** as a local variable based off of their signatures
as defined [here](https://learn.foundry.com/katana/dev-guide/Scripting/CallbacksAndEvents.html)

If these dynamic parameter/arg fields are filled in, then they will act as preflight checks
before running the **script/file**.  If they are empty, then this will mean that they are
disabled, and will be bypassed during preflight checks.

# Python Editor
The python editor will look very similar to the normal Katana Python Editor with the exception
that there are two inputs available at the bottom.  A List Input that will allow the user to select
the script/file that you wish to manipulate.  This input is automatically updated when the `py` button
is pressed.  After changes are made to the script, the `save` button needs to be pressed to push these changes
to disk.

# How to use
1. `Click` "New Event (Q)" button at the bottom left of the interface.
2. `Double click` on new item created with the text `<New Event>` to select the event type.
        You can only have one of each event type.
3. To the right press the `file/script` button to change the type of executable between a script and a file
4. Type code into the python editor and press **save**


