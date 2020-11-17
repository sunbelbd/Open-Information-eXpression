"""
vocative relation
"""
from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext

import more_itertools

def vocative(dep_graph, oia_graph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for n1, n2, deps in dep_graph.dependencies():

        if "vocative" in deps:
            voc_node = oia_graph.add_aux("VOC")
            arg1_node = oia_graph.add_words(n1.position)
            arg2_node = oia_graph.add_words(n2.position)

            oia_graph.add_argument(voc_node, arg1_node, 1)
            oia_graph.add_argument(voc_node, arg2_node, 2)


def discourse(dep_graph, oia_graph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for n1, n2, deps in dep_graph.dependencies():

        if "discourse" in deps:
            voc_node = oia_graph.add_aux("DISCOURSE")
            arg1_node = oia_graph.add_words(n1.position)
            arg2_node = oia_graph.add_words(n2.position)

            oia_graph.add_argument(voc_node, arg1_node, 1)
            oia_graph.add_argument(voc_node, arg2_node, 2)


def dislocated(dep_graph, oia_graph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for n1, n2, deps in dep_graph.dependencies():

        if "dislocated" in deps:
            voc_node = oia_graph.add_aux("TOPIC")
            arg1_node = oia_graph.add_words(n1.position)
            arg2_node = oia_graph.add_words(n2.position)

            oia_graph.add_argument(voc_node, arg1_node, 1)
            oia_graph.add_argument(voc_node, arg2_node, 2)


def reparandum(dep_graph, oia_graph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for n1, n2, deps in dep_graph.dependencies():

        if "reparandum" in deps:
            voc_node = oia_graph.add_aux("REPARANDUM")
            arg1_node = oia_graph.add_words(n1.position)
            arg2_node = oia_graph.add_words(n2.position)

            oia_graph.add_argument(voc_node, arg1_node, 1)
            oia_graph.add_argument(voc_node, arg2_node, 2)


def parataxis(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    #################### adverbs like however, then, etc ########################
    :param sentence:
    :return:
    """

    for dep_node in list(dep_graph.nodes()):

        parallel_nodes = [n for n, l in dep_graph.children(dep_node) if "parataxis" == l]

        if not parallel_nodes:
            continue

        parallel_nodes.append(dep_node)
        parallel_nodes.sort(key=lambda x: x.LOC)

        predicates = []


        for index, (former, latter) in enumerate(more_itertools.pairwise(parallel_nodes)):

            advcon = [n for n, l in dep_graph.children(latter,
                                                       filter=lambda n, l: "advmod" in l and
                                                                           (
                                                                                   former.LOC < n.LOC < latter.LOC)
                                                                           and (n.UPOS == "SCONJ" or n.LEMMA in {
                                                           "so"}))]

            coloncon = [n for n, l in dep_graph.children(dep_node,
                                                         filter=lambda n, l: "punct" in l and n.FORM in {":", ";", "--",
                                                                                                         ","}
                                                                             and (
                                                                                     former.LOC < n.LOC < latter.LOC))]

            if advcon:
                dep_con = advcon[0]
                # dep_graph.remove_dependency(para, dep_con)
                # otherwise, the dep_con will be recovered by adv_modifier, may cause further question
            elif coloncon:
                dep_con = coloncon[0]
            else:
                dep_con = None

            predicates.append(dep_con)

        if all(x is None for x in predicates):
            oia_pred_node = oia_graph.add_aux("PARATAXIS")
        else:
            if len(predicates) == 1:
                oia_pred_node = oia_graph.add_words(predicates[0].position)
            else:
                position = ["{1}"]
                for i, node in enumerate(predicates):
                    if node is not None:
                        position.extend(node.position)
                    position.append("{{{0}}}".format(i + 2))
                oia_pred_node = oia_graph.add_words(position)

        for idx, node in enumerate(parallel_nodes):
            oia_arg_node = oia_graph.add_words(node.position)
            oia_graph.add_argument(oia_pred_node, oia_arg_node, idx + 1)


        # nodes = [node, para]
        # nodes.sort(key=lambda x: x.LOC)
        # para, center = nodes
        # oia_center_node = oia_graph.add_words(center.position)
        # oia_graph.add_argument(oia_pred_node, oia_center_node, 1)
        #
        # oia_para_node = oia_graph.add_words(para.position)
        # oia_graph.add_argument(oia_pred_node, oia_para_node, 2)


def parallel_list(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    list_phrases = []
    for n in dep_graph.nodes():

        list_nodes = [n for n, l in dep_graph.children(n,
                                                       filter=lambda n, l: "list" in l)]

        if not list_nodes:
            continue

        list_nodes.append(n)
        list_nodes.sort(key=lambda n: n.LOC)

        list_phrases.append(list_nodes)

    for list_nodes in list_phrases:

        pred = oia_graph.add_aux("LIST")

        for idx, node in enumerate(list_nodes):
            oia_arg = oia_graph.add_words(node.position)
            oia_graph.add_argument(pred, oia_arg, idx + 1)

# def so(dep_graph:DependencyGraph, oia_graph: OIAGraph):
#     """
#
#     :param dep_graph:
#     :param oia_graph:
#     :return:
#     """
#
#
#     pattern = DependencyGraph()
#     v1 = pattern.create_node() # UPOS="VERB"
#     v2 = pattern.create_node()
#     so = pattern.create_node(LEMMA="so")
#
#     pattern.add_dependency(v1, v2, r'advmod')
#     pattern.add_dependency(v2, so, r"advmod")
#
#     for match in dep_graph.match(pattern):
#
#         dep_v1, dep_v2, dep_so = [match[x] for x in [v1, v2, so]]
#
#         oia_pred = oia_graph.add_word(dep_so.ID)
#         oia_v1 = oia_graph.add_word_with_head(dep_v1.LOC)
#         oia_v2 = oia_graph.add_word_with_head(dep_v2.LOC)
#
#         oia_graph.add_argument(oia_pred, oia_v1, 1)
#         oia_graph.add_argument(oia_pred, oia_v2, 2)
