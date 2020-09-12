from Katana import Utils

# initialize bebop menu
from Utils2.ParametersMenu import createParametersMenuButton
Utils.EventModule.RegisterCollapsedHandler(createParametersMenuButton, 'node_setEdited')