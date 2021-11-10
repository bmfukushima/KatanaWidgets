
# Summary
The NodeColorRegistryTab creates a new tab in Katana that will allow you to
set up custom node color presets.  When a new node is created in Katana, it
will check to see if this node type exists in the current presets file which
is located on the root node (Project Settings) at `KatanaBebop.NodeColorRegistry`.
<br />

# Color Config
### Default Profile
  The default color config is set to the one provided by KatanaBebop at
  `$KATANABEBOP/Settings/nodeColorConfig.json`.  If you want to set your own
  preset color config, you can set the environment variable `KATANABEBOPDEFAULTCOLORCONFIG`
  to a path on disk to the color config JSON file.
### Config Directories
  New directories can be added by extending the environment variable `KATANABEBOPNODECOLORS`.
  This environment variable will hold all of the directories to look for color config files in.
  The user directory located at `KatanaResources.GetUserKatanaPath() + /ColorConfigs/User`
  will always exist to be saved into.

# I/O
The save/load widget can be shown by pressing `Alt+S`.  This will give a few options:
### Dir
  The current directory to be stored in. 
  This environment variable can be set using `NodeColorRegistryWidget.setConfigsEnvar()`,
  by default it is set  to `KATANABEBOPDEFAULTCOLORCONFIG`.  If the envar is not valid,
  it will default to the default save directory. Which is set to
  `KatanaResources.GetUserKatanaPath() + /ColorConfigs/User`, and can also be set using
  `NodeColorRegistryWidget.setDefaultSaveLocation()`.
### File
  The name of the current file to be saved.  This will automatically have the `.json`
  suffix appended to it on save/load.

# How to use
- Clear color `MMB`
- Change color `Double Click` on color column item to open color editor, press `enter` to save color.
- Save/Load `Alt+S` to open/close Save/Load options
- Create new node type 
  - Type new node name into ListInputWidget.  This will auto display the available node types.
- Create new group `G`
