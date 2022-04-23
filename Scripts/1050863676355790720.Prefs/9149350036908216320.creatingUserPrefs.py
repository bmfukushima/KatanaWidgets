""" Shows you how to declare/set/get user preferences"""
from Katana import KatanaPrefs
from UI4.KatanaPrefs import KatanaPrefsObject, PrefNames
prefs = KatanaPrefsObject.KatanaPrefsObject()

pref_name = "test/pref"
# create group prefs
KatanaPrefs.declareGroupPref("test")

# declare a new preference
#if pref_name not in KatanaPrefs.keys():
KatanaPrefs.declareBoolPref(pref_name, False, helpText="Determines if the nodegraph grid is enabled")

# get pref
pref = KatanaPrefs[pref_name]
print(f"{pref_name} == ", pref)

# set a preference
KatanaPrefs[pref_name]=True
print(f"{pref_name} == ", KatanaPrefs[pref_name])
KatanaPrefs.commit()

# create pref w/options
options = ["a", "b", "c"]
options_list = []
for i, draw_mode in enumerate(options):
    options_list.append(f"{draw_mode}:{i}")
options_string = "|".join(options_list)
print(options_string)
KatanaPrefs.declareIntPref(
    ("test/mapperPref"),
    draw_mode,
    'Specifies the draw mode of the grid',
    hints={'widget': 'mapper', 'options': options_string}
)

# setup callback for pref changed
def prefChangedEvent(*args, **kwargs):
    if kwargs["prefKey"] == pref_name:
        print(args, kwargs)
Utils.EventModule.RegisterEventHandler(prefChangedEvent, 'pref_changed')
