from Katana import LayeredMenuAPI
from Utils2 import isLicenseValid

# Need to set UNREGISTERED so that it won't dual register

if isLicenseValid():
    # Todo Not sure why this is dual registering on init
    from .GSVMenu import gsv_menu
    from .NMXMenu import nmx_menu

    LayeredMenuAPI.RegisterLayeredMenu(nmx_menu, 'NMX')
    LayeredMenuAPI.RegisterLayeredMenu(gsv_menu, 'GSV')

