

d = RenderManager.InteractiveRenderDelegateManager.GetRenderFiltersDelegate()
active_filters = d.getActiveRenderFilterNodes()
print(active_filters)


all_render_filters = NodegraphAPI.GetAllNodesByType("RenderFilter")
for render_filter_node in all_render_filters:
    name = render_filter_node.getParameter('name')
    category = render_filter_node.getParameter('category')
    
    print(render_filter_node)

d.setActiveRenderFilterNodes(all_render_filters)

