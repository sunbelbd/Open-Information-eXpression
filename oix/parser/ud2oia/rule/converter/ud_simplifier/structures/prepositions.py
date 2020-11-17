"""
prepositions
"""

import logging

from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode


# from oix.oiagraph.graphs.oia_graph import OIAWordsNode, OIAGraph


def such_that(dep_graph: DependencyGraph):
    """
    ##### such a high price that
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = DependencyGraphNode(UPOS="NOUN")
    such_node = DependencyGraphNode(FORM="such")
    clause_pred_node = DependencyGraphNode(UPOS="VERB")
    that_node = DependencyGraphNode(FORM="that")

    pattern.add_nodes([noun_node, such_node, clause_pred_node, that_node])
    pattern.add_dependency(noun_node, such_node, r'det:predet')
    pattern.add_dependency(such_node, clause_pred_node, r'advcl:that')
    pattern.add_dependency(clause_pred_node, that_node, r'mark')

    such_that_pred = []
    for match in dep_graph.match(pattern):

        dep_noun_node = match[noun_node]
        dep_such_node = match[such_node]
        dep_clause_pred_node = match[clause_pred_node]
        dep_that_node = match[that_node]

        if dep_such_node.LOC < dep_noun_node.LOC < dep_that_node.LOC < dep_clause_pred_node.LOC:
            such_that_pred.append((dep_noun_node, dep_such_node, dep_clause_pred_node, dep_that_node))

    for dep_noun_node, dep_such_node, dep_clause_pred_node, dep_that_node in such_that_pred:
        nodes = [dep_such_node, dep_that_node]
        such_that_pred = merge_dep_nodes(nodes,
                                         UPOS="SCONJ",
                                         LOC=dep_that_node.LOC
                                         )
        dep_graph.add_node(such_that_pred)
        dep_graph.add_dependency(dep_noun_node, dep_clause_pred_node, "advcl:" + such_that_pred.FORM)
        dep_graph.add_dependency(dep_clause_pred_node, such_that_pred, "mark")

        dep_graph.remove_node(dep_such_node)
        dep_graph.remove_node(dep_that_node)


def amod_obl(dep_graph: DependencyGraph):
    """
    ##### include: more than, successful by
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = DependencyGraphNode(UPOS=r"NOUN|PRON")
    adj_node = DependencyGraphNode(UPOS="ADJ")
    adp_node = DependencyGraphNode(UPOS="ADP")
    obl_node = DependencyGraphNode()

    pattern.add_nodes([noun_node, adj_node, adp_node, obl_node])
    pattern.add_dependency(noun_node, adj_node, r'amod')
    pattern.add_dependency(adj_node, obl_node, r'obl:\w+')
    pattern.add_dependency(obl_node, adp_node, r'case')

    more_than_pred = []
    for match in dep_graph.match(pattern):

        dep_noun_node = match[noun_node]
        dep_adj_node = match[adj_node]
        dep_obl_node = match[obl_node]
        dep_adp_node = match[adp_node]

        obl_nodes = list(dep_graph.children(dep_adj_node, filter=lambda n, l: "obl" in l))

        if len(obl_nodes) > 1:
            # similar in form to the one
            continue

        if dep_adp_node.FORM not in dep_graph.get_dependency(dep_adj_node, dep_obl_node).values():
            continue

        if dep_noun_node.LOC < dep_adj_node.LOC < dep_adp_node.LOC < dep_obl_node.LOC:
            more_than_pred.append((dep_noun_node, dep_adj_node, dep_obl_node, dep_adp_node))

    for dep_noun_node, dep_adj_node, dep_obl_node, dep_adp_node in more_than_pred:
        nodes = [dep_adj_node, dep_adp_node]
        more_than_pred = merge_dep_nodes(nodes,
                                         UPOS="ADP",
                                         LOC=dep_adp_node.LOC
                                         )
        dep_graph.remove_dependency(dep_noun_node, dep_adj_node)
        dep_graph.remove_dependency(dep_adj_node, dep_obl_node)

        dep_graph.replace_nodes([dep_adj_node, dep_adp_node], more_than_pred)
        dep_graph.add_dependency(dep_noun_node, dep_obl_node, "nmod:" + more_than_pred.FORM)


def acl_verb_obl_case(dep_graph: DependencyGraph):
    """
    something extracted by
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    subj_node = pattern.create_node()
    verb_node = pattern.create_node(UPOS="VERB")
    obj_node = pattern.create_node()
    case_node = pattern.create_node()

    pattern.add_dependency(subj_node, verb_node, r'acl')
    pattern.add_dependency(verb_node, obj_node, r'obl:\w*')
    pattern.add_dependency(obj_node, case_node, r'case')

    phrases = []

    for match in dep_graph.match(pattern):

        dep_subj_node = match[subj_node]
        dep_verb_node = match[verb_node]
        dep_obj_node = match[obj_node]
        dep_case_node = match[case_node]

        obl_nodes = [n for n, l in dep_graph.children(dep_verb_node,
                                                      filter=lambda n, l: l.startswith("obl"))]
        if len(obl_nodes) > 1:
            continue

        existing_obj_nodes = [n for n, l in dep_graph.children(dep_verb_node,
                                                               filter=lambda n, l: "obj" in l or "comp" in l)]
        if existing_obj_nodes:
            continue

        obl_rel = dep_graph.get_dependency(dep_verb_node, dep_obj_node)

        if dep_case_node.FORM not in obl_rel.values():
            continue

        # there are may be other cases, join them all
        dep_case_nodes = [n for n, l in dep_graph.children(dep_obj_node,
                                                           filter=lambda n, l: l.startswith("case") and
                                                                               dep_verb_node.LOC < n.LOC < dep_obj_node.LOC)]

        subjs = list(dep_graph.children(dep_verb_node, filter=lambda n, l: "subj" in l))

        if len(subjs) > 1:
            continue

        phrases.append((dep_subj_node, dep_verb_node, dep_obj_node, dep_case_nodes))

    for dep_subj_node, dep_verb_node, dep_obj_node, dep_case_nodes in phrases:
        new_verb_phrase = [dep_verb_node] + dep_case_nodes
        logging.debug("acl_verb_obl_case: we are merging nodes")
        logging.debug("\n".join(str(node) for node in new_verb_phrase))

        new_verb_node = merge_dep_nodes(new_verb_phrase,
                                        UPOS=dep_verb_node.UPOS,
                                        LOC=dep_verb_node.LOC,
                                        FEATS=dep_verb_node.FEATS
                                        )

        logging.debug("acl_verb_obl_case: we obtain a new node")
        logging.debug(str(new_verb_node))

        dep_graph.remove_dependency(dep_verb_node, dep_obj_node)
        for node in dep_case_nodes:
            dep_graph.remove_dependency(dep_obj_node, node)

        dep_graph.replace_nodes(new_verb_phrase, new_verb_node)
        dep_graph.add_dependency(new_verb_node, dep_obj_node, "obj")


def amod_xcomp_to_acl(dep_graph: DependencyGraph):
    """
    something extracted by
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = pattern.create_node(UPOS="NOUN")
    adj_node = pattern.create_node(UPOS="ADJ")
    verb_node = pattern.create_node(UPOS="VERB")

    pattern.add_dependency(noun_node, adj_node, r'amod')
    pattern.add_dependency(adj_node, verb_node, r"xcomp")

    for match in list(dep_graph.match(pattern)):

        dep_noun_node = match[noun_node]
        dep_verb_node = match[verb_node]
        dep_adj_node = match[adj_node]

        try:
            [dep_graph.get_node(x.ID) for x in [dep_noun_node, dep_verb_node, dep_adj_node]]
        except Exception as e:
            # has been processed by previous match
            continue

        xcomp_nodes = [n for n, l in dep_graph.children(dep_adj_node,
                                                        filter=lambda n, l: l.startswith("xcomp"))]

        mark_nodes_list = []

        for dep_xcomp_node in xcomp_nodes:

            mark_nodes = [n for n, l in dep_graph.children(dep_xcomp_node,
                                                           filter=lambda n, l: l.startswith("mark") and
                                                                               dep_adj_node.LOC < n.LOC < dep_xcomp_node.LOC)]
            if mark_nodes:
                mark_nodes_list.append(mark_nodes)

        if len(mark_nodes_list) > 1:
            raise Exception("Unexpected Situation Happened")

        new_verb_nodes = [dep_adj_node]
        if mark_nodes_list:
            mark_nodes = mark_nodes_list[0]

            new_verb_nodes.extend(mark_nodes)
            new_verb_nodes.sort(key=lambda x: x.LOC)

        new_verb_nodes = ["(be)"] + new_verb_nodes

        new_node = merge_dep_nodes(new_verb_nodes,
                                   UPOS="VERB",
                                   LOC=new_verb_nodes[-1].LOC,
                                   FEATS={"VerbForm": "Ger"}
                                   )

        dep_graph.replace_nodes(new_verb_nodes, new_node)

        dep_graph.set_dependency(dep_noun_node, new_node, "acl")

        for dep_xcomp_node in xcomp_nodes:
            dep_graph.remove_dependency(dep_xcomp_node, new_node)
            dep_graph.set_dependency(new_node, dep_verb_node, "obj")

#
# def in_order_to(dep_graph: DependencyGraph: OIAGraph):
#     """
#
#     :param dep_graph:
#     :param oia_graph:
#     :return:
#     """
#
#     verb_node = DependencyGraphNode(UPOS="VERB|NOUN|PRON|PROPN")
#     in_node = DependencyGraphNode(LEMMA="in")
#     order_node = DependencyGraphNode(LEMMA="order")
#     to_node = DependencyGraphNode(LEMMA="to")
#     verb2_node = DependencyGraphNode(UPOS="VERB|ADJ|NOUN|PROPN|PRON")
#
#     pattern1 = DependencyGraph()
#     pattern1.add_nodes([verb_node, in_node, order_node, to_node, verb2_node])
#     pattern1.add_dependency(verb_node, verb2_node, r'advmod')
#     pattern1.add_dependency(verb2_node, in_node, r'mark')
#     pattern1.add_dependency(in_node, order_node, r'fixed')
#     pattern1.add_dependency(verb2_node, mark, r'mark|case')
#
#     for match in list(dep_graph.match(pattern1)) + list(dep_graph.match(pattern2)):
#
#         dep_verb_node = match[verb_node]
#         dep_adv_node = match[adv_node]
#         dep_as1_node = match[as1_node]
#         dep_as2_node = match[as2_node]
#         dep_verb2_node = match[verb2_node]
#
#         if not (dep_as1_node.LOC < dep_adv_node.LOC < dep_as2_node.LOC < dep_verb2_node.LOC):
#             continue
#
#         as_as_pred.append((dep_as1_node, dep_as2_node, dep_adv_node,
#                            dep_verb_node, dep_verb2_node))
#
#         pred = [node for node in dep_graph.nodes()
#                 if dep_as1_node.LOC <= node.LOC <= dep_adv_node.LOC]
#         pred.append(dep_as2_node)
#         pred.sort(key=lambda x: x.LOC)
#         head = dep_adv_node
#
#         dep_asas_node = DependencyGraphNode(ID=" ".join([x.ID for x in pred]),
#                                             FORM=" ".join([x.FORM for x in pred]),
#                                             LEMMA=" ".join([x.LEMMA for x in pred]),
#                                             UPOS="ADP",
#                                             LOC=head.LOC
#                                             )
#
#         dep_graph.replace_nodes(pred, dep_asas_node)
#         dep_graph.delete_dependency(dep_verb2_node, dep_asas_node)
#         dep_graph.delete_dependency(dep_asas_node, dep_verb2_node)
#         dep_graph.delete_dependency(dep_verb_node, dep_asas_node)
#
#         if dep_verb_node.UPOS == "VERB":
#
#             dep_graph.set_dependency(dep_verb_node, dep_verb2_node, "advcl:" + dep_asas_node.FORM)
#             dep_graph.set_dependency(dep_verb2_node, dep_asas_node, "mark")
#         else:
#             dep_graph.set_dependency(dep_verb_node, dep_verb2_node, "obl:" + dep_asas_node.FORM)
#             dep_graph.set_dependency(dep_verb2_node, dep_asas_node, "case")
#
#         oia_graph.add_word(dep_asas_node.ID)
#
#
