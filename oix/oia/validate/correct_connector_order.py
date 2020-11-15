"""
fix the order of conjunctions
"""
from oix.parser.ud2oia.rule.converter.oia_standardize.utils import get_loc
from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph, OIAAuxNode


def correct_connector_order(oia_graph: OIAGraph, dep_graph: DependencyGraph):
    """

    :param oia_graph:
    :return:
    """

    sentconnective = {'so', 'therefore', 'though', 'although',
                      'however', 'thus', 'meanwhile',
                      'otherwise', 'since',
                      'thereafter', 'thereby', 'hereby', "because", "after", "before",
                      "if",
                      "since"}

    fixed = False
    for oia_node in oia_graph.nodes():
        if isinstance(oia_node, OIAAuxNode):
            continue
        dep_ids = oia_node.words[0].split()

        conn_node = None
        has_arg_node = False
        for dep_id in dep_ids:
            dep_node = dep_graph.get_node(dep_id)
            if dep_node and dep_node.LEMMA.lower in sentconnective:
                conn_node = dep_node

            if not dep_node and dep_id in {"{0}", "{1}", "{2}", "{3}", "{4}"}:
                has_arg_node = True

        if not conn_node or has_arg_node:  # not a connection node or with args:
            continue

        relations = [(n, l.label) for n, l in oia_graph.children(oia_node)]

        relations = list(filter(lambda x: x[1].startswith("pred:arg:"), relations))

        if relations:

            logger.debug("connection words with argument found")

            relations.sort(key=lambda x: x[1])

            node_loc = get_loc(oia_node, dep_graph)
            child_locs = [get_loc(child, dep_graph) for child, rel in relations
                          if get_loc(child, dep_graph)]

            if len(relations) == 1:
                child, rel = relations[0]
                child_loc = child_locs[0]

                if child_loc > node_loc and rel != "pred:arg:1":

                    fixed = True
                    oia_graph.add_relation(oia_node, child, "pred:arg:1")

                    parents = [parent for parent, e in oia_graph.parents(oia_node)
                               if e.label.startswith("mod_by:pred:arg:")]
                    if parents:
                        assert len(parents) == 1
                        oia_graph.add_relation(parents[0], oia_node, "mod_by:pred:arg:2")

                elif child_loc <= node_loc:

                    logger.warning("connection word after the argument, unexpected")

            elif len(relations) == 2:
                child1, rel1 = relations[0]
                child2, rel2 = relations[1]
                child_loc1, child_loc2 = child_locs

                if child_loc1 < node_loc < child_loc2:
                    fixed = True
                    oia_graph.add_relation(oia_node, child2, "pred:arg:1")
                    oia_graph.add_relation(oia_node, child1, "pred:arg:2")
                elif child_loc2 < node_loc < child_loc1:
                    # correct, do nothing
                    pass
                else:
                    logger.warning("connection word not in the middle of args, unexpected")

    return fixed
