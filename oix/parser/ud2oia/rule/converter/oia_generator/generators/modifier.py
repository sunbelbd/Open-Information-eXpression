"""
modifier
"""
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.parser.ud2oia.rule.converter.utils import continuous_component

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
# from oix.oiagraph.graphs.oia_graph import OIAAuxNode, OIAWordsNode, OIAGraph
from oix.oia.graphs.oia_graph import OIAGraph
from loguru import logger

def find_head(graph, nodes, context: UD2OIAContext):
    """

    :param graph:
    :param nodes:
    :return:
    """

    in_degrees = graph.in_degree(nodes)
    for node, degree in in_degrees:
        if degree == 0:
            return node


def adj_modifier(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    adj previous to noun is coped with by noun phrase
    this process the case that adj is behind the noun
    #################### a pretty little boy ########################
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = pattern.create_node()  # UPOS="NOUN|PRON|PROPN")
    adj_node = pattern.create_node()  # UPOS="ADJ|NOUN")

    pattern.add_dependency(noun_node, adj_node, r'amod')

    for match in dep_graph.match(pattern):
        dep_noun_node = match[noun_node]
        dep_adj_node = match[adj_node]

        oia_noun_node = oia_graph.add_words(dep_noun_node.position)

        oia_adj_node = oia_graph.add_words(dep_adj_node.position)
        logger.debug("adj_modifier: ")
        logger.debug(dep_noun_node.position)
        logger.debug(oia_noun_node)
        logger.debug(dep_adj_node.position)
        logger.debug(oia_adj_node)

        oia_graph.add_mod(oia_adj_node, oia_noun_node)

    #
    # for tok in dep_graph.nodes():
    #     if tok.LEMMA == "not":
    #         continue
    #
    #     # if tok is not the head of np discovered by the simple_np rule
    #     # continue
    #
    #     children = []
    #     for child_tok, child_rel in dep_graph.children(tok):
    #
    #         # modifier as functions
    #         # (arg, modifier) pairs
    #         if child_rel in ['amod', 'nummod', 'nmod'] or (
    #                 child_rel == 'advmod' and child_tok.UPOS != 'VERB'):
    #             children.append(child_tok)
    #
    #     if not children:
    #         continue
    #
    #     modifier_graph = dep_graph.subgraph(children)
    #
    #     children.sort(key=lambda x: x.ID)
    #
    #     for pre_node, post_node in pairwise(children):
    #
    #         if not modifier_graph.has_path(pre_node, post_node):
    #             modifier_graph.add_dependency(pre_node, post_node, "conj:and")
    #
    #     assert modifier_graph.is_connected()
    #
    #     dependency_to_del = []
    #
    #     for node1, node2, dependency in modifier_graph.dependencies():
    #
    #         if dependency == "conj:or":
    #             dependency_to_del.append((node1, node2))
    #
    #     for node1, node2 in dependency_to_del:
    #         modifier_graph.delete_dependency(node1, node2)
    #
    #     and_components = list(modifier_graph.connected_components())
    #
    #     add_nodes = []
    #
    #     for arg_idx, and_component in enumerate(and_components):
    #
    #         and_component.sort(key=lambda x: x.ID)
    #
    #         if len(and_component) > 1:
    #             node = OIAAuxNode(label="AND")
    #
    #             for idx, arg in enumerate(and_component):
    #                 arg_node = OIAWordsNode(arg.ID, arg.ID)
    #                 oia_graph.add_node(arg_node)
    #                 oia_graph.add_argument(node, arg_node, idx)
    #         else:
    #             arg = and_component[0]
    #             node = OIAWordsNode(arg.ID, arg.ID)
    #
    #         oia_graph.add_node(node)
    #         add_nodes.append(node)
    #
    #     if len(and_components) > 1:
    #         node = OIAAuxNode(label="OR")
    #
    #         for idx, arg_node in enumerate(add_nodes):
    #             oia_graph.add_argument(node, arg_node, idx)
    #     else:
    #         node = add_nodes[0]
    #
    #     oia_graph.add_node(node)
    #     word_node = oia_graph.add_word(tok.ID)
    #     oia_graph.add_function(node, word_node)


def acl_mod_verb(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    this is called after adnominal_clause_mark, which means there is no mark
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = pattern.create_node(UPOS="NOUN|PRON|PROPN|ADJ|ADV|NUM")
    # ADJ is for the cases that "many/some" are abbrv of many X/some X, representing NOUN
    # ADV is for the case of "here" for "i am here thinking xxx"
    verb_node = pattern.create_node(UPOS="VERB|AUX")
    # aux is for can, have which ommits the true verb

    pattern.add_nodes([noun_node, verb_node])

    pattern.add_dependency(noun_node, verb_node, r'acl')

    for match in dep_graph.match(pattern):

        dep_noun_node = match[noun_node]
        dep_verb_node = match[verb_node]

        if context.is_processed(dep_noun_node, dep_verb_node):
            continue

        if oia_graph.has_relation(dep_noun_node, dep_verb_node, direct_link=False):
            continue

        oia_verb_node = oia_graph.add_words(dep_verb_node.position)
        oia_noun_node = oia_graph.add_words(dep_noun_node.position)

        dep = dep_graph.get_dependency(dep_noun_node, dep_verb_node)
        labels = [x for x in dep.rels if x.startswith("acl:")]

        pred = None

        if labels:
            assert len(labels) == 1
            label = labels[0]
            pred = label.split(":")[1]
            if pred == "relcl":
                pred = None

        # if pred:
        #     # there is no mark, but we add it because it may be because of not being shared in conjunction
        #
        #     oia_pred_node = oia_graph.add_aux(pred)
        #     oia_graph.add_argument(oia_pred_node, oia_noun_node, 1, mod=True)
        #     oia_graph.add_argument(oia_pred_node, oia_verb_node, 2)
        # else:

        oia_graph.add_mod(oia_verb_node, oia_noun_node)
        #
        # if "Tense" in dep_verb_node.FEATS and "Past" in dep_verb_node.FEATS["Tense"]:
        #
        #     # following code is for the case;
        #     # The sheikh in wheel-chair has been attacked with a F-16-launched bomb.
        #     # but is useless since the F-16-launched is recognized as a verb now
        #     # compound = [n for n, l in dep_graph.children(dep_verb_node, filter=lambda x, l: "compound" in l)]
        #     # compound.sort(key=lambda x: x.LOC)
        #     #
        #     # punct = [n for n, l in dep_graph.children(dep_verb_node,
        #     #                                           filter=lambda x, l: "punct" in l and x.FORM == "-")]
        #     # punct.sort(key=lambda x: x.LOC)
        #     #
        #     # if compound and punct:
        #     #     compound = compound[-1]
        #     #     punct = punct[-1]
        #     #
        #     #
        #     #     if compound.LOC < dep_verb_node.LOC - 1 and punct.LOC == dep_verb_node.LOC - 1:
        #     #         subject_nodes = list(dep_graph.offsprings(compound))
        #     #         subject_nodes.sort(key=lambda x: x.LOC)
        #     #         subject_words = [x.ID for x in subject_nodes]
        #     #         head = compound.ID
        #     #
        #     #         subj_node = oia_graph.add_word(subject_words, head)
        #     #         pred_node = oia_graph.add_word_with_head(dep_verb_node.LOC)
        #     #         obj_node = oia_graph.add_word_with_head(dep_noun_node.LOC)
        #     #
        #     #         oia_graph.add_argument(pred_node, subj_node, 1)
        #     #         oia_graph.add_argument(pred_node, obj_node, 2, mod=True)
        #     #
        #     # else:
        #     pred_node = oia_graph.add_word_with_head(dep_verb_node.LOC)
        #     subj_node = oia_graph.add_word_with_head(dep_noun_node.LOC)
        #     oia_graph.add_argument(pred_node, subj_node, 1, mod=True)
        #
        # # elif "VerbForm" in dep_verb_node.FEATS and "Ger" in dep_verb_node.FEATS["VerbForm"]:
        # #     # There are many online sites offering booking facilities
        # #     pred_node = oia_graph.add_word_with_head(dep_verb_node.LOC)
        # #     subj_node = oia_graph.add_word_with_head(dep_noun_node.LOC)
        # #
        # #     oia_graph.add_argument(pred_node, subj_node, 1, mod=True)
        # else:
        #     pred_node = oia_graph.add_word_with_head(dep_verb_node.LOC)
        #     subj_node = oia_graph.add_word_with_head(dep_noun_node.LOC)
        #
        #     oia_graph.add_argument(pred_node, subj_node, 1, mod=True)


def acl_mod_adjv(dep_graph, oia_graph, context: UD2OIAContext):
    """
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = DependencyGraphNode(UPOS="NOUN|PRON|PROPN|NUM")
    adjv_node = DependencyGraphNode(UPOS="ADJ|ADV")

    pattern.add_nodes([noun_node, adjv_node])

    pattern.add_dependency(noun_node, adjv_node, r'acl')

    for match in dep_graph.match(pattern):
        dep_noun_node = match[noun_node]
        dep_adjv_node = match[adjv_node]

        oia_noun_node = oia_graph.add_words(dep_noun_node.position)
        oia_adjv_node = oia_graph.add_words(dep_adjv_node.position)

        oia_graph.add_mod(oia_adjv_node, oia_noun_node)


def nmod_with_case(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    #################### nmod:x ########################

    ##### the office of the chair #####
    ##### Istanbul in Turkey #####
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()

    parent_node = DependencyGraphNode()
    child_node = DependencyGraphNode()
    case_node = DependencyGraphNode()

    pattern.add_nodes([parent_node, child_node, case_node])

    pattern.add_dependency(parent_node, child_node, r'\w*nmod\w*')
    pattern.add_dependency(child_node, case_node, r'\w*case\w*')

    for match in dep_graph.match(pattern):

        dep_parent_node = match[parent_node]
        dep_child_node = match[child_node]
        dep_case_node = match[case_node]

        rel = dep_graph.get_dependency(dep_parent_node, dep_child_node)

        # vs, lemma = versus
        # according, lemma = accord,
        # but rel always select the shorter one

        if oia_graph.has_relation(dep_parent_node, dep_child_node):
            continue

        if rel != "nmod:" + dep_case_node.LEMMA and rel != 'nmod:' + dep_case_node.FORM:
            pred_node = oia_graph.add_words(dep_case_node.position)
        else:
            pred_node = oia_graph.add_words(dep_case_node.position)

        arg1_node = oia_graph.add_words(dep_parent_node.position)
        arg2_node = oia_graph.add_words(dep_child_node.position)

        oia_graph.add_argument(pred_node, arg1_node, 1, mod=True)
        oia_graph.add_argument(pred_node, arg2_node, 2)


def nmod_without_case(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    #################### nmod:x ########################

    :param sentence:
    :return:
    """

    pattern = DependencyGraph()

    center_node = pattern.create_node()
    modifier_node = pattern.create_node()

    pattern.add_dependency(center_node, modifier_node, r'\w*nmod\w*')

    for match in dep_graph.match(pattern):

        dep_center_node = match[center_node]
        dep_modifier_node = match[modifier_node]

        rels = dep_graph.get_dependency(dep_center_node, dep_modifier_node)

        if "nmod:poss" in rels and dep_center_node in set(dep_graph.offsprings(dep_modifier_node)):
            # whose in there
            continue

        if oia_graph.has_relation(dep_center_node, dep_modifier_node, direct_link=False):
            continue

        oia_center_node = oia_graph.add_words(dep_center_node.position)
        oia_modifier_node = oia_graph.add_words(dep_modifier_node.position)

        oia_graph.add_mod(oia_modifier_node, oia_center_node)


def adv_ccomp(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    # TODO: it seems that in UD labeling, adv is used instead of adj for noun
    # verb_node = pattern.create_node(UPOS="VERB|NOUN|PROPN")
    adv_node = pattern.create_node(UPOS="ADV|X|NOUN|PART")  # part is for "not"
    ccomp_node = pattern.create_node()

    # pattern.add_dependency(verb_node, adv_node, r'advmod')
    pattern.add_dependency(adv_node, ccomp_node, r"ccomp|xcomp")

    patterns = []
    for match in dep_graph.match(pattern):

        # dep_verb_node = match[verb_node]
        dep_adv_node = match[adv_node]
        dep_ccomp_node = match[ccomp_node]

        if oia_graph.has_relation(dep_adv_node, dep_ccomp_node):
            continue

        dep_case_nodes = [n for n, l in dep_graph.children(dep_ccomp_node,
                                                           filter=lambda n, l: "case" == l and
                                                                               dep_adv_node.LOC < n.LOC < dep_ccomp_node.LOC)]

        if dep_case_nodes:
            dep_case_nodes = continuous_component(dep_case_nodes, dep_case_nodes[0])
            predicate_nodes = [dep_adv_node] + dep_case_nodes
            predicate_nodes.sort(key=lambda n: n.LOC)
        else:
            predicate_nodes = [dep_adv_node]

        dep_subj_nodes = [n for n, l in dep_graph.parents(dep_adv_node,
                                                          filter=lambda n, l: "advmod" == l and
                                                                              n.UPOS in {"ADV", "X", "NOUN"})]
        if len(dep_subj_nodes) > 1:
            raise Exception("Multiple subject")
        elif len(dep_subj_nodes) > 0:
            dep_subj_node = dep_subj_nodes[0]
        else:
            dep_subj_node = None

        patterns.append([dep_subj_node, predicate_nodes, dep_ccomp_node])

    for dep_subj_node, predicate_nodes, dep_ccomp_node in patterns:

        if len(predicate_nodes) > 1:

            new_pred_node = dep_graph.create_node(
                ID=" ".join([x.ID for x in predicate_nodes]),
                FORM=" ".join([x.FORM for x in predicate_nodes]),
                LEMMA=" ".join([x.LEMMA for x in predicate_nodes]),
                UPOS="ADV",
                LOC=predicate_nodes[0].LOC
            )

            new_pred_node.aux = True

            dep_graph.replace_nodes(predicate_nodes, new_pred_node)

            dep_graph.remove_dependency(dep_ccomp_node, new_pred_node)

        else:
            new_pred_node = predicate_nodes[0]

        oia_pred_node = oia_graph.add_words(new_pred_node.position)

        if dep_subj_node:
            oia_subj_node = oia_graph.add_words(dep_subj_node.position)
            oia_graph.add_argument(oia_pred_node, oia_subj_node, 1, mod=True)

        else:
            oia_ccomp_node = oia_graph.add_words(dep_ccomp_node.position)
            oia_graph.add_argument(oia_pred_node, oia_ccomp_node, 2)


def adv_verb_modifier(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    the adv before the verb should be processed by verb_phrase
    this converter should process the adv after the verb
    verb1 in order to verb2
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()

    # TODO: it seems that in UD labeling, adv is used instead of adj for noun
    verb_node = DependencyGraphNode(UPOS="VERB|NOUN|PROPN|AUX|PRON")  # aux is for be word
    adv_node = DependencyGraphNode(UPOS="ADV|X|NOUN|ADJ|VERB")

    pattern.add_nodes([verb_node, adv_node])

    pattern.add_dependency(verb_node, adv_node, r'advmod')

    for match in dep_graph.match(pattern):

        dep_verb_node = match[verb_node]
        dep_adv_node = match[adv_node]

        if context.is_processed(dep_verb_node, dep_adv_node):
            continue

        if oia_graph.has_relation(dep_verb_node, dep_adv_node):
            continue

        obl_children = [x for x, l in dep_graph.children(dep_adv_node, filter=lambda n, l: l.startswith("obl"))]

        obl_node = None
        obl_has_case = False
        if len(obl_children) == 1:

            obl_node = obl_children[0]

            case_nodes = list(n for n, l in dep_graph.children(obl_node, filter=lambda n, l: "case" in l))

            if case_nodes:
                # if obl with case, let the oblique to process it
                obl_has_case = True

        mark_children = [x for x, l in dep_graph.children(dep_adv_node, filter=lambda n, l: l.startswith("mark"))]

        oia_verb_node = oia_graph.add_words(dep_verb_node.position)
        oia_adv_node = oia_graph.add_words(dep_adv_node.position)

        if obl_node and not obl_has_case:
            # arg_nodes = list(dep_graph.offsprings(obl_node))
            # arg_nodes.sort(key=lambda x: x.LOC)
            # arg_words = [x.ID for x in arg_nodes]
            # head = obl_node.ID

            oia_arg_node = oia_graph.add_words(obl_node.position)

            oia_graph.add_argument(oia_adv_node, oia_verb_node, 1, mod=True)
            oia_graph.add_argument(oia_adv_node, oia_arg_node, 2)
        else:
            if mark_children:
                mark_node = mark_children[0]
                oia_pred_node = oia_graph.add_words(mark_node.position)

                oia_graph.add_argument(oia_pred_node, oia_verb_node, 1, mod=True)
                oia_graph.add_argument(oia_pred_node, oia_adv_node, 2)

            else:
                oia_graph.add_mod(oia_adv_node, oia_verb_node)


def adv_adj_modifier(dep_graph, oia_graph, context: UD2OIAContext):
    """
    the adv before the verb should be processed by verb_phrase
    this converter should process the adv after the verb
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()

    # TODO: it seems that in UD labeling, adv is used instead of adj for noun
    adj_node = DependencyGraphNode(UPOS="ADJ")
    adv_node = DependencyGraphNode(UPOS="ADV|X|NOUN")

    pattern.add_nodes([adj_node, adv_node])

    pattern.add_dependency(adj_node, adv_node, r'advmod')

    for match in dep_graph.match(pattern):

        dep_adj_node = match[adj_node]
        dep_adv_node = match[adv_node]

        if oia_graph.has_relation(dep_adj_node, dep_adv_node):
            continue

        oia_adj_node = oia_graph.add_words(dep_adj_node.position)
        oia_adv_node = oia_graph.add_words(dep_adv_node.position)

        oia_graph.add_mod(oia_adv_node, oia_adj_node)


def obl_modifier(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    the adv before the verb should be processed by verb_phrase
    this converter should process the adv after the verb
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()

    # TODO: it seems that in UD labeling, adv is used instead of adj for noun
    modified_node = DependencyGraphNode()
    modifier_node = DependencyGraphNode()

    pattern.add_nodes([modified_node, modifier_node])

    pattern.add_dependency(modified_node, modifier_node, r'\bobl')

    for match in dep_graph.match(pattern):

        dep_modified_node = match[modified_node]
        dep_modifier_node = match[modifier_node]

        if oia_graph.has_relation(dep_modified_node, dep_modifier_node, direct_link=False):
            continue

        oia_modified_node = oia_graph.add_words(dep_modified_node.position)
        oia_modifier_node = oia_graph.add_words(dep_modifier_node.position)

        oia_graph.add_mod(oia_modifier_node, oia_modified_node)


def det_predet(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for n1, n2, dep in dep_graph.dependencies():

        if "det:predet" in dep:
            oia_n1 = oia_graph.add_words(n1.position)
            oia_n2 = oia_graph.add_words(n2.position)
            oia_graph.add_mod(oia_n2, oia_n1)
