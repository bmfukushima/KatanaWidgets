# Script Editor Tab
The script editor is an all in one place where users can
- Create/Delete/Organize scripts
- Setup hotkeys for scripts
- Create designs for scripts

There are two main parts to the Script Editor, the first is the Katana Tab which is where the user will do
most of their work.  The second is an event filter that runs over the top of the main Katana instance
at `UI4.App.MainWindow.GetMainWindow()`.

# Designs
A **design** is a widget that can popup and will allow users to quickly access their scripts either through a hotkey,
gesture, or mouse press. This will allow users to create their own interfaces for their scripts, or for
engineering to create interfaces for scripts.  The general idea behind designs is that when done correctly,
the user can rely on muscle memory to access tools.  There are two main types of designs:
- **Gesture**: User can activate by swiping through
  - As of this point in time, I wouldn't recommend using Gesture Designs, as they are not working
       well, to the point where I might just disable their usage prior to release.
- **Hotkey**: User can activate via clicking or hotkey

Designs can be created by `RMB -> CreateHotkeyDesign | CreateGestureDesign`.

# Data Structures
## Directories
Different directories can be added by modifying the `KATANABEBOPSCRIPTS` environment variable.
This environment variable will be a list of directories to be used as top level items.  This will
always have the directories `$KATANABEBOP/Scripts` as **KatanaBebop** and `$HOME/.katana/Scripts` as **Sandbox**.

Each directory must have two files `hotkeys.json` and `settings.json`.  By default if the directory,
or any of the metadata files does not exist, they will be created.
### hotkeys.json
When a user sets a hotkey, this file will be updated 
`str(filepath): str(hotkey)` ie `"/path/on/disk/pythonfile.py":"Ctrl+Alt+A"`

### settings.json
This will hold the settings for this directory.  There are only two settings, `display_name`, and
`locked`.  These will be displayed with the signature`{"display_name": str(name), "locked": bool}`,
if you wish to update these, they will need to be manually updated.

## Designs
Are stored as a JSON file with the key pairs of `str(hotkey):str(filepath)` ie `"1": "/path/on/disk/to/script/py"`.

**Hotkey Design Keys:**
> 1 2 3 4 5 <br />
> q w e r t <br />
> a s d f g <br />
> z x c v b <br />

**Gesture Gesture Keys:**
> 1 2 3 4 5 6 7 8

## Items on disk
Scripts/Designs/ Groups are stored in directories with a unique hash as a prefix.  Their filename should
look something like `uid.name.extension` for scripts/designs, and `uid.name` for directories/groups.

# How to use
- Create new item `RMB --> CreateItemType`
- Modify Script
  - Select script in view
  - Type stuff into the Python Editor
  - Click save
- Modify Designs
  - Drag/Drop items from the view into the different buttons.