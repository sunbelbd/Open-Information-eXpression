"""
single root
"""
import networkx as nx
from more_itertools import pairwise

from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphSuperNode, DependencyGraphNode
# from oix.oiagraph.graphs.oia_graph import OIAAuxNode, OIAWordsNode
from oix.oia.graphs.oia_graph import OIAGraph, OIAWordsNode, \
    OIAAuxNode
from oix.oia.standard import IMPORTANT_CONNECTION_WORDS
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext


def make_dag(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    cycles = list(nx.algorithms.cycles.simple_cycles(oia_graph.g))

    for cycle in cycles:

        if len(cycle) == 1:  # self loop
            oia_graph.g.remove_edge(cycle[0], cycle[0])
            continue

        cycle.append(cycle[0])
        has_ref = False
        for v1, v2 in pairwise(cycle):
            n1 = oia_graph.get_node(v1)
            n2 = oia_graph.get_node(v2)

            relation = oia_graph.get_edge(n1, n2)
            if relation is None:
                continue
            if relation.label == "ref":
                has_ref = True
                oia_graph.remove_relation(n1, n2)
                oia_graph.add_relation(n2, n1, "as:ref")
        # ic(cycle)
        # assert has_ref

    # assert nx.is_directed_acyclic_graph(oia_graph.graph)


def is_conj_node(oia_node, dep_graph):
    """

    :param oia_node:
    :param dep_graph:
    :return:
    """

    if isinstance(oia_node, OIAWordsNode):

        dep_node = dep_graph.get_node_by_spans(oia_node.spans)
        if isinstance(dep_node, DependencyGraphSuperNode) and dep_node.is_conj:
            return True

    return False


def single_root(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    in_degrees = [(node, oia_graph.g.in_degree(node.ID)) for node in oia_graph.nodes()]

    zero_degree_nodes = [n for n, degree in in_degrees if degree == 0]

    if len(zero_degree_nodes) == 0:
        return
    elif len(zero_degree_nodes) == 1:
        root = zero_degree_nodes[0]
    else:
        # len(zero_degree_nodes) >= 2
        dists_to_root = []
        for oia_node in zero_degree_nodes:

            related_dep_nodes = set()
            if isinstance(oia_node, OIAWordsNode):
                dep_node = dep_graph.get_node_by_spans(oia_node.spans)

                if dep_node:
                    if isinstance(dep_node, DependencyGraphNode):
                        related_dep_nodes.add(dep_node)
                    elif isinstance(dep_node, list):
                        for node in dep_node:
                            related_dep_nodes.add(node)
                    else:
                        logger.error("get_node_by_spans return type unknown.")

            children = [n for n, l in oia_graph.children(oia_node)]

            for child in children:
                if isinstance(child, OIAWordsNode):
                    dep_node = dep_graph.get_node_by_spans(child.spans)

                    if dep_node:
                        if isinstance(dep_node, DependencyGraphNode):
                            related_dep_nodes.add(dep_node)
                        elif isinstance(dep_node, list):
                            for node in dep_node:
                                related_dep_nodes.add(node)
                        else:
                            logger.error("get_node_by_spans return type unknown.")

            dep_root = dep_graph.get_node("0")
            real_dep_root = next(n for n, l in dep_graph.children(dep_root))

            min_dist_to_root = min(
                [len(nx.shortest_path(dep_graph.g.to_undirected(), real_dep_root.ID, dep_node.ID))
                 for dep_node in related_dep_nodes])

            dists_to_root.append((oia_node, min_dist_to_root))

        dists_to_root.sort(key=lambda x: x[1])
        root_candidates = []

        min_dist = dists_to_root[0][1]

        for oia_node, dist in dists_to_root:
            if dist == min_dist:
                root_candidates.append(oia_node)

        if len(root_candidates) == 1:

            root = root_candidates[0]

        else:

            scores = []

            score_map = {":": 40, "\"": 30, ";": 20, ",": 10, "(": -10}

            for cand in root_candidates:

                score = -100
                if any(["func" in rel.label for n, rel in oia_graph.children(cand)]):
                    score = 100

                children = [n for n, l in oia_graph.children(cand)]
                dep_children = []
                for child in children:
                    if isinstance(child, OIAWordsNode):
                        dep_node = dep_graph.get_node_by_spans(child.spans)

                        if dep_node:
                            if isinstance(dep_node, DependencyGraphNode):
                                dep_children.append(dep_node)
                            elif isinstance(dep_node, list):
                                for node in dep_node:
                                    dep_children.append(node)
                            else:
                                logger.error("get_node_by_spans return type unknown.")
                # check what between them
                dep_children.sort(key=lambda x: x.LOC)

                for node in dep_graph.nodes():
                    if node.LOC is None:
                        continue
                    if dep_children[0].LOC < node.LOC < dep_children[-1].LOC:

                        if node.FORM in score_map:
                            score = max(score, score_map[node.FORM])

                if isinstance(cand, OIAWordsNode):
                    dep_node = dep_graph.get_node_by_spans(cand.spans)
                    if dep_node:
                        if isinstance(dep_node, DependencyGraphNode):
                            if dep_node.LEMMA in IMPORTANT_CONNECTION_WORDS:
                                score += 8
                        elif isinstance(dep_node, list):
                            for node in dep_node:
                                if node.LEMMA in IMPORTANT_CONNECTION_WORDS:
                                    score += 8
                        else:
                            logger.error("get_node_by_spans return type unknown.")

                elif isinstance(cand, OIAAuxNode) and cand.label == "PARATAXIS":
                    score += 4

                scores.append((cand, score))

            scores.sort(key=lambda x: x[1], reverse=True)

            top_nodes = []
            for node, score in scores:
                if score == scores[0][1]:
                    top_nodes.append(node)

            if len(top_nodes) == 1:
                root = top_nodes[0]

            elif len(top_nodes) >= 3:
                # multiple top node found, merge them to one
                if all(isinstance(node, OIAAuxNode) and node.label == "PARATAXIS" for node in top_nodes):
                    next_nodes = []
                    for top in top_nodes:
                        for n, l in list(oia_graph.children(top)):
                            next_nodes.append(n)
                        oia_graph.remove_node(top)
                        for node in zero_degree_nodes:
                            if node.ID == top.ID:
                                zero_degree_nodes.remove(node)
                    root = oia_graph.add_aux("PARATAXIS")
                    oia_graph.add_node(root)
                    next_nodes.sort(key=lambda x: x.ID)
                    for index, second_node in enumerate(next_nodes):
                        oia_graph.add_argument(root, second_node, index)
                else:
                    logger.error("Deep intersection point, currently cannot process")
                    return
                # raise Exception("Two top nodes? I think it is not possible ")

            else:  # len(top_nodes) == 2:
                # check who is prev, and who is next

                dep_tops = []

                for top in top_nodes:
                    if isinstance(top, OIAWordsNode):
                        dep_node = dep_graph.get_node_by_spans(top.spans)

                        if dep_node:
                            if isinstance(dep_node, DependencyGraphNode):
                                dep_tops.append((top, dep_node))
                            elif isinstance(dep_node, list):
                                for node in dep_node:
                                    dep_tops.append((top, node))
                            else:
                                logger.error("get_node_by_spans return type unknown.")

                if not len(dep_tops) >= 1:
                    logger.error("Multiple AUX head ")
                    return

                dep_tops.sort(key=lambda x: x[1].LOC)

                root = dep_tops[0][0]

    # root obtained, change other zero-in-degree node

    logger.debug("Root obtained ")
    logger.debug(root)

    for node in zero_degree_nodes:
        # print('zero_degree_nodes:', node)
        if root.ID == node.ID:
            continue

        if is_conj_node(node, dep_graph):
            # print('is_conj_node:',node,'  !!!!!!!!!!')
            for child, rel in list(oia_graph.children(node)):
                label = rel.label
                if "pred.arg." in label:
                    arg_no = label.split(".")[-1]
                    new_rel = "as:pred.arg." + arg_no
                    oia_graph.remove_relation(node, child)
                    oia_graph.add_relation(child, node, new_rel)

            continue

        ref_childs = [child for child, rel in oia_graph.children(node) if rel.label == "ref"]


        if ref_childs:
            for child in ref_childs:
                oia_graph.remove_relation(node, child)
                oia_graph.add_relation(child, node, "as:ref")

            continue

    in_degrees = [(node, oia_graph.g.in_degree(node.ID)) for node in oia_graph.nodes()]

    zero_degree_nodes = [n for n, degree in in_degrees if degree == 0 and n.ID != root.ID]

    while len(zero_degree_nodes) > 0:

        logger.debug("we found zero_degree_nodes: ")
        for node in zero_degree_nodes:
            logger.debug(node)

        root_offsprings = set(oia_graph.offsprings(root))

        logger.debug("root offsprings :")
        for n in root_offsprings:
            logger.debug(n)

        intersections = []
        for node in zero_degree_nodes:

            node_offspring = set(oia_graph.offsprings(node))

            logger.debug("node offsprings :")
            for n in node_offspring:
                logger.debug(n)

            intersection = root_offsprings.intersection(node_offspring)

            logger.debug("we found {0} initial intersection :".format(len(intersection)))
            for n in intersection:
                logger.debug(n)

            if intersection:

                top_intersection_point = None
                parents_to_root = None
                parents_to_other = None
                for x in intersection:
                    parents = set([n for n, l in oia_graph.parents(x)])
                    if not parents.intersection(intersection):
                        top_intersection_point = x
                        parents_to_root = parents.intersection(root_offsprings)
                        parents_to_other = parents.intersection(node_offspring)
                        break

                if top_intersection_point is None:
                    logger.error("It seems we have a problem ")
                    continue

                logger.debug("we found a intersections: ")
                logger.debug(top_intersection_point)

                logger.debug("Its parents to root: ")
                for x in parents_to_root:
                    logger.debug(x)

                logger.debug("Its parents to other: ")
                for x in parents_to_other:
                    logger.debug(x)

                intersections.append((top_intersection_point, parents_to_root, parents_to_other))

        if len(intersections) == 0:
            logger.error("seems we have disconnected compoenent")
            break
            # raise Exception("Unexpected situation")


        for intersection_point, parents_to_root, parents_to_other in intersections:

            # if node not in set([n for n, l in oia_graph.parents(intersection_point)]):
            #     logger.error("Deep intersection point, currently cannot process")
            #     # raise Exception("Deep intersection point, currently cannot process")
            #     continue

            for node in parents_to_other:

                if isinstance(node, OIAAuxNode) and node.label == "LIST":
                    logger.error("lets see what happens for LIST")
                    if len(list(oia_graph.parents(node))) != 0:
                        logger.error("it seems different with what we have thought for LIST ")

                    relation = oia_graph.get_edge(node, intersection_point)
                    oia_graph.remove_relation(node, intersection_point)
                    oia_graph.add_relation(intersection_point, node, "as:" + relation.label)
                    # for parent, l in list(oia_graph.parents(intersection_point)):
                    #     if parent != node:
                    #         oia_graph.remove_relation(parent, intersection_point)
                    #         oia_graph.add_relation(parent, node, l.label)
                elif (isinstance(node, OIAAuxNode) and node.label == "WHETHER"):

                    # parents_to_root = list(oia_graph.parents_on_path(intersection_point, root))
                    if len(list(oia_graph.parents(node))) != 0:
                        logger.error("it seems different with what we have thought for WHETHER ")

                    for parent in parents_to_root:
                        relation = oia_graph.get_edge(parent, intersection_point)
                        oia_graph.remove_relation(parent, intersection_point)
                        oia_graph.add_relation(parent, node, relation.label)
                else:

                    relation = oia_graph.get_edge(node, intersection_point)
                    oia_graph.remove_relation(node, intersection_point)
                    oia_graph.add_relation(intersection_point, node, "as:" + relation.label)

        in_degrees = [(node, oia_graph.g.in_degree(node.ID)) for node in oia_graph.nodes()]

        zero_degree_nodes = [n for n, degree in in_degrees if degree == 0 and n.ID != root.ID]
