"""
verb predicates
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes
from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphSuperNode


def be_not_phrase2(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    be_not = []
    # for pred_node in dep_graph.nodes(filter=lambda x: x.UPOS in {"VERB"}):
    for pred_node in dep_graph.nodes():
        # print('pred_node LEMMA:', pred_node.LEMMA, 'pred_node UPOS:', pred_node.UPOS)
        if not "be" in pred_node.LEMMA.split(" "):
            continue
        objs = []
        for child, rel in dep_graph.children(pred_node):
            if rel.startswith('obj'):
                objs.append(child)
        if not objs:
            continue
        objs.sort(key=lambda x: x.LOC)
        for obj in objs:
            def __interested_node2(n):
                # that conj is ommited
                return (n.UPOS == "PART" and "not" in n.LEMMA.split(" "))

            nodes_of_interests2 = [n for n, l in dep_graph.children(obj,
                                                                    filter=lambda n,
                                                                                  l: l == "advmod" and __interested_node2(
                                                                        n))]
            if not nodes_of_interests2:
                continue
            assert len(nodes_of_interests2) == 1
            not_node = nodes_of_interests2[0]
            be_not.append((pred_node, obj, not_node))
    for dep_be_node, dep_obj_node, dep_not_node in be_not:
        dep_graph.remove_dependency(dep_obj_node, dep_not_node, 'advmod')
        verb_node = merge_dep_nodes((dep_be_node, dep_not_node), UPOS=dep_be_node.UPOS, LOC=dep_be_node.LOC)
        dep_graph.replace_nodes([dep_be_node, dep_not_node], verb_node)


def be_not_phrase(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    pattern = DependencyGraph()

    be_node = pattern.create_node()  # contain the be verb
    obj_node = pattern.create_node()
    # not_node = pattern.create_node(UPOS="PART")
    not_node = pattern.create_node()

    pattern.add_node(be_node)
    pattern.add_node(obj_node)
    pattern.add_node(not_node)

    pattern.add_dependency(be_node, obj_node, r'\w*obj\w*')
    pattern.add_dependency(obj_node, not_node, r'\w*advmod\w*')

    be_not = []
    for match in dep_graph.match(pattern):
        # print("be_not_phrase match !!!!!!!!!!!!!!")
        dep_be_node = match[be_node]
        dep_obj_node = match[obj_node]
        dep_not_node = match[not_node]

        if not "be" in dep_be_node.LEMMA.split(" "):
            continue

        if not "not" in dep_not_node.LEMMA.split(" "):
            continue

        if (dep_not_node.LOC > dep_obj_node.LOC) or (dep_be_node.LOC > dep_not_node.LOC):
            continue
        be_not.append((dep_be_node, dep_obj_node, dep_not_node))

    for dep_be_node, dep_obj_node, dep_not_node in be_not:
        dep_graph.remove_dependency(dep_obj_node, dep_not_node, 'advmod')
        verb_node = merge_dep_nodes((dep_be_node, dep_not_node), UPOS=dep_be_node.UPOS, LOC=dep_be_node.LOC)
        dep_graph.replace_nodes([dep_be_node, dep_not_node], verb_node)


def be_adp_phrase(dep_graph: DependencyGraph):
    """
    example: is for xxx
    this should be not applied:
    1. if xxx is adj, then be_adj_verb will be applied;
    2. if xxx is NOUN, then copula_phrase will be applied
    note that there may be multiple adp:
    the insurgency is out of the picture
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    some_node = pattern.create_node()

    adp_node = pattern.create_node(UPOS="ADP")
    be_node = pattern.create_node(UPOS="AUX")

    pattern.add_dependency(some_node, be_node, r'cop')
    pattern.add_dependency(some_node, adp_node, r'case')

    verb_phrases = []

    for match in dep_graph.match(pattern):

        dep_be_node = match[be_node]
        dep_some_node = match[some_node]

        dep_adp_nodes = [n for n, l in
                         dep_graph.children(dep_some_node, filter=lambda n, l: "case" in l and n.UPOS == "ADP")]

        if not all(dep_be_node.LOC < x.LOC < dep_some_node.LOC for x in dep_adp_nodes):
            continue

        pred = [dep_be_node] + dep_adp_nodes
        head = dep_be_node

        verb_phrases.append((dep_some_node, pred, head))

    for dep_some_node, verbs, root in verb_phrases:

        if not all(dep_graph.get_node(v.ID) for v in verbs):
            continue  # has been processed

        verb_node = merge_dep_nodes(verbs, UPOS="AUX", LOC=root.LOC)

        for node in verbs:
            dep_graph.remove_dependency(dep_some_node, node)
        dep_graph.replace_nodes(verbs, verb_node)
        dep_graph.add_dependency(dep_some_node, verb_node, "cop")

        # oia_graph.add_word(verb_node.ID)


def subj_adp_phrase(dep_graph):
    """
    same as be_adp_phrase but the be verb is ommited
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    some_node = pattern.create_node()
    adp_node = pattern.create_node(UPOS="ADP")
    subj_node = pattern.create_node()

    pattern.add_dependency(some_node, subj_node, r'nsubj')
    pattern.add_dependency(some_node, adp_node, r'case')

    verb_phrases = []

    for match in dep_graph.match(pattern):

        dep_adp_node = match[adp_node]
        dep_subj_node = match[subj_node]
        dep_some_node = match[some_node]

        if dep_adp_node.LOC != dep_subj_node.LOC + 1:
            continue

        verb_phrases.append((dep_some_node, dep_adp_node, dep_subj_node))

    for dep_some_node, dep_adp_node, dep_subj_node in verb_phrases:
        # make the adp node as a fake be node,
        # so the be_adj_verb or copula_phrase can be called

        dep_graph.set_dependency(dep_some_node, dep_adp_node, "cop")
        dep_adp_node.UPOS = "AUX"


def be_adj_verb_phrase(dep_graph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    adj_node = pattern.create_node(UPOS="ADJ|ADV")
    be_node = pattern.create_node()  # contain the be verb

    pattern.add_node(adj_node)
    pattern.add_node(be_node)

    pattern.add_dependency(adj_node, be_node, r'cop')

    verb_phrases = []

    for match in dep_graph.match(pattern):

        dep_adj_node = match[adj_node]
        dep_be_node = match[be_node]

        if not "be" in dep_be_node.LEMMA.split(" "):
            continue

        if dep_be_node.LOC > dep_adj_node.LOC:
            # may be question
            continue

        if isinstance(dep_adj_node, DependencyGraphSuperNode) and dep_adj_node.is_conj:
            continue

        verb_phrases.append((dep_be_node, dep_adj_node))

    for be_node, adj_node in verb_phrases:

        conj_parents = [n for n, l in dep_graph.parents(adj_node) if "arg_con" in l]


        if conj_parents:
            adjv_brothers = [n for n, l in dep_graph.children(conj_parents[0])
                             if "arg_con" in l and n.UPOS in {"ADJ", "ADV"}]

            for node in adjv_brothers:
                if node != adj_node and len([n for n, l in dep_graph.children(node) if "cop" in l]) == 0:
                    node.FORM = "(be) " + node.FORM
                    node.LEMMA = "(be) " + node.LEMMA
                  #  node.position.insert(0, "(be)")

        verb_node = merge_dep_nodes([be_node, adj_node],
                                    UPOS="VERB",
                                    LOC=be_node.LOC
                                    )
        dep_graph.replace_nodes([be_node, adj_node], verb_node)


def get_adj_verb_phrase(dep_graph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    adj_node = pattern.create_node(UPOS="ADJ")
    get_node = pattern.create_node(LEMMA="get", UPOS="VERB")

    pattern.add_dependency(adj_node, get_node, r'aux')

    verb_phrases = []

    for match in dep_graph.match(pattern):

        dep_adj_node = match[adj_node]
        dep_get_node = match[get_node]

        if isinstance(dep_adj_node, DependencyGraphSuperNode) and dep_adj_node.is_conj:
            continue

        pred = [dep_get_node, dep_adj_node]
        head = dep_adj_node
        verb_phrases.append((pred, head))

    for verbs, root in verb_phrases:
        verb_node = merge_dep_nodes(verbs,
                                    UPOS="VERB",
                                    LOC=root.LOC
                                    )
        dep_graph.replace_nodes(verbs, verb_node)
        # oia_graph.add_word(verb_node.ID)


def there_be_verb_phrase(dep_graph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    there_node = pattern.create_node(FORM=r'there|There')
    be_node = pattern.create_node()

    pattern.add_dependency(be_node, there_node, r'\w*expl\w*')

    verb_phrases = []
    for match in dep_graph.match(pattern):

        dep_there_node = match[there_node]
        dep_be_node = match[be_node]

        if not "be" in dep_be_node.LEMMA.split(" "):
            continue

        pred = [dep_there_node, dep_be_node]
        head = dep_be_node

        verb_phrases.append((pred, head))

    for verbs, root in verb_phrases:
        verb_node = merge_dep_nodes(verbs,
                                    UPOS="VERB",
                                    LOC=root.LOC
                                    )

        dep_graph.replace_nodes(verbs, verb_node)


#       oia_pred_node = oia_graph.find_node_by_head(root.ID)

#       new_pred_node = OIAWordsNode((verb_node.ID,), verb_node.ID)
#       oia_graph.replace(oia_pred_node, new_pred_node)


def copula_phrase(dep_graph):
    """
    ##### Copula #####
    ##### She is a teacher #####
    ##### NOT HEADED by another VERB #####
    Note that "she is smarter", that is, the pattern  "x is adj"
    is processed by be_adj_verb_phrase,
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    # subj_node = pattern.create_node()
    obj_node = pattern.create_node()  # UPOS=r'(?!ADJ\b)\b\w+')
    # for the adj case, it sould be processed by be_adj_verb_phrase,
    # if not, it means it is a question, and then should be processed by me
    be_node = pattern.create_node()

    # pattern.add_dependency(obj_node, subj_node, r'\w*subj\w*')
    pattern.add_dependency(obj_node, be_node, r'\w*cop\w*')

    copula_phrases = []

    # dep_graph.visualize('before_copula.png')

    for match in dep_graph.match(pattern):
        # dep_subj_node = match[subj_node]
        dep_obj_node = match[obj_node]
        dep_be_node = match[be_node]

        copula_phrases.append((dep_obj_node, dep_be_node))

    for dep_obj_node, dep_be_node in copula_phrases:
        # TODO: which should be moved? not clear, for example, obl

        logger.debug("copula phrase detected")
        logger.debug(str(dep_be_node))
        logger.debug(str(dep_obj_node))

        # move children
        node_to_move = []
        for n, rels in dep_graph.children(dep_obj_node):
            if any(rels.startswith(x) for x in
                   {"nsubj", "csubj", "parataxis", "aux", "expl", 'advcl', 'advmod'}):  # obl is removed temporally
                node_to_move.append((n, rels))
            elif n.LOC < dep_obj_node.LOC and "mark" in rels:
                node_to_move.append((n, rels))
            else:
                pass
                logger.debug("node not added ")
                logger.debug(str(n))
                logger.debug(str(rels))

        for n, rels in node_to_move:
            dep_graph.remove_dependency(dep_obj_node, n)
            logger.debug("dependency removed")
            logger.debug(str(dep_obj_node))
            logger.debug(str(n))
            if n != dep_be_node:
                for rel in rels:
                    dep_graph.add_dependency(dep_be_node, n, rel)
                    logger.debug("dependency added")
                    logger.debug(str(dep_be_node))
                    logger.debug(str(n))

        # move parents
        node_to_move = []
        for n, rels in dep_graph.parents(dep_obj_node):
            if n != dep_be_node and not any(rels.startswith(x) for x in {"nsubj", "csubj", "obj"}):
                node_to_move.append((n, rels))

        for n, rels in node_to_move:
            dep_graph.remove_dependency(n, dep_obj_node)

            for rel in rels:
                dep_graph.add_dependency(n, dep_be_node, rel)

        dep_graph.remove_dependency(dep_obj_node, dep_be_node)

        if dep_obj_node.UPOS == "ADV":
            dep_graph.add_dependency(dep_be_node, dep_obj_node, "advmod")
        else:
            dep_graph.add_dependency(dep_be_node, dep_obj_node, "obj")

        dep_be_node.UPOS = "VERB"
        #
        # oia_be_node = oia_graph.add_word(dep_be_node.ID)
        # oia_arg_node = oia_graph.add_word_with_head(dep_subj_node.LOC)
        # oia_graph.add_argument(oia_be_node, oia_arg_node, 1)
        #
        # oia_obj_node = oia_graph.add_word_with_head(dep_obj_node.LOC)
        # oia_graph.add_argument(oia_be_node, oia_obj_node, 2)
