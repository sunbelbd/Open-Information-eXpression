"""
fix the order of conjunctions
"""
from oix.parser.ud2oia.rule.converter.oia_standardize.utils import is_conjunction_without_args, get_loc
from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph


def correct_conj_order(oia_graph: OIAGraph, dep_graph: DependencyGraph):
    """

    :param oia_graph:
    :return:
    """
    fixed = False
    for node in oia_graph.nodes():

        if not is_conjunction_without_args(node, dep_graph):
            continue

        relations = [(n, l.label) for n, l in oia_graph.children(node)]

        relations = list(filter(lambda x: x[1].startswith("pred:arg:"), relations))

        if relations:
            if len(relations) == 1 and relations[0][1] == "pred:arg:1":
                continue

            fixed = True
            relations.sort(key=lambda x: x[1])

            locs = sum([get_loc(child, dep_graph) for child, rel in relations
                        if get_loc(child, dep_graph)], [])

            if not all(locs[i] <= locs[i + 1] for i in range(len(locs) - 1)):
                logger.error("locs = {0}".format(locs))
                logger.error("Illogic conjunction in old standard ")
                continue
            relations = reversed(relations)

            for i, (child, rel) in enumerate(relations):
                oia_graph.add_argument(node, child, i + 1)

        relations = [(parent, e.label) for parent, e in oia_graph.parents(node)]

        relations = list(filter(lambda x: x[1].startswith("conj_by:pred:arg:"), relations))
        if relations:

            fixed = True

            relations.sort(key=lambda x: x[1])

            locs = sum([get_loc(child, dep_graph) for child, rel in relations if get_loc(child, dep_graph)], [])

            if not all(locs[i] <= locs[i + 1] for i in range(len(locs) - 1)):
                logger.error("Illogic conjunction in old standard ")
                continue
            relations = reversed(relations)
            for i, (child, rel) in enumerate(relations):
                oia_graph.add_relation(node, child, "conj_by:pred:arg:{0}".format(i + 1))

    return fixed
