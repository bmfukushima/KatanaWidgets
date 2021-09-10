#filepath = "/media/ssd01/dev/katana/KatanaWidgets/Scripts/KatanaBebop/6541263318701568000.Script.py"
#filepath = "/media/ssd01/dev/katana/KatanaWidgets/Scripts/KatanaBebop/3810466965062384640.PopupGSVDisplay.py"
filepath = "/media/ssd01/dev/katana/KatanaWidgets/Scripts/KatanaBebop/4184577316399640064.Script.py"

with open(file_path, "r") as script_descriptor:
    exec(compile(script_descriptor.read(), file_path, "exec"))
