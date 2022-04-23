""" Shows you how to declare/set/get user preferences"""
from Katana import KatanaPrefs
from UI4.KatanaPrefs import KatanaPrefsObject, PrefNames

pref_name = "nodegraph/grid"

# declare a new preference
if pref_name not in KatanaPrefs.keys():
    KatanaPrefs.declareBoolPref(pref_name, False, helpText="Determines if the nodegraph grid is enabled")

# get pref
pref = KatanaPrefs[pref_name]
print(f"{pref_name} == ", pref)

# set a preference
KatanaPrefs[pref_name]=True
print(f"{pref_name} == ", KatanaPrefs[pref_name])
KatanaPrefs.commit()
