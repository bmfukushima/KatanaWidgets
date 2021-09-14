# Access the catalog items shown as the front and back buffer in
# the largest available Monitor tab
monitorTab = UI4.App.Tabs.FindTopTab('Monitor')
monitorWidget = monitorTab.getMonitorWidget()
frontBufferCatalogItem, backBufferCatalogItem = monitorWidget.getDisplayItems()

# Print the names of available layers/AOVs
layersAndViews = frontBufferCatalogItem.getLayerViews()
print('Available layers/AOVs of front buffer catalog item:')
for layer, view in layersAndViews:
    print('    %s | %s' % (layer, view))
    monitorWidget.update()
    frontBufferDrawState, backBufferDrawState = monitorWidget.getDrawStates()
    frontBufferDrawState.setLayerSelection(layer)
    center = monitorWidget.getPixelProbeCenter()
    monitorWidget.setPixelProbeCenter(center)
    for b in monitorWidget._MonitorWidget__pixelComponentsA:
        print b.text()
# Get draw state objects to access how catalog items are displayed
#frontBufferDrawState, backBufferDrawState = monitorWidget.getDrawStates()
frontBufferDrawState.setLayerSelection('primary')
# Set AOV to 'primary'
print('Setting layer/AOV of front buffer catalog item to primary...')


# Reset AOV to 'default'
#frontBufferDrawState.setLayerSelection(None)


monitor_widget = monitorTab._MonitorPanel__monitorWidget


