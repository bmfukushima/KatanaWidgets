# Disclaimer
This is my own personal work (Brian Fukushima), and does not represent that of my employer.  All
work done in this library represents my own personal designs, code, resources spent, etc.
Please do not contact my employer with any questions/comments/concerns pertaining to this
library, but rather please contact me directly if you have any questions/comments/concerns.

# Katana Bebop
This repo contains a Katana Resources directory which can be added to the `KATANA_RESOURCES `environment variable.
This repo contains a small collection of my personal tools which have been created to sit as addons for Katana.


### Installation
Install [PIL](https://pypi.org/project/Pillow/)

Append this directory to your `$KATANA_RESOURCES` environment variable.

Install your license file under `$KATANABEBOP/license.txt` or place it in the environment variable `$KATANABEBOPLICENSE`

### Written for
This library is written for [VFX Reference Platform 2021](https://vfxplatform.com/)
  * Ubuntu 20.04
  * Python 3.7.7
  * PyQt 5.15.0
  * Katana 5.x+
  
# Tools
### Tabs
- [Node Graph Pins Tab](Tabs/DesiredStuffTab/README.md)
- [Global Events Tab](MultiTools/GlobalEventsTab/README.md)
- [GSV Manager Tab](MultiTools/StateManagerTabs/GSVManagerTab/README.md)
- [IRF Manager Tab](MultiTools/StateManagerTabs/IRFManagerTab/README.md)
- [State Manager Tab](MultiTools/StateManagerTabs/README.md) +
- [Bookmark Manager Tab](MultiTools/StateManagerTabs/BookmarkManagerTab/README.md) +
- [Node Color Registry Tab](MultiTools/NodeColorRegistryTab/README.md)
- [Popup Bar Tabs](Tabs/PopupBar/README.md)
- [Script Manager Tab](MultiTools/ScriptEditorTab/README.md)

### SuperTools
- [Constraint](SuperTools/Constraint/README.md)
- [Isolate CEL](SuperTools/IsolateCEL/README.md)
- [Node Tree](SuperTools/NodeTree/README.md) +
- [Simple Tool](MultiTools/SimpleTool/README.md)

### Layered Menus
- `N` to access NetworkMaterialCreate/Edits
- `S` to access GSVs

### Swipe Gestures
Are a new way of manipulating nodes/links inside of the legacy node graph. 
In order to use a `Swipe Gesture` you will simple need to press the modifier 
(such as `Q/W/A/etc`) and then press and hold `LMB` as you move the cursor around.
The cursor should then change colors to signify that you're doing a gesture event.

- `Q + LMB` Select links (input)
  - Can continue selection by pressing `Shift + LMB` or `Control + LMB` to add or remove links to the current selection.
- `W + LMB` Select links (output)
- `A + LMB` Align nodes
  - Will align nodes swiped through depending on the direction of the cursor when it passes through the second node.  Each node after will be aligned to that direction
  - If only one node is it, this will perform an auto align up or down depending on the direction of the cursor as it passes through that node.
- `S + LMB` Select nodes
- `X + LMB` Cut links
- `C + LMB` Connect nodes

### UX Enhancements
- Port connector `~` 
  - Detects closest node to cursor
  - `Shift + ~` Will enable continuously port connection selection
  - `Alt + ~` Will disable the warning if a connection already exists
  - If multiple ports are detected a popup will display the ports
    - Can select multiple ports by pressing `Shift` during selection
    - Can press `Shift` to choose multiple ports to connect to.
  - Link Connection
    - Can now drop dots with `D`
    - Can create nodes with `Tab`
- View/Edit parameters `E`
  - `Alt + E` move to `E`
  - `Alt + E` popup parameters tab
  - `Alt + Shift + E` Pinned popup parameters tab
- Closest node to cursor is highlighted
- `Alt + D` disable moved to `D` and `Q`
- `V` node viewed moved to `W`
- Full Screen changed from `Space` to `Ctrl + B`
  - `Space` is now used to increase widget sizes of new KatanaBebop widgets
- `Ctrl + Shift + LMB` Duplicate selected nodes
- `Alt + LMB` Move all nodes above closest node
- `Alt + Shift + LMB` Move all nodes below closest node
- `A` Alignment Menu
- Back/Forward buttons
  - `Back Button` show previous node as view node
  - `Forward Button` show next node view node
  - `Alt + Back Button` show parent node as view node
  - `Alt + Forward Button` show root node as view node
-`Control + G` Show  Grid Settings Dialogue
- `B` Create new backdrop
  - `LMB` Select backdrop and children
  - `Alt + LMB` Select and float backdrop and selected children
  - `Alt + Shift + LMB` Select and float backdrop and all children
  - `Ctrl + LMB` Select / Deselect backdrop
  - `Ctrl + Alt + LMB` Select and float backdrop
  - `Shift + LMB` Append/Remove backdrop and children to current selection
  - `Alt + RMB` Resize backdrop

### [Macros](Macros/README.md) +
- Cleanup Empty Groups
- Frustum
- Calculate Near/Far Objects
