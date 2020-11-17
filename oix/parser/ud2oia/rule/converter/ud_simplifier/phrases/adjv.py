"""
Adjv phrases
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph

valid_adj_form = {"flat", "fixed", "compound", "advmod"}


def valid_adjv_element(n, dep_graph):
    """

    :param n:
    :param valid_elements:
    :return:
    """
    elements = [n]
    for child, rel in dep_graph.children(n):
        if rel.intersect(valid_adj_form):
            elements.extend(valid_adjv_element(child, dep_graph))
    return elements


def adjv_phrase(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    phrases = []

    for node in dep_graph.nodes(filter=lambda n: n.UPOS in {"ADJ", "ADV"}):

        is_root = True
        for parent, rel in dep_graph.parents(node):
            if "advmod" in rel and parent.UPOS not in {"ADJ", "ADV"}:
                is_root = True
                break
            elif rel.intersect(valid_adj_form):
                is_root = False

        if not is_root:
            continue

        adjv_element = valid_adjv_element(node, dep_graph)

        adjv_element = sorted(list(adjv_element), key=lambda x: x.LOC)

        connected_components = [node]
        start_loc = node.LOC
        for child in reversed(adjv_element):
            # print(str(node.FORM))

            if child.UPOS in {"ADJ", "ADV"} and child.LOC == start_loc - 1:

                connected_components.append(child)
                start_loc = child.LOC

        connected_components.sort(key=lambda x: x.LOC)

        if len(connected_components) > 1:
            phrases.append((connected_components, node))

    for adjv_phrase, node in phrases:
        adjv_node = merge_dep_nodes(adjv_phrase,
                                    UPOS=node.UPOS,
                                    LOC=node.LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.replace_nodes(adjv_phrase, adjv_node)
