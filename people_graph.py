

""" GENERAL GRAPH FUNCTIONS """
def make_graph():
	return [[], []] # nodes, then edges

def get_nodes(graph):
	return graph[0]

def get_edges(graph):
	return graph[1]

def add_node(graph, node):
	if node not in get_nodes(graph):
		get_nodes(graph).append(node)

def add_edge(graph, start, end):
	if [start, end] not in get_edges(graph) and [end, start] not in get_edges(graph):
		get_edges(graph).append([start, end])

""""""