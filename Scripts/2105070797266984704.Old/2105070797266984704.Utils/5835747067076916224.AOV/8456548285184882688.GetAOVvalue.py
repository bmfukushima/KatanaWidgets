# Access the catalog items shown as the front and back buffer in
# the largest available Monitor tab
monitorTab = UI4.App.Tabs.FindTopTab('Monitor')
monitorWidget = monitorTab.getMonitorWidget()
frontBufferCatalogItem, backBufferCatalogItem = monitorWidget.getDisplayItems()

# Print the names of available layers/AOVs
layersAndViews = frontBufferCatalogItem.getLayerViews()

# get luminance and name of all aovs
aov_list = {}
for layer, view in layersAndViews:
    #print('    %s | %s' % (layer, view))
    monitorWidget.update()
    frontBufferDrawState, backBufferDrawState = monitorWidget.getDrawStates()
    frontBufferDrawState.setLayerSelection(layer)
    monitorWidget.update()
    monitorTab.update()
    luminance = monitorWidget._MonitorWidget__pixelComponentsA[4]
    luminance = luminance.text().split(' ')[1]
    aov_list[layer] = luminance
# Get draw state objects to access how catalog items are displayed
#frontBufferDrawState, backBufferDrawState = monitorWidget.getDrawStates()
frontBufferDrawState.setLayerSelection('primary')
print aov_list

