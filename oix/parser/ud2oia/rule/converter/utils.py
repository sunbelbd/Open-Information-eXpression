# -*- coding: UTF-8 -*-
"""
utils for conversions
"""


from oix.oia.graphs.dependency_graph import DependencyGraphNode, DependencyGraphSuperNode


def continuous_component(nodes, head_node):
    """

    :param node_set:
    :param head:
    :return:
    """

    # found the connected component containing the case node
    connected_loc = {head_node.LOC}
    connected_nodes = {head_node}
    while True:
        case_num = len(connected_loc)
        for node in nodes:
            if node.LOC + 1 in connected_loc or node.LOC - 1 in connected_loc:
                connected_loc.add(node.LOC)
                connected_nodes.add(node)

        if len(connected_loc) == case_num:
            break
    connected_nodes = sorted(connected_nodes, key=lambda x: x.LOC)
    return connected_nodes


def merge_dep_nodes(nodes, **kwargs):
    """

    :param nodes:
    :param kwargs:
    :return:
    """

    new_node = DependencyGraphSuperNode(nodes, **kwargs)

    for node in nodes:
        if isinstance(node, DependencyGraphNode):
            new_node.contexts.extend(node.contexts)

    return new_node


from itertools import tee



