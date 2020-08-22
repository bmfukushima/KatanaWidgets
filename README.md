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
  * The [cgwidgets] (https://github.com/bmfukushima/cgwidgets) is not currently published,
    however at this point in time it is not required, but will be for future releases.  Please
    note that this library will not be released under as free of a license ( because reasons ).
   
	
Final Note:
The work in this library represents my learning path from scripting towards  Software Engineering.
There will be many questionable choices made, and things that many of you find incredibly idiotic.
Chances are, I just fucked up and plead ignorance, so please let me know if you find anything
idiotic in here as it is a learning experience for myself.

Cheers,

Me

# KatanaWidgets
This repo contains a Katana Resources directory which can be added to the KATANA_RESOURCES environment variable.
This repo contains a small collection of my personal tools which have been created to sit as addons for Katana.

## Prerequisites
  * [qtpy](https://pypi.org/project/QtPy/) is a small abstraction layer that lets you write applications using a single API call to either PyQt or PySide.
  * [cgwidgets](https://github.com/bmfukushima/cgwidgets) small PyQt5/PySide agnostic widgets to be used between multiple DCCs
 
## Written In:
  * Python 3.7.7
  * PyQt 5.15.0

## Tested In:
This library is written for [VFX Reference Platform 2021](https://vfxplatform.com/), however I have intentionally left some things in the ancient Python 2.7.x so that you can still enjoy it... but seriously, fstrings... hurry up.
  * Python 2.7.blah
  * PyQt 5.12.1
