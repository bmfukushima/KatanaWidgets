# Popup Bar Tabs
PopupBarTabs are designed to display multiple tabs to the user simultaneously.
Similar to the function that was provided to TV's in the mid 1970's.  This widget is
designed to allow the user to create multiple hot swappable widgets inside of the same
tab. There are three different modes of display for these tabs, `PiP`, `PiPTaskbar`,
and `Standalone Taskbar`.  

Since there will be to many options to create, there is an organizer/creator where the user
can create their own popup bar tabs, which will automatically be registered when Katana
is loaded.  Custom popup bar tabs can be created through the `Popup Bar Organizer Tab`.



# Popup Bar Organizer Tab
Will help the user register their own Popup Bar widgets.  By default `KatanaBebeop` will
ship with a default one at `$KATANABEBOP/Tabs/PopupBar/KatanaBebopPopupBarTabs.json`.  However,
this one will be locked, and the user will by default use the one located at 
`$HOME/.katana/.PopupBarTabs.json`.

You can add additional save directories, and widgets to be loaded into these tabs by looking
at the example in the `PopupBarOrganizerTab.py`

Individual sections can be maximized with the " \` ".  And you can leave maximization with the
`esc` key.

### Display
Will display the current widget that the user can expect to be displayed when they
initialize this tab later.

Note that this isn't a perfect 1:1 representation, and there will be a few minor details
that don't work.  But the basic jist of it should be there.

### Organizer
The area where the user decides which tabs they would like to add to their Popup Display
Tab.  Users can add a tab, by type a tab name into the section at the bottom, and delete
them by selecting them and pressing delete.

Note that the **last** item in here will default to the main tab.

Changing the name in this portion of the UI will change the `Display Name` of the widget
when it is displayed.  `Display Names` can be toggled on/off in the `Settings` portion of the UI.

### Save / Load
Area for saving/loading custom Popup Bar Widgets.  The data is saved as a `JSON` with
the data structure looking like:

    {"PiPName": {
        "widgets": [
            {"widget name": {
                "code": "constructor_code",
                "Overlay Text": "text",
                "Overlay Image": "path/on/disk/to/image"},
            {"widget name": {
                "code": "constructor_code",
                "Overlay Text": "text",
                "Overlay Image": "path/on/disk/to/image"},
            ],
        "settings": {"setting name": "value"}}
    }

Each top level item consists of one dictionary, and is registered with a dictionary
that can describe the settings to `lock` the location, and set a `display name` to the user.

    {   "DisplayName":{
            "file_path": path_on_disk_to_file,
            "locked": bool}
        "KatanaBebop": {
            "file_path": built_ins_file_path,
            "locked": False},
        "User": {
            "file_path": user_save_path,
            "locked": False}
    }

### Settings
- **Display Titles <br />**
    - Determines if there should be a title displayed above each widget.
    - Note: Something with this is making some widgets go haywire when enlarging/closing.
- **Direction <br />**
    - The direction that the popup will be shown on.
- **Display Mode <br />**
    - How the widget will be displayed
- **PiP Scale <br />**
    - The amount of space the PiPWidget will take up when not enlarged
    - This setting is only available when the `Display Mode` is set to `PIP`.
- **Enlarged Scale <br />**
    - The scale of the widget when it is enlarged.  This is a percentage of the parent
    widget.
    - This setting is only available when the `Display Mode` is set to 
    `PIPTASKBAR` or `PIP`.
- **Enlarged Size <br />**
    - The size (pixels) in the expanding direction of the enlarged widget.
    ie. if the expanding direction is set to East, this will be the width in pixels.
    - This setting is only available when the `Display Mode` is set to `STANDALONE TASKBAR`.
- **Enlarged Offset <br />**
    - The size (pixels) of the offset of the direction perpendicular to the direction.
    - This setting is only available when the `Display Mode` is set to `STANDALONE TASKBAR`.
- **Taskbar Size <br />**
    - The size (pixels) of the taskbar when not enlarged
    - This setting is only available when the `Display Mode` is set to `PIPTASKBAR`.
- **Overlay Text <br />**
    - The text to be overlaid while not enlarged.
    - This will set the overlay text for the item currently selected in the views tab 
    - This setting is only available when the `Display Mode` is set to `STANDALONE TASKBAR`.
        or `PIP TASKBAR`.
- **Overlay Image <br />**
    - The overlay image while not enlarged.
    - This will set the overlay image for the item currently selected in the views tab.
    - This setting is only available when the `Display Mode` is set to `STANDALONE TASKBAR`
       or `PIP TASKBAR`.
    - You can use `../` to access the current directory

### Help
Area that displays most of this stuff to the user

# How to use (Popup Tabs)
In order to enlarge a Popup Tab, the user simply needs to have their cursor enter the
widget.  In order to close the enlarged view, the user simple needs to have their cursor
exit the enlarged popup widget, or press `esc`.

- Press `esc` to close the currently enlarged widget.
- Press `space` to swap the currently enlarged widget with the previously enlarged widget.
    <br /> or <br />
    If a widget is currently enlarged, swap it with the main view
- Press `1 | 2 | 3 | 4 | 5`, to swap the main view widget with the popup widget at the
  selected index.
- Press `Q` to hide popup widgets.
