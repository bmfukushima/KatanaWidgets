#IRF Manager Tab
The IRF (Interactive Render Filter) Tab is an all in one place where users can go to
create/edit, activate, and view their IRF's.

There are three main portions of this tab, view, activate, and create.

# Activate
Simply drag/drop filters from the **available filters** side into the **active filters**
side in order to enable them.

In order to remove a filter, select it, and delete it from the **active filters** side

Entire categories can be enabled/disabled by dragging/dropping or deleting them.

# Create
Users can create/modify IRFs by going to the **Create Tab** and using `RMB --> Create New Filter`
to create a new render filter.

Selecting an item, will display a mini nodegraph below, which will be the **Group** node which
will be the container for this **render filter**.  All nodes created in this context will
be used in the render filter.  Selecting a **node** in this context will display the
parameters 

New **categories** can be created in a similar fashion, by going to `RMB --> Create New Category`.
Categories cannot be destroyed, however they will automatically be destroyed during the 
next update when they have no children.  

**Render Filters** can be **drag/dropped** into different categories to have their default category changed.
Categories, however cannot be drag/dropped.

To change a **category/render filters name** simply `Double Click` on the item and enter a new name.

The `Node` parameter at the top will be the name of the `InteractiveRenderFilter` node tha
is currently being used when creating new filters.  By default if one does not exist, this
will create a new one for you.