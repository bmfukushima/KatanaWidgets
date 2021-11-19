# Disclaimer
This is my own personal work (Brian Fukushima), and does not represent that of my employer.  
All work done in this library represents my own personal designs, code, resources spent, etc.
Please do not contact my employer with any questions/comments/concerns pertaining to this
library, but rather please contact me directly if you have any questions/comments/concerns.

# Katana Bebop
This repo contains a Katana Resources directory which can be added to the `KATANA_RESOURCES `environment variable.
This repo contains a small collection of my personal tools which have been created to sit as addons for Katana.

### Prerequisites
  * [qtpy](https://pypi.org/project/QtPy/)
        is a small abstraction layer that lets you write applications using a single API call to either PyQt or PySide.
  * [cgwidgets](https://github.com/bmfukushima/cgwidgets)
        PyQt5/PySide agnostic widgets to be used between multiple DCCs


### Written for
This library is written for [VFX Reference Platform 2021](https://vfxplatform.com/)
  * Ubuntu 20.04
  * Python 3.7.7
  * PyQt 5.15.0
  * Katana 5.x+
  
# Tools
### Tabs
- [Global Events Tab](MultiTools/GlobalEventsTab/README.md)
- [GSV Manager Tab](MultiTools/GSVManagerTab/README.md)
- [Script Editor Tab](MultiTools/ScriptEditorTab/README.md)
- [Node Color Registry Tab](MultiTools/NodeColorRegistryTab/README.md)
- [Popup Bar Tabs](Tabs/PopupBar/README.md) +
- [Desired Stuff Tab](Tabs/DesiredStuffTab/README.md) +

### SuperTools
- [Constraint](SuperTools/Constraint/README.md)
- [Isolate CEL](SuperTools/IsolateCEL/README.md)
- [Node Tree](SuperTools/NodeTree/README.md) +
- [Simple Tool](MultiTools/SimpleTool/README.md) +
- [Variable Manager](MultiTools/VariableManager/README.md)

### [Macros](Macros/README.md) +
- CleanupEmptyGroups
- Frustum

# Notes
  * I am aiming for a first release of this library with Katana 5.0 which will have the upgrades to
      Python 3.7.x and Qt for Python (PySide2).
  * The Utils2 / Widgets2 folders are named this way to avoid library conflicts with
        Katana's internal mechanisms.  I haven't really tested a worked around too much
        for this... But as of this time, this works and shouldn't conflict with anything...
  * Load Order...
      * SuperTools
      * UIPlugins
      * Startup
      * Tabs
