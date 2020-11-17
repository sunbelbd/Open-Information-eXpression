"""
conjunction
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes
from loguru import logger
from more_itertools import pairwise
from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode, DependencyGraphSuperNode
from oix.oia.standard import NOUN_UPOS


def build_conjunction_node(dep_graph: DependencyGraph, root, root_parents, parallel_components):
    """

    :param dep_graph:
    :param parallel_components:
    :return:
    """
    parallel_components.sort(key=lambda x: x.LOC)

    conj_phrases = []

    for n1, n2 in pairwise(parallel_components):

        node1 = n1
        node2 = n2


        cur_conjs = []
        for n, l in sorted(list(dep_graph.children(node2)), key=lambda x: x[0].LOC):

            if not node1.LOC < n.LOC < node2.LOC:
                continue

            if ("case" in l or "mark" in l or "cc" in l) and \
                    (any(x in n.LEMMA for x in {"and", "or", "but", "not", "as well as"}) or n.UPOS == "CCONJ"):
                cur_conjs.append(n)

            if "punct" in l:
                cur_conjs.append(n)

            if ("advmod" in l) and any(x in n.LEMMA for x in {"so", "also"}):
                if len(list(dep_graph.children(n))) == 0:
                    cur_conjs.append(n)

        if not cur_conjs:
            conj_phrases.append(["AND"])
        else:
            conj_phrases.append(cur_conjs)



    if len(conj_phrases) == 1:
        unified_conj_phrase = conj_phrases[0]
        with_arg_palceholder = False
    else:
        with_arg_palceholder = True
        unified_conj_phrase = ["{1}"]
        for index, phrase in enumerate(conj_phrases):
            unified_conj_phrase.extend(phrase)
            unified_conj_phrase.append("{{{0}}}".format(index + 2))

    for n, l in sorted(list(dep_graph.children(parallel_components[0])),
                       key=lambda x: x[0].LOC,
                       reverse=True):
        if l == "cc:preconj":
            unified_conj_phrase.insert(0, n)
            dep_graph.remove_node(n)


    # uposes = set([p.UPOS for p in root_parents])
    # uposes.add(root.UPOS)

    conj_node = merge_dep_nodes(unified_conj_phrase,
                                is_conj=True,
                                UPOS=root.UPOS,
                                FEATS=root.FEATS,
                                LOC=root.LOC,
                                )

    for conj_phrase in conj_phrases:
        for n in conj_phrase:
            if isinstance(n, DependencyGraphNode):
                dep_graph.remove_node(n)

    dep_graph.add_node(conj_node)

    return conj_node, with_arg_palceholder


#
# # check whether the components are in same role
# upos_groups = [{"NOUN", "PROPN", "NUM", "PRON", "X", "PART", "DET", "SYM"}, {"VERB", "AUX", "PART", "INTJ"},
#                {"ADJ", "ADV", "PART", "SCONJ"}, {"ADP"}, {"CCONJ"}]
#
# upos_id_map = defaultdict(set)
# for idx, upos_group in enumerate(upos_groups):
#     for upos in upos_group:
#         upos_id_map[upos].add(idx)
#
#
# def is_compatible(parallel_components):
#     """
#
#     :param dep_graph:
#     :param parallel_components:
#     :return:
#     """
#
#     upos_group_id_map = [[] for _ in range(len(upos_groups))]
#
#     for child in parallel_components:
#         if child.UPOS not in upos_id_map:
#             raise Exception("Unknown upos in conjunction " + child.UPOS)
#
#         for idx in upos_id_map[child.UPOS]:
#             upos_group_id_map[idx].append(child)
#
#     compatible = False
#     for compatible_group in upos_group_id_map:
#
#         if len(compatible_group) == len(parallel_components):
#             compatible = True
#
#     return compatible


def get_relation_to_conj(dep_graph: DependencyGraph, root, root_parents, parallel_components):
    """

    :param dep_graph:
    :param parallel_components:
    :return:
    """

    relation_to_conj = dict()
    for parent in root_parents:
        prefixs = []
        marks = []
        shared_prefix = True
        for child in parallel_components:
            rels = dep_graph.get_dependency(parent, child)
            if rels:
                rel = list(rels.rels)[0]

                if child != root and rel.startswith("conj"):
                    continue
                if ":" in rel:
                    prefix, mark = rel.split(":")
                    if mark in {"relcl", "xsubj", "pass", "poss", "tmod"}:
                        prefix = rel
                        mark = None
                else:
                    prefix = rel
                    mark = None
                prefixs.append(prefix)
                marks.append(mark)
            else:
                shared_prefix = False
                marks.append(None)
        # ic(str(parent))

        # ic(list(map(str, parallel_components)))
        assert (len(set(prefixs))) == 1
        prefix = prefixs[0]
        if all([m is None for m in marks]):
            marks = None

        if any(x in prefix for x in {"subj", "obj", "ccomp", "xcomp"}):
            marks = None

        relation_to_conj[parent.ID] = (prefix, shared_prefix, marks)

    return relation_to_conj


#
#
# def merge_marks(dep_graph, parallel_components):
#     """
#
#     :param parallel_components:
#     :return:
#     """
#
#     same_mark_map = defaultdict(set)  # say that xxx, and that xxxx
#     for parent, _ in parallel_components:
#         for child, rels in dep_graph.children(parent):
#             if rels == "mark" or rels == "case":
#                 same_mark_map[child.LEMMA].add(child)
#
#     duplicated_marks = [marks for mark_lemma, marks in same_mark_map.items()
#                         if len(marks) == len(parallel_components)]
#
#     if not duplicated_marks:
#         return
#
#     assert len(duplicated_marks) == 1
#     duplicated_marks = duplicated_marks[0]
#
#     duplicated_marks = sorted(list(duplicated_marks), key=lambda x: x.LOC)
#     merged_mark = merge_dep_nodes(list(duplicated_marks),
#                                   FORM=duplicated_marks[0].FORM,
#                                   LEMMA=duplicated_marks[0].LEMMA,
#                                   UPOS=duplicated_marks[0].UPOS,
#                                   LOC=duplicated_marks[0].LOC)
#
#     dep_graph.replace_nodes(duplicated_marks, merged_mark)
#
#     return merged_mark
#

def find_mark(case_marks, node_range, required_mark):
    """

    :param case_marks:
    :param node_range:
    :return:
    """

    required_mark = required_mark.replace("_", " ")

    for node in reversed(node_range):
        for n, l in case_marks[node.ID]:
            if required_mark == n.LEMMA or required_mark in n.LEMMA.split(" "):
                rel = "mark" if "mark" in l else "case" if "case" in l else "cc" if "cc" in l else None
                if rel is None:
                    raise Exception("relation is not met")
                return n, rel


def complete_missing_case_mark(dep_graph: DependencyGraph, root, root_parents, parallel_components,
                               relation_to_conj, case_marks):
    """

    :param dep_graph:
    :param parallel_components:
    :return:
    """

    parallel_components.sort(key=lambda x: x.LOC)

    for parent in root_parents:
        # ic(str(root))
        # ic(str(parent))

        # ic(relation_to_conj)

        prefix, shared_prefix, required_mark = relation_to_conj[parent.ID]
        if not required_mark:
            continue

        for index, (node, mark) in enumerate(zip(parallel_components, required_mark)):

            if mark is None:
                continue

            is_exist = any(mark == child.LEMMA or mark in child.LEMMA.split(" ")
                           for child, l in dep_graph.children(node))
            if is_exist:
                continue

            found_mark = find_mark(case_marks, parallel_components[:index], mark)

            if found_mark:

                mark_node, rel = found_mark

                dup_case_mark = dep_graph.create_node(FORM=mark_node.FORM,
                                                      LEMMA=mark_node.LEMMA,
                                                      UPOS=mark_node.UPOS,
                                                      LOC=mark_node.LOC)
                dup_case_mark.aux = True
                dep_graph.add_dependency(node, dup_case_mark, rel)
            else:

                logger.warning("cannot find the mark, just add the relation")


def process_conjunction(dep_graph: DependencyGraph, root: DependencyGraphNode):
    """

    :param dep_graph:
    :param root:
    :return:
    """
    conj_childs = [child for child, rels in dep_graph.children(root,
                                                               filter=lambda n, l: l.startswith("conj"))]

    assert conj_childs

    parallel_components = [root]

    for child in conj_childs:

        is_nest = any(grand_rels.startswith("conj") for grand_sun, grand_rels in dep_graph.children(child))
        if is_nest:
            logger.debug("nested conj is found ")
            logger.debug(str(child))

            conj_node, parallel_nodes = process_conjunction(dep_graph, child)
            logger.debug("conj_node is created ")
            logger.debug(str(conj_node))

            for node in parallel_nodes:
                logger.debug("Containing nodes  ")
                logger.debug(str(node))
                rels = list(dep_graph.get_dependency(root, node))
                for rel in rels:
                    if rel.startswith("conj"):
                        logger.debug("remove dependency {0}".format((root.ID, node.ID, rel)))

                        dep_graph.remove_dependency(root, node, rel)
                        dep_graph.add_dependency(root, conj_node, rel)
            child = conj_node

        parallel_components.append(child)

    parallel_components.sort(key=lambda x: x.LOC)

    # if all(n.UPOS in NOUN_UPOS for n in parallel_components):
    #
    #     logger.debug("Processing all noun conjunction")
    #
    #     is_pure_noun = True
    #
    #     merging_noun_nodes = []
    #     min_loc = 10000
    #     max_loc = -1
    #     for child in parallel_components:
    #         if isinstance(child, DependencyGraphNode):
    #             min_loc = min(min_loc, child.LOC)
    #             max_loc = max(min_loc, child.LOC)
    #         elif isinstance(child, DependencyGraphSuperNode):
    #             min_loc = min(min_loc, min([x.LOC for x in child.nodes]))
    #             max_loc = max(max_loc, max([x.LOC for x in child.nodes]))
    #         merging_noun_nodes.extend(dep_graph.offsprings(child))
    #
    #         logger.debug("Checking acl for {0}".format(child))
    #         for n, l in dep_graph.children(child):
    #             logger.debug(n)
    #             logger.debug("label {0}".format(l))
    #             if "acl" in l:
    #                 is_pure_noun = False
    #                 break
    #
    #     if is_pure_noun:
    #         merging_noun_nodes = [n for n in merging_noun_nodes if min_loc <= n.LOC <= max_loc]
    #         is_pure_noun = not any(n.UPOS in {"ADP", "VERB", "SCONJ", "AUX"} for n in merging_noun_nodes)
    #
    #     if is_pure_noun:
    #         # merged_noun_nodes.sort(key=lambda x: x.LOC)
    #         for node in merging_noun_nodes:
    #             logger.debug("merging {0}".format(node))
    #
    #         new_noun = merge_dep_nodes(merging_noun_nodes, UPOS=root.UPOS, LOC=root.LOC)
    #         dep_graph.replace_nodes(merging_noun_nodes, new_noun)
    #
    #         return new_noun, []

    root_parents = list(set(parent for parent, rels in dep_graph.parents(root)))
    root_parents.sort(key=lambda x: x.LOC)

    # ic(list(map(str, root_parents)))

    conj_node, with_arg_palceholder = build_conjunction_node(dep_graph, root, root_parents, parallel_components)

    relation_to_conj = get_relation_to_conj(dep_graph, root, root_parents, parallel_components)

    case_marks = dict()
    for index, node in enumerate(parallel_components):
        case_marks[node.ID] = [(n, l) for n, l in dep_graph.children(node)
                               if ("case" in l or "mark" in l or "cc" in l)]
    for key, values in case_marks.items():
        for v in values:
            logger.debug("case_marker = {} {} {}".format(key, v[0].ID, v[1].rels))

    logger.debug("relation_to_conj = {}".format(relation_to_conj))

    for parent in root_parents:
        # ic(parent)

        prefix, shared_prefix, required_mark = relation_to_conj[parent.ID]
        if any(x in prefix for x in {"subj", "obj", "ccomp", "xcomp"}) \
                or not required_mark or len(set(required_mark)) == 1:

            for node in parallel_components:
                dep_graph.remove_dependency(parent, node)

            relation = prefix

            if required_mark and len(set(required_mark)) == 1:
                ## with same mark

                mark_lemma = list(set(required_mark))[0]

                relation += ":" + mark_lemma

                mark_node = find_mark(case_marks, parallel_components, mark_lemma)

                if mark_node:

                    mark_node, mark_rel = mark_node

                    dep_graph.remove_node(mark_node)
                    dep_graph.add_node(mark_node)  # clear the dependency

                    dep_graph.add_dependency(conj_node, mark_node, mark_rel)
                else:
                    logger.error("cannot find the mark node")

            dep_graph.add_dependency(parent, conj_node, relation)

        else:

            complete_missing_case_mark(dep_graph, root, root_parents, parallel_components,
                                       relation_to_conj, case_marks)

            if not required_mark:
                required_mark = [None] * len(parallel_components)

            for index, (node, mark) in enumerate(zip(parallel_components, required_mark)):
                if mark:
                    rel = prefix + ":" + mark
                else:
                    rel = prefix

                # if rel.startswith("conj"):
                #    continue
                logger.debug("add dependency {0}".format((parent.ID, node.ID, rel)))

                dep_graph.add_dependency(parent, node, rel)

        for idx, node in enumerate(parallel_components):
            if node != root:
                rels = dep_graph.get_dependency(root, node)
                for rel in rels:
                    if rel.startswith("conj"):
                        dep_graph.remove_dependency(root, node)

            if with_arg_palceholder:
                index = idx + 1
            else:
                # a, but b, b should be the arg1 and a be the arg2
                index = len(parallel_components) - idx

            dep_graph.add_dependency(conj_node, node, "arg_conj:{0}".format(index))

    return conj_node, parallel_components


def process_head_conj(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """
    first_word = dep_graph.get_node_by_loc(0)
    if first_word and first_word.LEMMA in {"and", "but"}:
        cc_parents = [n for n, l in dep_graph.parents(first_word) if l == "cc"]
        for p in cc_parents:
            dep_graph.remove_dependency(p, first_word)
            dep_graph.add_dependency(first_word, p, "arg_conj:1")


def conjunction(dep_graph: DependencyGraph):
    """

    #### Coordination ####
    #### I like apples, bananas and oranges. conj:and/or with punct
    #### @return a list of list of conjuncted entities
    TODO: currently cannot process nested conjunction. should process from bottom to up
    :param sentence:
    :return:
    """

    # find the root of conj and do the process

    root_of_conj = []

    for node in dep_graph.nodes():

        if any(rels.startswith("conj") for parent, rels in dep_graph.parents(node)):
            continue

        if any(rels.startswith("conj") for child, rels in dep_graph.children(node)):
            root_of_conj.append(node)

    for root in root_of_conj:
        logger.debug("found the root of conjunction")
        logger.debug(str(root))

        process_conjunction(dep_graph, root)

    process_head_conj(dep_graph)

#
# class Conjunction(UDSimplifierActor):
#     """
#     Conjunction
#     """
#
#     def triggered(self, dep_graph: DependencyGraph):
#         """
#
#         @param dep_graph:
#         @type dep_graph:
#         @return:
#         @rtype:
#         """
#
#         pattern = DependencyGraph()
#
#         conj_parent_node = pattern.add_node(DependencyGraphNode())
#         conj_root_node = pattern.add_node(DependencyGraphNode())
#         conj_parallel_node = pattern.add_node(DependencyGraphNode())
#
#         pattern.add_dependency(conj_parent_node, conj_root_node, r'^(?!conj).*')
#         pattern.add_dependency(conj_root_node, conj_parallel_node, r'conj\w*')
#
#         for match in dep_graph.match(pattern):

