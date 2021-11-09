# Disclaimer ( Boring Legal Crap )
This is my own personal work (Brian Fukushima), and does not represent that of my employer.  
All work done in this library represents my own personal designs, code, resources spent, etc.
Please do not contact my employer with any questions/comments/concerns pertaining to this
library, but rather please contact me directly if you have any questions/comments/concerns.

If you wish to use this library there are a few things to note:
  * It is published under the MIT Open Source license which will allow you to basically
    do w/e tf you want to do with it.
  * If you are using this in a commercial setting, it would be nice if you let me know
    what company is using it to try and atleast track if people are using these tools in
    production, and might be nice to stick companies on here that are using it #marketing.

# KatanaWidgets
This repo contains a Katana Resources directory which can be added to the KATANA_RESOURCES environment variable.
This repo contains a small collection of my personal tools which have been created to sit as addons for Katana.

## Prerequisites
  * [qtpy](https://pypi.org/project/QtPy/) is a small abstraction layer that lets you write applications using a single API call to either PyQt or PySide.
  * [cgwidgets](https://github.com/bmfukushima/cgwidgets) small PyQt5/PySide agnostic widgets to be used between multiple DCCs


## Written for
This library is written for [VFX Reference Platform 2021](https://vfxplatform.com/)
  * Ubuntu 20.04
  * Python 3.7.7
  * PyQt 5.15.0
  * Katana 5.x+
    
## Note
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
