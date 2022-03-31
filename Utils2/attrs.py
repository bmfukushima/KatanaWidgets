prman = 0.0
arnold = 1.0
redshift = 2.0
delight = 3.0
custom = 4.0

def getRendererName(value):
    if value == 0.0:
        return "Prman"
    if value == 1.0:
        return "Arnold"
    if value == 2.0:
        return "Redshift"
    if value == 3.0:
        return "Delight"
    if value == 4.0:
        return "Custom"
