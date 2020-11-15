"""
negation
"""
from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext


def negation(dep_graph, oia_graph, context: UD2OIAContext):
    """
    #################### Negation ########################
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    not_node = DependencyGraphNode(LEMMA="not")
    parent_node = DependencyGraphNode()

    pattern.add_nodes([not_node, parent_node])

    pattern.add_dependency(parent_node, not_node, r'\w*')

    for match in dep_graph.match(pattern):
        dep_not_node = match[not_node]
        dep_parent_node = match[parent_node]

        oia_pred_node = oia_graph.add_aux(label="SCOPE")

        oia_not_node = oia_graph.add_words(dep_not_node.position)
        oia_parent_node = oia_graph.add_words(dep_parent_node.position)

        oia_graph.add_argument(oia_pred_node, oia_not_node, 1)
        oia_graph.add_argument(oia_pred_node, oia_parent_node, 1)
