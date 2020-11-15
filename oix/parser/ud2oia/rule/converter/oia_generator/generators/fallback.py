"""
fallback processors
"""
from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from loguru import logger

def fallback_sconj(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for node in dep_graph.nodes():

        if oia_graph.has_word(node.position):
            continue

        if node.UPOS == "SCONJ" and node.LEMMA in {"because", "so", "if", "then", "otherwise",
                                                   "after", "before", "and", "or", "but"}:

            parents = [n for n, l in dep_graph.parents(node) if "mark" in l]

            if not parents:
                continue

            assert len(parents) == 1

            parent = parents[0]

            logger.debug("context = " + str(context.processed_edges))

            if context.is_processed(parent, node):
                continue

            oiar_node = oia_graph.add_words(parent.position)
            oia_sconj_node = oia_graph.add_words(node.position)

            if node.LEMMA in {"because", "if"}:
                oia_graph.add_argument(oia_sconj_node, oiar_node, 1)
            else:
                oia_graph.add_argument(oia_sconj_node, oiar_node, 1)
