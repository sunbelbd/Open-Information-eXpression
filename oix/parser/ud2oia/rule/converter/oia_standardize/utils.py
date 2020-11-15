"""
utilities for fixes
"""
from oix.oia.standard import NOUN_UPOS

from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIANode, OIAWordsNode




def is_noun(node: OIANode, dep_graph: DependencyGraph):
    """

    :param node:
    :param dep_graph:
    :return:
    """

    if not isinstance(node, OIAWordsNode):
        return False

    is_noun = False

    dep_ids = node.words[0].split()
    for dep_id in dep_ids:
        dep_node = dep_graph.get_node(dep_id)
        if dep_node:
            if dep_node.UPOS in NOUN_UPOS:
                is_noun = True

    return is_noun


def get_dep_nodes(node: OIANode, dep_graph: DependencyGraph):
    """

    :param node:
    :param dep_graph:
    :return:
    """
    if not isinstance(node, OIAWordsNode):
        return []

    dep_nodes = []

    dep_ids = node.words[0].split()
    for dep_id in dep_ids:
        dep_node = dep_graph.get_node(dep_id)
        if dep_node:
            dep_nodes.append(dep_node)
        else:
            dep_nodes.append(dep_id)

    return dep_nodes


def get_loc(node: OIANode, dep_graph: DependencyGraph):
    """

    :param node:
    :param dep_graph:
    :return:
    """

    if not isinstance(node, OIAWordsNode):
        return None

    min_loc = 1000
    max_loc = 0

    dep_ids = node.words[0].split()
    for dep_id in dep_ids:
        dep_node = dep_graph.get_node(dep_id)
        if dep_node:
            min_loc = min(min_loc, dep_node.LOC)
            max_loc = max(max_loc, dep_node.LOC)

    return [min_loc, max_loc]
