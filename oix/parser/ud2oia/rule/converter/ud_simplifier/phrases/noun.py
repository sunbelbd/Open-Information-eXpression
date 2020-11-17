"""
noun phrases
"""
import itertools

from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.adjv import valid_adj_form
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes
from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphSuperNode

valid_np_children_dep = {
    "fixed",
    "compound",
    "nummod",
    "det",
    "flat",
    "amod",
    "nmod:poss",
    "nmod:tmod",
    "obl:npmod",
    "reparandum",
    "nmod:npmod",
    "case",
    "dep",
    "punct"}


def is_np_root(node, dep_graph):
    """

    :param relation:
    :return:
    """

    #    valid_np_parent = {"obj", "subj"}
    #    if any(x in relation for x in valid_np_parent):
    #        return False

    np_parent = {"flat",
                 "fixed",
                 "compound",
                 "det",
                 "dep",
                 # "conj",
                 "cc",
                 # "appos",
                 "reparandum",
                 "case",
                 "punct"}

    mod_rel = {"amod", "obl:npmod", "nmod:poss",
               "nmod:npmod", "nummod"}

    is_root = True

    for parent, rel in dep_graph.parents(node):

        if any(rel.startswith(x) for x in np_parent):
            is_root = False
            break

        if any(rel.startswith(x) for x in mod_rel) and parent.UPOS in {"NOUN", "PROPN", "X", "NUM", "SYM"}:
            # middle_node = [n for n in dep_graph.nodes() if node.LOC < n.LOC < parent.LOC or
            #               node.LOC > n.LOC > parent.LOC]

            is_root = False
            break

    return is_root


def is_valid_np_child(dep_graph, root, relation, child):
    """

    :param rel:
    :return:
    """

    if relation.startswith("det:predet") and child.LEMMA in {"such", "so"}:
        return False

    if "PronType" in child.FEATS and "Int" in child.FEATS["PronType"] and child.LEMMA == "whose":  # whose
        return False

    if relation.startswith("nmod:poss"):
        if any(n.LEMMA == 'whose' for n in dep_graph.nodes() if child.LOC < n.LOC < root.LOC):
            return False

    return any(relation.startswith(x) for x in valid_np_children_dep)


def noun_phrase(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    nouns = []
    # we first find np roots
    for root in dep_graph.nodes(filter=lambda x: x.UPOS in {"NOUN", "PROPN", "X", "NUM", "SYM"}):

        logger.debug("checking the node:")
        logger.debug(str(root))

        # np_elements = valid_np_element(root, dep_graph)
        parent_rels = set(itertools.chain.from_iterable(l.values() for n, l in dep_graph.parents(root)))
        parent_rels = set(rel.replace("_", " ") for rel in parent_rels)

        escaped_case_node = set()
        if parent_rels:
            case_nodes = [x for x, l in dep_graph.children(root, filter=lambda n, l: l == "case")]
            for node in case_nodes:
                if node.LEMMA.lower() in parent_rels or node.FORM.lower() in parent_rels:
                    # lemma is for including
                    escaped_case_node.add(node)

        valid_np_children = [(n, l) for n, l in dep_graph.children(root,
                                                                   filter=lambda n, l: is_valid_np_child(dep_graph,
                                                                                                         root, l, n))]
        logger.debug("noun_phrase: valid_np_children:")
        for node, l in valid_np_children:
            logger.debug(str(node))

        np_elements = [root]

        for n, l in valid_np_children:
            if n.UPOS == "ADP":
                continue
            if n.LOC > root.LOC and \
                    not any(l.startswith(x)
                            for x in {"fixed", "compound", "nummod",
                                      "nmod:tmod", "flat", "nmod:npmod", "dep"}):
                continue
            if n in escaped_case_node:
                continue

            if isinstance(n, DependencyGraphSuperNode) and n.is_conj:
                continue

            offsprings = list(dep_graph.offsprings(n))
            valid_np_component = True

            for x in offsprings:
                for parent, rels in dep_graph.parents(x):
                    if any(x in rels for x in {"acl", "obl", "advcl", "subj", "obj"}):
                        valid_np_component = False
                        break
                if not valid_np_component:
                    break
            if valid_np_component:
                np_elements.extend(offsprings)

        logger.debug("noun_phrase: candidate np_elements:")
        for node in np_elements:
            logger.debug(str(node))

        det = [n for n, l in dep_graph.children(root, filter=lambda n, l: l == "det")]
        det = [x for x in det if x.LOC <= root.LOC]
        det.sort(key=lambda x: x.LOC)

        if det:
            # raise Exception("noun phrase without det ")

            det = det[-1]
            # check the element should be continuous
            np_elements = [x for x in np_elements if det.LOC <= x.LOC]
            logger.debug("noun_phrase: det found, cut the nodes before the det")

        filtered_np_elements = sorted(list(np_elements), key=lambda x: x.LOC)
        # if np_elements[-1].LOC - np_elements[0].LOC != len(np_elements) - 1:
        #     print ("root", root)
        #     for n in np_elements:
        #         print("np element", n.LOC, n)
        #     raise Exception("Bad Business Logic")
        changed = True
        while changed:
            changed = False
            if filtered_np_elements and filtered_np_elements[0].LEMMA in {"-", "--"}:
                filtered_np_elements.pop(0)
                changed = True
            if filtered_np_elements and filtered_np_elements[0].UPOS in {"ADP", "CCONJ", "PUNCT"}:
                filtered_np_elements.pop(0)
                changed = True

        if filtered_np_elements:
            nouns.append((set(filtered_np_elements), root))

    sub_nouns = []
    for idx1, (phrase1, head1) in enumerate(nouns):
        for idx2, (phrase2, head2) in enumerate(nouns):
            if idx1 == idx2:
                continue

            phrasex, phrasey = (phrase1, phrase2) if len(phrase1) > len(phrase2) else (phrase2, phrase1)
            common = phrasex.intersection(phrasey)

            if not common:
                continue
            elif len(common) == len(phrasey):
                # node2 is a sub np of node1, delete
                sub_nouns.append(phrasey)
            else:
                print("Phrase 1", [x.ID for x in phrase1])
                print("Phrase 2", [x.ID for x in phrase2])
                # return
                raise Exception("duplicate words found")

    for idx, (phrase, head) in enumerate(nouns):

        if phrase in sub_nouns:
            continue

        phrase = sorted(list(phrase), key=lambda x: x.LOC)

        for node in phrase:
            for child, _ in dep_graph.children(node):
                if child.LOC == phrase[0].LOC - 1 and child.LEMMA in {"\"", "\'"}:
                    phrase.insert(0, child)
                if child.LOC == phrase[-1].LOC + 1 and child.LEMMA in {"\"", "\'"}:
                    phrase.append(child)

        noun_node = merge_dep_nodes(phrase,
                                    UPOS=head.UPOS,
                                    LOC=phrase[-1].LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.replace_nodes(phrase, noun_node)
        # oia_graph.add_word(noun_node.ID)


def noun_all(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """
    noun_all_phrase = []
    for root in dep_graph.nodes(filter=lambda x: x.UPOS in {"NOUN", "PROPN", "PRON", "X", "NUM", "SYM"}):
        for child, rels in dep_graph.children(root):
            if "det" in rels and child.LEMMA == "all" and child.LOC == root.LOC + 1:
                noun_all_phrase.append((root, child))

    for noun, all in noun_all_phrase:
        noun_node = merge_dep_nodes([noun, all],
                                    UPOS=noun.UPOS,
                                    LOC=noun.LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.replace_nodes([noun, all], noun_node)


def whose_noun(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """

    pattern = DependencyGraph()
    noun_node = pattern.create_node(UPOS="NOUN|PROPN|PRON|X|NUM|SYM")
    owner_node = pattern.create_node()
    whose_node = pattern.create_node(LEMMA="whose")

    pattern.add_dependency(noun_node, owner_node, "nmod:poss")
    pattern.add_dependency(owner_node, whose_node, "ref")

    whose_noun_phrase = []
    for match in dep_graph.match(pattern):
        dep_owner_node = match[owner_node]
        dep_noun_node = match[noun_node]
        dep_whose_node = match[whose_node]

        whose_noun_phrase.append((dep_owner_node, dep_whose_node, dep_noun_node))

    for owner, whose, noun in whose_noun_phrase:
        noun_node = merge_dep_nodes([whose, noun],
                                    UPOS=noun.UPOS,
                                    LOC=noun.LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.remove_dependency(owner_node, whose)
        dep_graph.remove_dependency(noun, owner_node, "nmod:poss")
        dep_graph.replace_nodes([whose, noun], noun_node)


#
# def noun_phrase_with_of(dep_graph, oia_graph):
#     """
#     the CEO of Baidu
#     a couple of weeks
#     a lot of something
#     a large amount of something
#     :param dep_graph:
#     :param oia_graph:
#     :return:
#     """
#
#     pattern = DependencyGraph()
#
#     parent_node = DependencyGraphNode(UPOS="NOUN")
#     child_node = DependencyGraphNode(UPOS="NOUN")
#     case_node = DependencyGraphNode(FORM=r'\bof\b')
#
#     pattern.add_nodes([parent_node, child_node, case_node])
#
#     pattern.add_dependency(parent_node, child_node, r'nmod:of')
#     pattern.add_dependency(child_node, case_node, r'case')
#
#     for match in dep_graph.match(pattern):
#
#         dep_parent_node = match[parent_node]
#         dep_child_node = match[child_node]
#         dep_case_node = match[case_node]
#
#         rel = dep_graph.get_dependency(dep_parent_node, dep_child_node)
#
#         if rel != "nmod:" + dep_case_node.FORM:
#             continue
#
#         if oia_graph.has_relation(dep_parent_node.ID, dep_child_node.ID):
#             continue
#
#         if oia_graph.has_word(dep_case_node.ID):
#             # print("CASE", dep_case_node.ID, type(dep_case_node.ID))
#             # print("PARENT", dep_parent_node.ID, type(dep_case_node.ID))
#             # print("CHILD", dep_child_node.ID, type(dep_case_node.ID))
#             # dep_graph.visualize("error_dep.png")
#             # oia_graph.visualize(dep_graph, "error_oia.png")
#             # raise Exception("The case has already been added")
#             continue
#
#         oia_parent_node = oia_graph.find_node_by_head(dep_parent_node.ID)
#         oia_child_node = oia_graph.find_node_by_head(dep_child_node.ID)
#
#         assert oia_parent_node and oia_child_node
#
#         oia_graph.remove_node(oia_parent_node)
#         oia_graph.remove_node(oia_child_node)
#
#         new_noun = list(oia_parent_node.ID) + [dep_case_node.ID] + list(oia_child_node.ID)
#         head = oia_parent_node.head
#
#         oia_graph.add_word(new_noun, head)
#         #
#         # pred_node = oia_graph.add_word(dep_case_node.ID)
#         # arg1_node = oia_graph.add_word_with_head(dep_parent_node.LOC)
#         # arg2_node = oia_graph.add_word_with_head(dep_child_node.LOC)
#         #
#         # oia_graph.add_argument(pred_node, arg1_node, 1)
#         # oia_graph.add_argument(pred_node, arg2_node, 2)


def find_new_nodes(old_node, dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    for node in dep_graph.nodes():
        if old_node.ID in node.ID:
            return node
    return None


def noun_of_noun(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """
    pattern = DependencyGraph()
    noun1_node = pattern.create_node(UPOS="NOUN|PROPN|PRON|X|NUM|SYM")
    of_node = pattern.create_node(LEMMA="of")
    noun2_node = pattern.create_node(UPOS="NOUN|PROPN|PRON|X|NUM|SYM")

    pattern.add_dependency(noun1_node, noun2_node, "nmod:of")
    pattern.add_dependency(noun2_node, of_node, "case")

    merged_map = dict()

    #    need_merge = []
    for match in list(dep_graph.match(pattern)):

        dep_noun1_node = match[noun1_node]
        if dep_noun1_node in merged_map:
            dep_noun1_node = merged_map[dep_noun1_node]

        dep_noun2_node = match[noun2_node]
        if dep_noun2_node in merged_map:
            dep_noun2_node = merged_map[dep_noun2_node]

        dep_of_node = match[of_node]

        if not all([dep_noun1_node, dep_noun2_node, dep_of_node]):
            # processed by others
            continue

        involved_in_complex_structure = False
        for child, rel in dep_graph.children(dep_noun2_node):
            if "conj" in rel or "acl" in rel:
                involved_in_complex_structure = True

        for parent, rel in dep_graph.parents(dep_noun2_node):
            if "conj" in rel or "acl" in rel:
                involved_in_complex_structure = True

        if involved_in_complex_structure:
            continue

        if isinstance(dep_noun1_node, DependencyGraphSuperNode) and dep_noun1_node.is_conj:
            continue

        if isinstance(dep_noun2_node, DependencyGraphSuperNode) and dep_noun2_node.is_conj:
            continue

        dep_noun2_parents = [parent for parent, rel in dep_graph.parents(dep_noun2_node)]
        if len(dep_noun2_parents) == 1:
            if dep_noun2_parents[0] != dep_noun1_node:
                logger.error("dep_noun1 {0} {1}".format(dep_noun1_node.ID, dep_noun1_node.FORM))
                logger.error("dep_noun2 {0} {1}".format(dep_noun2_node.ID, dep_noun2_node.FORM))
                logger.error("dep_noun2_parent {0} {1}".format(dep_noun2_parents[0].ID, dep_noun2_parents[0].FORM))
                raise Exception("Noun of Noun failed")

            new_noun_nodes = [dep_noun1_node, dep_of_node, dep_noun2_node]
            # <<<<<<< HEAD

            new_noun = merge_dep_nodes(new_noun_nodes,
                                       UPOS=dep_noun1_node.UPOS,
                                       FEATS=dep_noun1_node.FEATS,
                                       LOC=dep_noun1_node.LOC)

            dep_graph.replace_nodes(new_noun_nodes, new_noun)
            for node in new_noun_nodes:
                merged_map[node] = new_noun

            logger.debug("node merged :" + " ".join([dep_noun1_node.ID, dep_of_node.ID, dep_noun2_node.ID]))


# =======
#            need_merge.append(new_noun_nodes)

#     for new_noun_nodes in need_merge:
#         dep_noun1_node, dep_of_node, dep_noun2_node = new_noun_nodes
#         dep_noun1_node = find_new_nodes(dep_noun1_node, dep_graph)
#         dep_of_node = find_new_nodes(dep_of_node, dep_graph)
#         dep_noun2_node = find_new_nodes(dep_noun2_node, dep_graph)
#         assert dep_noun1_node is not None
#         assert dep_of_node is not None
#         assert dep_noun2_node is not None
#         new_noun_nodes = [dep_noun1_node, dep_of_node, dep_noun2_node]
#         new_noun = merge_dep_nodes(new_noun_nodes,
#                                     UPOS=dep_noun1_node.UPOS,
#                                     FEATS=dep_noun1_node.FEATS,
#                                     LOC=dep_noun1_node.LOC)
#
#         dep_graph.replace_nodes(new_noun_nodes, new_noun)
# >>>>>>> 60cbb0e7ddd6adc89ca0a7b5799ad70c1da97800


def det_of_noun(dep_graph: DependencyGraph):
    """
    any/some/all of noun
    :param dep_graph:
    :return:
    """
    pattern = DependencyGraph()
    det_node = pattern.create_node(UPOS="DET")
    of_node = pattern.create_node(LEMMA="of")
    noun2_node = pattern.create_node(UPOS="NOUN|PROPN|PRON|X|NUM|SYM")

    pattern.add_dependency(det_node, noun2_node, "nmod:of")
    pattern.add_dependency(noun2_node, of_node, "case")

    for match in list(dep_graph.match(pattern)):

        dep_det_node = match[det_node]
        dep_noun2_node = match[noun2_node]
        dep_of_node = match[of_node]

        if not all([dep_det_node, dep_noun2_node, dep_of_node]):
            # processed by others
            continue

        if isinstance(dep_noun2_node, DependencyGraphSuperNode) and dep_noun2_node.is_conj:
            continue

        dep_noun2_parents = [parent for parent, rel in dep_graph.parents(dep_noun2_node)]
        if len(dep_noun2_parents) == 1:
            assert dep_noun2_parents[0] == dep_det_node

            new_noun_nodes = [dep_det_node, dep_of_node, dep_noun2_node]

            new_noun = merge_dep_nodes(new_noun_nodes,
                                       UPOS=dep_det_node.UPOS,
                                       FEATS=dep_det_node.FEATS,
                                       LOC=dep_det_node.LOC)

            dep_graph.replace_nodes(new_noun_nodes, new_noun)


def det_adjv_phrase(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    phrases = []

    for node in dep_graph.nodes(filter=lambda n: n.UPOS in {"ADJ", "ADV"}):

        parent_rels = itertools.chain.from_iterable((rel for parent, rel in dep_graph.parents(node)))
        if any([rel in valid_adj_form for rel in parent_rels]):
            continue

        if any([rel in {"amod", "advmod"} for rel in parent_rels]):
            continue

        det = [n for n, l in dep_graph.children(node, filter=lambda n, l: l == "det")]

        if not det:
            continue

        det.sort(key=lambda x: x.LOC)

        det = det[-1]

        if det.LEMMA not in {"the", "a", "an", "some", "any", "all"}:
            continue

        root = node
        np_elements = list(dep_graph.offsprings(root, filter=lambda n: det.LOC <= n.LOC <= root.LOC))

        # check the element should be continuous

        np_elements = sorted(list(np_elements), key=lambda x: x.LOC)
        # if np_elements[-1].LOC - np_elements[0].LOC != len(np_elements) - 1:
        #     print ("root", root)
        #     for n in np_elements:
        #         print("np element", n.LOC, n)
        #     raise Exception("Bad Business Logic")

        phrases.append((np_elements, root))

    for np, root in phrases:
        noun_node = merge_dep_nodes(np,
                                    UPOS="NOUN",
                                    LOC=root.LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.replace_nodes(np, noun_node)
