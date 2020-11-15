"""
single node
"""

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext


def single_node(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    regular_nodes = [n for n in dep_graph.nodes() if n.UPOS not in {"ROOT", "PUNCT"}]
    #logger.debug("regular nodes")
    #for node in regular_nodes:
    #    logger.debug(str(node))

    if len(regular_nodes) == 1:
        node = regular_nodes[0]

        oia_graph.add_words(node.position)
        #logger.debug("single node added")


def two_node_with_case(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    regular_nodes = [n for n in dep_graph.nodes() if n.UPOS not in {"ROOT", "PUNCT"}]
    #logger.debug("regular nodes")
    #for node in regular_nodes:
    #    logger.debug(str(node))

    if len(regular_nodes) == 2:
        regular_nodes.sort(key=lambda x: x.LOC)
        case_node, noun_node = regular_nodes
        if dep_graph.get_dependency(noun_node, case_node) == "case":
            oia_case_node = oia_graph.add_words(case_node.position)
            oia_noun_node = oia_graph.add_words(noun_node.position)

            oia_graph.add_argument(oia_case_node, oia_noun_node, 2)


