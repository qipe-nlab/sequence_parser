import networkx as nx

def topological_sort(node_list, edge_list):
    graph = nx.DiGraph()
    graph.add_nodes_from(node_list)
    graph.add_edges_from(edge_list)
    sorted_node_list = list(nx.topological_sort(graph))
    return sorted_node_list

def weighted_topological_sort(node_list, weighted_edge_list):
    edge_list = [(fnode, bnode) for fnode, bnode, weight in weighted_edge_list]
    sorted_node_list = topological_sort(node_list, edge_list)

    node_pos = [None]*len(node_list)
    head_node_list = [sorted_node_list[0]]
    node_pos[sorted_node_list[0]] = 0
    while len(head_node_list) >0:
        head_node = head_node_list.pop(0)
        head_pos = node_pos[head_node]
        next_head_node_list = []
        for fnode, bnode, weight in weighted_edge_list:
            if fnode == head_node:
                next_head_node_list.append(bnode)
                if node_pos[bnode] is None:
                    node_pos[bnode] = head_pos + weight
                else:
                    node_pos[bnode] = max(head_pos + weight, node_pos[bnode])
                weighted_edge_list.remove((fnode, bnode, weight))

        for next_head_node in next_head_node_list:
            flag = True
            for fnode, bnode, weight in weighted_edge_list:
                if bnode == next_head_node_list:
                    flag = False
            if flag:
                if next_head_node not in head_node_list:
                    head_node_list.append(next_head_node)
        head_node_list.sort(key=sorted_node_list.index)

    return node_pos