"""
remove desc

"""

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
from oix.oia.graphs.oia_graph import OIAGraph, OIAAuxNode
from loguru import logger


def remove_desc(oia_graph: OIAGraph, dep_graph: DependencyGraph):
    """

    :param oia_graph:
    :return:
    """

    removed = False
    for oia_node in list(oia_graph.nodes()):

        if not isinstance(oia_node, OIAAuxNode):
            continue

        if oia_node.label != "DESC":
            continue

        parents = list(oia_graph.parents(oia_node))
        if not (len(parents) == 1):
            continue
        desc_parent = parents[0][0]

        children = list(oia_graph.children(oia_node))
        if not (len(children) == 1):
            continue

        desc_child = children[0][0]

        removed = True

        oia_graph.remove_node(oia_node)
        oia_graph.add_relation(desc_parent, desc_child, "mod_by")

        logger.debug("Removing DESC between {0} and {1}".format(oia_graph.get_node_label(desc_parent, dep_graph),
                                                                oia_graph.get_node_label(desc_child, dep_graph)))

    return removed
