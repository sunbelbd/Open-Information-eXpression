"""
fix the order of conjunctions
"""
from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph, OIAWordsNode, OIAAuxNode
from loguru import logger


def fix_verb_adp(oia_graph: OIAGraph, dep_graph: DependencyGraph):
    """

    :param oia_graph:
    :return:
    """

    logger.debug("fix_verb_adp")

    fixed = False
    for oia_node in list(oia_graph.nodes()):

        if isinstance(oia_node, OIAAuxNode):
            continue

        dep_ids = oia_node.words[0].split()

        logger.debug(dep_ids)

        adp_node = None
        verb_node = None
        for dep_id in dep_ids:
            dep_node = dep_graph.get_node(dep_id)
            if dep_node and dep_node.UPOS == "VERB":
                verb_node = dep_node

            if dep_node and dep_node.UPOS == "ADP":
                adp_node = dep_node

        logger.debug("verb = {0} adp = {1}".format(verb_node, adp_node))

        if not (adp_node and verb_node and adp_node.LOC > verb_node.LOC + 1):
            continue

        logger.debug("verb and adp found")

        relations = [(n, l.label) for n, l in oia_graph.children(oia_node)]

        arg2_node = [n for n, l in relations if l == "pred:arg:2"]
        arg3_node = [n for n, l in relations if l == "pred:arg:3"]

        if arg2_node and arg3_node:
            logger.debug("arg2 and arg3 found")
            if adp_node.ID != dep_ids[-1]:
                logger.warning("last word is not adp, unknown situation")
                continue

            fixed = True
            arg2_node = arg2_node[0]
            arg3_node = arg3_node[0]

            oia_graph.remove_relation(oia_node, arg3_node)
            adp_oia_node = OIAWordsNode((adp_node.ID,), adp_node.ID)
            oia_graph.add_node(adp_oia_node)

            new_verb_node = OIAWordsNode((" ".join(dep_ids[:-1]),), verb_node.ID)
            oia_graph.replace(oia_node, new_verb_node)

            oia_graph.add_relation(new_verb_node, adp_oia_node, "mod_by:pred:arg:1")
            oia_graph.add_relation(adp_oia_node, arg3_node, "pred:arg:2")

    return fixed
