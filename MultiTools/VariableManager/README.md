# Variable Manager
The Variable Manager is an all in one place for a user to manage a GSV switch.
Rather than having to setup `Variable Switches` and `VariableEnabledGroups`.  The
Variable Manager will control the GSV flow for an entire section of the Nodegraph
for a specific GSV. It will do this by allowing users to create new GSV branches,
and containers for those branches to easily manage the inheritance between them.

There is also a separate local publishing system that can be used.  This was probably
a rather ambitious project, and the results of the local publishing system may still be buggy.

# Parameters
![](VariableManagerDiagram.png)
### 1. GSV
Which GSV should be used.  If the user selects a GSV that doesn't exist, it will
automagically be created.

### 2. Node Type


### 3. Save location
This is the location that the user can publish/load `blocks` and `patterns` to.

### 4. Organizer
Area for the user to organize the GSV Patterns.

Items can be drag/dropped to alter the Graph State flow.  Anything that is done in a `block`
will effect all of its descendants.  For example, a change in `block02` will effect `pattern02,
pattern04, pattern05`.

Patterns are unique, and there can only be one pattern.  Note if you load a block
in with a pattern, it will allow duplicate patterns.  This is a bug.

#### Item Types
There are two types of items, `patterns` and `blocks`
   1. Patterns relate to one GSV pattern
   2. Blocks are containers of patterns/blocks
   <br /> Each item has a node of the type specified in the `Node Type (2)` parameter
       associated with it.  When the user clicks an item, it will display this node in
       the parameters display field (7)
   3. The nodes associated with the items will are not directly reference parent nodes, and so
        the inheritance will have to be manually setup.  However, what is done in the parent
        will also effect its children.  For example, making an adjustment in `block01` will also
        effect `pattern01` and `pattern03`.

#### Publishing
1. Loading <br />Users can load patterns/blocks by `clicking` on the **version number** under the corresponding 
block/pattern type.  This will bring up a loading menu.
2. Saving <br /> Users can save a block or pattern by `RMB` and going to `Publish Pattern` or `Publish Block`.
3. Options <br />The publish widget will have the same options for saving/loading
   1. A besterest button, to determine that this is a version that should be used
   2. A text field
   3. Accept/Cancel buttons (can also be pressed with `esc/enter`)

### 5. Nodegraph
This is only available when the Node Type is set to `Group` and will display the contents of the Group.

### 6. Pattern / Block creation area
Area where the user can create new `blocks/patterns`.
1. To switch between `block/pattern` mode, click on the green `P` or blue `B` to the left of the field. 
2. Users can press `Ctrl+Shift` to temporarily switch between blocks/patterns.
3. To create a new `block/pattern` press `enter` or the `:)` to the right.
4. If the user creates a pattern that does not exist, it will automagically be created for them.

### 7. Parameters Display
This will display the parameters of the currently selected item.

If the `Node Type`is set to `Group` then this will display the selected nodes in the Nodegraph Area.


# Note
This is very  old crappy code.  It's some of the first I've ever written, however the benefits of
the tool are still valid.  This tool really needs a complete overhaul, as I really have no idea
how it works anymore, except for that most of the bugs have been worked out.

Most likely you will find bugs in the publishing system.  That entire thing is a nightmare, and was
a horrible idea.