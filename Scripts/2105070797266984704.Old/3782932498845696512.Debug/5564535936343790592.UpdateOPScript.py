update_node.flushAll()
with Utils.EventModule.SynchronousEventProcessingScope():
    current_selection = self.hud_widget.getSelectedItems()
    self.hud_widget.setSelectedItems(current_selection)