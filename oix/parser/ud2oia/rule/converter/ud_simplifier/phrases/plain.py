"""
multi-word
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes
from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode, DependencyGraphSuperNode
from oix.oia.standard import NOUN_UPOS


def multi_words_case(dep_graph: DependencyGraph):
    """
    :TODO  add example case
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    noun_node = DependencyGraphNode()
    x_node = DependencyGraphNode()
    case_node = DependencyGraphNode()

    pattern.add_node(noun_node)
    pattern.add_node(x_node)
    pattern.add_node(case_node)

    pattern.add_dependency(noun_node, x_node, r'\w*:\w*')
    pattern.add_dependency(x_node, case_node, r'\bcase\b')



    for match in list(dep_graph.match(pattern)):

        multiword_cases = []

        dep_noun_node = match[noun_node]
        dep_x_node = match[x_node]
        dep_case_node = match[case_node]

        if not dep_graph.has_node(dep_case_node):
            continue

        direct_case_nodes = [n for n, l in dep_graph.children(dep_x_node, filter=lambda n, l: "case" == l)]
        all_case_nodes = set()
        for node in direct_case_nodes:
            all_case_nodes.update(dep_graph.offsprings(node))

        if len(all_case_nodes) == 1:
            continue

        all_case_nodes = sorted(list(all_case_nodes), key=lambda n: n.LOC)
        logger.debug("multi case discovered")
        for node in all_case_nodes:
            logger.debug(str(node))

        #        if len(case_nodes) > 2:
        #            raise Exception("multi_words_case: Unexpected Situation: nodes with more than two cases")

        x_rel = dep_graph.get_dependency(dep_noun_node, dep_x_node)

        for rel in x_rel:
            if ":" in rel:
                # print('-----------------rel:        ',rel)

                rel_str, case_str = rel.split(":")
                # some times, the rel only contains one word
                # Example :
                # that OBSF values within the extended trial balance may be misstated due to data issues ( above and beyond existing conversations with AA on model simplifications)
                if case_str in "_".join([x.LEMMA for x in all_case_nodes]):
                    multiword_cases.append((dep_noun_node, dep_x_node, dep_case_node, all_case_nodes, rel_str))

        for dep_noun_node, dep_x_node, dep_case_node, case_nodes, rel_str in multiword_cases:

            logger.debug("we are merging:")
            for node in case_nodes:
                logger.debug(str(node))

            if not all([dep_graph.has_node(x) for x in case_nodes]):
                continue

            new_case_node = merge_dep_nodes(case_nodes,
                                            UPOS=dep_case_node.UPOS,
                                            LOC=dep_case_node.LOC
                                            )
            dep_graph.replace_nodes(case_nodes, new_case_node)
            dep_graph.remove_dependency(dep_noun_node, dep_x_node)
            dep_graph.add_dependency(dep_noun_node, dep_x_node,
                                     rel_str + ":" + " ".join([x.LEMMA for x in case_nodes]))


def multi_words_mark(dep_graph: DependencyGraph):
    """
    arise on to
    the "on to" should be combined
    :param dep_graph:
    :param oia_graph:
    :return:
    """
    # print('multi_words_mark')
    mark_phrases = []

    for node in dep_graph.nodes():
        marks = []
        for n, l in dep_graph.children(node, filter=lambda n, l: "mark" in l):
            marks.extend(dep_graph.offsprings(n))

        if not marks:
            continue
        # print('multi_words_mark marks:', marks)
        if len(marks) > 1:
            if any([x.UPOS in {"NOUN", "NUM", "VERB", "ADJ", "ADV", "PRON"} for x in marks]):
                continue

            marks.sort(key=lambda n: n.LOC)
            mark_phrases.append((node, marks))

    for node, marks in mark_phrases:
        # print('multi_words_mark marks:', marks)
        if not all([dep_graph.get_node(x.ID) for x in marks]):
            continue

        mark_min_loc = marks[0].LOC
        mark_max_loc = marks[-1].LOC
        marks = [n for n in dep_graph.nodes() if mark_min_loc <= n.LOC <= mark_max_loc]
        marks.sort(key=lambda n: n.LOC)

        if any([x.UPOS in NOUN_UPOS for x in marks]):
            continue
        # print('marks:')
        # for nnnn in marks:
        #     print(nnnn)
        new_mark_node = merge_dep_nodes(marks,
                                        UPOS=marks[0].UPOS,
                                        LOC=marks[0].LOC
                                        )
        for mark in marks:
            dep_graph.remove_dependency(node, mark)
        dep_graph.replace_nodes(marks, new_mark_node)
        dep_graph.add_dependency(node, new_mark_node, "mark")

        # mark_lemmas = set(n.LEMMA for n in marks)
        # for parent, rels in dep_graph.parents(node):
        #     for rel in rels:
        #         if ":" in rel:
        #             prefix, word = rel.split(":")
        #             if word in mark_lemmas:
        #                 dep_graph.remove_dependency(parent, node, rel)
        #                 dep_graph.add_dependency(parent, node, ":".join((prefix, new_mark_node.LEMMA)))


def multi_words_cc(dep_graph: DependencyGraph):
    """
    arise on to
    the "on to" should be combined
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    mark_phrases = []

    for node in dep_graph.nodes():
        marks = []
        for n, l in dep_graph.children(node, filter=lambda n, l: "cc" == l):
            marks.extend(dep_graph.offsprings(n))

        if not marks:
            continue

        if len(marks) > 1:
            if any([x.UPOS in {"NOUN", "NUM", "VERB"} for x in marks]):
                continue

            marks.sort(key=lambda n: n.LOC)
            mark_phrases.append((node, marks))

    for node, marks in mark_phrases:

        mark_min_loc = marks[0].LOC
        mark_max_loc = marks[-1].LOC
        marks = [n for n in dep_graph.nodes() if mark_min_loc <= n.LOC <= mark_max_loc]

        if any([x.UPOS in {"NOUN", "NUM", "VERB"} for x in marks]):
            continue
        if not all([dep_graph.get_node(x.ID) for x in marks]):
            continue
        new_mark_node = merge_dep_nodes(marks,
                                        UPOS=marks[0].UPOS,
                                        LOC=marks[0].LOC
                                        )

        dep_graph.replace_nodes(marks, new_mark_node)
        for mark in marks:
            dep_graph.remove_dependency(node, mark)

        if dep_graph.get_node(node.ID):
            dep_graph.add_dependency(node, new_mark_node, "cc")

        # mark_lemmas = set(n.LEMMA for n in marks)
        # for parent, rels in dep_graph.parents(node):
        #     for rel in rels:
        #         if ":" in rel:
        #             prefix, word = rel.split(":")
        #             if word in mark_lemmas:
        #                 dep_graph.remove_dependency(parent, node, rel)
        #                 dep_graph.add_dependency(parent, node, ":".join((prefix, new_mark_node.LEMMA)))


def multi_word_sconj(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    verb_node = pattern.create_node(UPOS="VERB")
    verb2_node = pattern.create_node(UPOS="VERB")
    mark_node = pattern.create_node(UPOS="SCONJ")

    pattern.add_dependency(verb_node, verb2_node, r'advcl:\w*')
    pattern.add_dependency(verb2_node, mark_node, r'mark')

    mark_phrases = []
    for match in dep_graph.match(pattern):

        dep_verb_node = match[verb_node]
        dep_verb2_node = match[verb2_node]
        dep_mark_node = match[mark_node]

        if dep_mark_node.LEMMA not in dep_graph.get_dependency(dep_verb_node, dep_verb2_node).values():
            continue

        new_marks = list(dep_graph.offsprings(dep_mark_node))
        if len(new_marks) == 1:
            continue

        new_marks.sort(key=lambda n: n.LOC)
        mark_phrases.append((dep_verb_node, dep_verb2_node, dep_mark_node, new_marks))

    for (dep_verb_node, dep_verb2_node, dep_mark_node, new_marks) in mark_phrases:

        if not all([dep_graph.get_node(x.ID) for x in new_marks]):
            continue

        dep_graph.remove_dependency(dep_verb2_node, dep_mark_node)
        dep_graph.remove_dependency(dep_verb_node, dep_verb2_node)

        new_mark_node = merge_dep_nodes(new_marks,
                                        UPOS=dep_mark_node.UPOS,
                                        LOC=dep_mark_node.LOC
                                        )

        dep_graph.replace_nodes(new_marks, new_mark_node)
        dep_graph.add_dependency(dep_verb_node, dep_verb2_node, "advcl:" + new_mark_node.LEMMA)
        dep_graph.add_dependency(dep_verb2_node, new_mark_node, "mark")


def multi_word_fix_flat(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    fixed_rels = {"fixed", "flat", "compound"}

    phrases = []

    for node in dep_graph.nodes():

        parents = [n for n, l in dep_graph.parents(node,
                                                   filter=lambda n, l: any(x in l for x in fixed_rels))]

        if parents:
            continue

        phrase = []
        for n, l in dep_graph.children(node,
                                       filter=lambda n, l: any(x in l for x in fixed_rels)):
            phrase.extend(dep_graph.offsprings(n))

        if not phrase:
            continue

        phrase.append(node)

        if len(phrase) > 1:
            phrase.sort(key=lambda n: n.LOC)
            # min_loc = phrase[0].LOC
            # max_loc = phrase[-1].LOC
            # phrase = [n for n in dep_graph.nodes() if min_loc <= n.LOC <= max_loc]
            phrases.append((phrase, node))

    phrases.sort(key=lambda x: len(x[0]), reverse=True)

    for phrase, head in phrases:

        if not all([dep_graph.get_node(x.ID) for x in phrase]):
            continue  # already been processed

        merging_nodes = set()
        min_loc = 10000
        max_loc = -1
        for child in phrase:
            if isinstance(child, DependencyGraphNode):
                min_loc = min(min_loc, child.LOC)
                max_loc = max(min_loc, child.LOC)
            elif isinstance(child, DependencyGraphSuperNode):
                min_loc = min(min_loc, min([x.LOC for x in child.nodes]))
                max_loc = max(max_loc, max([x.LOC for x in child.nodes]))
            merging_nodes.update(dep_graph.offsprings(child))

        merged_nodes = set([n for n in merging_nodes if min_loc <= n.LOC <= max_loc])
        for node in merging_nodes:
            if node.LOC == min_loc - 1 and node.LEMMA in {"\"", "\'"}:
                merged_nodes.add(node)
            if node.LOC == max_loc + 1 and node.LEMMA in {"\"", "\'"}:
                merged_nodes.add(node)
        merged_nodes = list(merged_nodes)
        merged_nodes.sort(key=lambda x: x.LOC)

        logger.debug("multi_word_fix_flat: we are merging ")
        logger.debug("\n".join(str(node) for node in merged_nodes))
        logger.debug("with head \n" + str(head))
        new_node = merge_dep_nodes(merged_nodes, UPOS=head.UPOS, LOC=head.LOC)

        dep_graph.replace_nodes(merged_nodes, new_node)


def and_or(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    parent_node = pattern.create_node()
    some_node = pattern.create_node()
    and_node = pattern.create_node(LEMMA=r"\band\b")
    or_node = pattern.create_node(LEMMA=r"\bor\b")

    pattern.add_dependency(parent_node, some_node, r'\bconj:\w*')
    pattern.add_dependency(some_node, and_node, r'\bcc\b')
    pattern.add_dependency(some_node, or_node, r'\bcc\b')
    pattern.add_dependency(and_node, or_node, r'\bconj')

    for match in list(dep_graph.match(pattern)):

        dep_parent_node = match[parent_node]
        dep_some_node = match[some_node]
        dep_and_node = match[and_node]
        dep_or_node = match[or_node]

        rel = dep_graph.get_dependency(dep_parent_node, dep_some_node)

        if not rel.startswith("conj:and") and not rel.startswith("conj:or"):
            continue

        and_or_nodes = [n for n in dep_graph.nodes() if dep_and_node.LOC < n.LOC < dep_or_node.LOC]

        if any([node.UPOS in {"VERB", "NOUN", "ADJ", "ADP", "ADV"} for node in and_or_nodes]):
            continue

        and_or_nodes.append(dep_and_node)
        and_or_nodes.append(dep_or_node)
        and_or_nodes.sort(key=lambda n: n.LOC)

        if not all([dep_graph.get_node(x.ID) for x in and_or_nodes]):
            continue

        new_and_or_node = merge_dep_nodes(and_or_nodes,
                                          UPOS=dep_and_node.UPOS,
                                          LOC=dep_and_node.LOC,
                                          FEATS=dep_and_node.FEATS
                                          )

        dep_graph.replace_nodes(and_or_nodes, new_and_or_node)
        dep_graph.set_dependency(dep_parent_node, dep_some_node, "conj:" + new_and_or_node.FORM)


def goeswith(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    goeswith_phrases = []
    for n in dep_graph.nodes():

        goeswith_nodes = [n for n, l in dep_graph.children(n,
                                                           filter=lambda n, l: "goeswith" in l)]

        if not goeswith_nodes:
            continue

        goeswith_nodes.append(n)
        goeswith_nodes.sort(key=lambda n: n.LOC)

        goeswith_phrases.append(goeswith_nodes)

    for goeswith_nodes in goeswith_phrases:

        upos = "X"
        for node in goeswith_nodes:
            if node.UPOS != "X":
                upos = node.UPOS

        new_node = merge_dep_nodes(goeswith_nodes,
                                   UPOS=upos,
                                   LOC=goeswith_nodes[-1].LOC
                                   )

        dep_graph.replace_nodes(goeswith_nodes, new_node)


def part(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """

    pattern = DependencyGraph()

    parent_node = pattern.create_node(UPOS="AUX|VERB")
    part_node = pattern.create_node(UPOS="PART")

    pattern.add_dependency(parent_node, part_node, r'advmod')

    for match in list(dep_graph.match(pattern)):
        dep_parent_node = match[parent_node]
        dep_part_node = match[part_node]

        new_node_list = [dep_parent_node, dep_part_node]
        new_node_list.sort(key=lambda n: n.LOC)

        new_node = merge_dep_nodes(new_node_list,
                                   UPOS=dep_parent_node.UPOS,
                                   LOC=dep_parent_node.LOC,
                                   FEATS=dep_parent_node.FEATS
                                   )

        dep_graph.replace_nodes(new_node_list, new_node)


def aux_not(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """

    aux_not = []
    for node in dep_graph.nodes(filter=lambda n: n.UPOS == "AUX"):

        next_node = dep_graph.get_node_by_loc(node.LOC + 1)

        if not next_node:
            continue

        if next_node.UPOS == "PART" and next_node.FORM == "n't":
            aux_not.append((node, next_node))

    for aux_node, not_node in aux_not:
        new_node = merge_dep_nodes([aux_node, not_node], UPOS=aux_node.UPOS, LOC=aux_node.LOC)

        dep_graph.replace_nodes([aux_node, not_node], new_node)

# # seems contained in multi-word-case
# def case_case(dep_graph: DependencyGraph):
#     """
#     according to
#     :param sentence:
#     :return:
#     """
#
#     pattern = DependencyGraph()
#
#     head_node = DependencyGraphNode()
#     case1_node = DependencyGraphNode()
#     case2_node = DependencyGraphNode()
#
#     pattern.add_nodes([head_node, case1_node, case2_node])
#
#     pattern.add_dependency(head_node, case1_node, r'case')
#     pattern.add_dependency(case1_node, case2_node, r'case')
#
#     for match in dep_graph.match(pattern):
#         dep_case1_node = match[case1_node]
#         dep_case2_node = match[case2_node]
#
#         oia_graph.add_word((dep_case1_node.ID, dep_case2_node.ID), dep_case1_node.ID)
