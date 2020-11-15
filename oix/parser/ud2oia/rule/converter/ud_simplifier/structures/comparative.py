"""
separated, like "such as", "as as", "more than "
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode, in_interval


def separated_asas(dep_graph: DependencyGraph):
    """
    ##### Equality comparison #####
    ##### A is as X a C as B #####

    ##### the first 'as' is always the advmod of a following element, X, which is within the range of as... as #####
    ##### the second 'as' is always the dependent of B #####
    ##### B sometimes depends on the first 'as', sometimes dependts on X #####
    ##### Sometimes X has a head that is also within the range of as...as #####
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    adj_node = DependencyGraphNode(UPOS="ADJ")
    noun_node = DependencyGraphNode(UPOS="NOUN")
    as1_node = DependencyGraphNode(FORM="as")
    as2_node = DependencyGraphNode(FORM="as")
    obj_node = DependencyGraphNode()

    pattern.add_nodes([noun_node, adj_node, as1_node, as2_node, obj_node])
    pattern.add_dependency(noun_node, adj_node, r'amod')
    pattern.add_dependency(adj_node, as1_node, r'\w*advmod\w*')
    pattern.add_dependency(as1_node, obj_node, r'\w*advcl:as\w*')
    pattern.add_dependency(obj_node, as2_node, r'mark')

    as_as_pred = []
    for match in dep_graph.match(pattern):

        dep_noun_node = match[noun_node]
        dep_adj_node = match[adj_node]
        dep_as1_node = match[as1_node]
        dep_as2_node = match[as2_node]
        dep_obj_node = match[obj_node]

        if dep_as1_node.LOC < dep_adj_node.LOC < dep_noun_node.LOC < dep_as2_node.LOC < dep_obj_node.LOC:
            pred = [node for node in dep_graph.nodes() if dep_as1_node.LOC <= node.LOC <= dep_adj_node.LOC]
            pred.append(dep_as2_node)
            pred.sort(key=lambda x: x.LOC)
            head = dep_adj_node

            asas_node = merge_dep_nodes(pred,
                                        UPOS="ADJ",
                                        LOC=dep_as2_node.LOC
                                        )

            as_as_pred.append((pred, head, asas_node, dep_noun_node, dep_obj_node))

    for pred, head, asas_node, dep_noun_node, dep_obj_node in as_as_pred:
        dep_graph.replace_nodes(pred, asas_node)

        dep_graph.remove_dependency(asas_node, dep_obj_node)
        dep_graph.remove_dependency(dep_noun_node, asas_node)

        dep_graph.add_dependency(dep_noun_node, dep_obj_node, "acl:" + asas_node.FORM)


def continuous_asas(dep_graph: DependencyGraph):
    """
    ##### as far as I known #####

    ##### the first 'as' is always the advmod of a following element, X, which is within the range of as... as #####
    ##### the second 'as' is always the dependent of B #####
    ##### B sometimes depends on the first 'as', sometimes dependts on X #####
    ##### Sometimes X has a head that is also within the range of as...as #####
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    verb_node = DependencyGraphNode(UPOS="VERB|NOUN|PRON|PROPN")
    adv_node = DependencyGraphNode(UPOS="ADV|ADJ")
    as1_node = DependencyGraphNode(LEMMA="as")
    as2_node = DependencyGraphNode(LEMMA="as")
    verb2_node = DependencyGraphNode(UPOS="VERB|ADJ|NOUN|PROPN|PRON")
    # ADJ is for as soon as possible
    pattern1 = DependencyGraph()
    pattern1.add_nodes([verb_node, adv_node, as1_node, as2_node, verb2_node])
    pattern1.add_dependency(verb_node, adv_node, r'advmod|amod')
    pattern1.add_dependency(adv_node, as1_node, r'\w*advmod\w*')
    pattern1.add_dependency(as1_node, verb2_node, r'advcl:as|obl:as|advmod')
    pattern1.add_dependency(verb2_node, as2_node, r'mark|case')

    pattern2 = DependencyGraph()
    pattern2.add_nodes([verb_node, adv_node, as1_node, as2_node, verb2_node])
    pattern2.add_dependency(verb_node, adv_node, r'advmod|amod')
    pattern2.add_dependency(adv_node, as1_node, r'\w*advmod\w*')
    pattern2.add_dependency(adv_node, verb2_node, r'advcl:as|obl:as|advmod')
    pattern2.add_dependency(verb2_node, as2_node, r'mark|case')

    as_as_pred = []
    for match in list(dep_graph.match(pattern1)) + list(dep_graph.match(pattern2)):

        dep_verb_node = match[verb_node]
        dep_adv_node = match[adv_node]
        dep_as1_node = match[as1_node]
        dep_as2_node = match[as2_node]
        dep_verb2_node = match[verb2_node]

        if not (dep_as1_node.LOC < dep_adv_node.LOC < dep_as2_node.LOC < dep_verb2_node.LOC):
            continue

        as_as_pred.append((dep_as1_node, dep_as2_node, dep_adv_node,
                           dep_verb_node, dep_verb2_node))

        pred = [node for node in dep_graph.nodes()
                if dep_as1_node.LOC <= node.LOC <= dep_adv_node.LOC]
        pred.append(dep_as2_node)
        pred.sort(key=lambda x: x.LOC)
        head = dep_adv_node

        dep_asas_node = merge_dep_nodes(pred,
                                        UPOS="ADP",
                                        LOC=head.LOC
                                        )

        dep_graph.replace_nodes(pred, dep_asas_node)
        dep_graph.remove_dependency(dep_verb2_node, dep_asas_node)
        dep_graph.remove_dependency(dep_asas_node, dep_verb2_node)
        dep_graph.remove_dependency(dep_verb_node, dep_asas_node)

        if dep_verb_node.UPOS == "VERB":

            dep_graph.set_dependency(dep_verb_node, dep_verb2_node, "advcl:" + dep_asas_node.FORM)
            dep_graph.set_dependency(dep_verb2_node, dep_asas_node, "mark")
        else:
            dep_graph.set_dependency(dep_verb_node, dep_verb2_node, "obl:" + dep_asas_node.FORM)
            dep_graph.set_dependency(dep_verb2_node, dep_asas_node, "case")


def gradation(dep_graph: DependencyGraph):
    """
    TODO: do not match with the tech report, and the verb is not considered
    ##### Comparative #####
    ##### Periphrastic gradation #####
    ##### He runs faster than her #####
    ##### Martin is more intelligent than Donald #####
    ##### He is a nicer person than Tom
    ##### She is more than a regular cook
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()
    verb_node = pattern.create_node(UPOS="VERB|NOUN|PRON|PROPN|SYM")
    advj_node = pattern.create_node(UPOS="ADJ|ADV", FEATS={"Degree": "Cmp"})
    than_node = pattern.create_node(FORM="than")
    obj_node = pattern.create_node()

    pattern.add_dependency(verb_node, advj_node, r'advmod|amod')
    pattern.add_dependency(advj_node, obj_node, r'\w*(nmod:than|obl:than|advcl:than)\w*')
    pattern.add_dependency(obj_node, than_node, r'\w*case|mark\w*')

    for match in list(dep_graph.match(pattern)):

        dep_verb_node = match[verb_node]
        dep_advj_node = match[advj_node]
        dep_than_node = match[than_node]
        dep_obj_node = match[obj_node]

        def __valid_mod(n, l):
            return (l == "amod" or l == "advmod") and in_interval(n, None, dep_advj_node)

        aux_node = list(dep_graph.children(dep_advj_node, filter=__valid_mod))

        if aux_node:
            aux_node = aux_node[0][0]
            offsprings = dep_graph.offsprings(aux_node)

            more_than_nodes = offsprings + [dep_than_node]
        else:
            more_than_nodes = (dep_advj_node, dep_than_node)

        dep_more_than_node = merge_dep_nodes(more_than_nodes,
                                             UPOS="ADP",
                                             LOC=dep_than_node.LOC
                                             )

        dep_graph.replace_nodes(more_than_nodes, dep_more_than_node)
        dep_graph.remove_dependency(dep_obj_node, dep_more_than_node)
        dep_graph.remove_dependency(dep_more_than_node, dep_obj_node)
        dep_graph.remove_dependency(dep_verb_node, dep_more_than_node)

        if dep_verb_node.UPOS == "VERB":

            dep_graph.set_dependency(dep_verb_node, dep_obj_node, "advcl:" + dep_more_than_node.FORM)
            dep_graph.set_dependency(dep_obj_node, dep_more_than_node, "mark")
        else:
            dep_graph.set_dependency(dep_verb_node, dep_obj_node, "obl:" + dep_more_than_node.FORM)
            dep_graph.set_dependency(dep_obj_node, dep_more_than_node, "case")

#
# def asas(dep_graph, oia_graph):
#     """
#     ##### Equality comparison #####
#     ##### A is as X as B #####
#
#     ##### the first 'as' is always the advmod of a following element, X, which is within the range of as... as #####
#     ##### the second 'as' is always the dependent of B #####
#     ##### B sometimes depends on the first 'as', sometimes dependts on X #####
#     ##### Sometimes X has a head that is also within the range of as...as #####
#     :param sentence:
#     :return:
#     """
#
#     pattern = DependencyGraph()
#
#     advj_node = DependencyGraphNode()
#     as1_node = DependencyGraphNode(FORM="as")
#     as2_node = DependencyGraphNode(FORM="as")
#     obj_node = DependencyGraphNode()
#
#     pattern.add_nodes([advj_node, as1_node, as2_node])
#
#     pattern.add_dependency(advj_node, as1_node, r'\w*advmod\w*')
#     pattern.add_dependency(advj_node, obj_node, r'\w*nmod:as\w*')
#     pattern.add_dependency(obj_node, as2_node, r'case')
#
#     for match in dep_graph.match(pattern):
#
#         dep_advj_node = match[advj_node]
#         dep_as1_node = match[as1_node]
#         dep_as2_node = match[as2_node]
#         dep_obj_node = match[obj_node]
#
#         if dep_as1_node.ID < dep_advj_node.ID < dep_as2_node.ID < dep_obj_node.ID:
#
#             pred_node = oia_graph.add_word(range(dep_as1_node.ID, dep_as2_node.ID + 1))
#             obj_node = oia_graph.add_word_with_head(dep_obj_node.LOC)
#
#             oia_graph.add_argument(pred_node, obj_node, 2)
#
