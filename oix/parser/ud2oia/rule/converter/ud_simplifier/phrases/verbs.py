"""
verb phrases
"""

from oix.parser.ud2oia.rule.converter.utils import continuous_component, merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphSuperNode


def verb_phrase(dep_graph: DependencyGraph):
    """
    ##### Merging aux and cop with their head VERB #####
    Cases:

    :param sentence:
    :return:
    """
    verb_phrases = []

    for node in dep_graph.nodes(filter=lambda x: x.UPOS in {"VERB", "AUX"}):

        if node.UPOS == "AUX":
            parent = [n for n, l in dep_graph.parents(node,
                                                      filter=lambda n, l: l == "aux")]
            if len(parent) > 0:
                continue

        #        if "VerbForm" in node.FEATS and "Ger" in node.FEATS["VerbForm"]:
        #            continue

        if "Tense" in node.FEATS and "Past" in node.FEATS["Tense"]:
            # if the verb is before the noun, it will be processed by noun_phrase and taken as a part of the noun
            parent = [n for n, l in dep_graph.parents(node,
                                                      filter=lambda n, l: l == "amod" and node.LOC < n.LOC)]
            if len(parent) > 0:
                continue
        # logger.debug("We are checking node {0}".format(node))

        root = node
        verbs = [root]
        for n, l in dep_graph.children(root):
            if dep_graph.get_dependency(n, root):
                continue

            if n.LEMMA in {"so", "also", "why"}:
                continue

            if "advmod" in l:
                offsprings = list(dep_graph.offsprings(n))
                if any(x.UPOS in {"VERB", "NOUN", "AUX", "PRON"} for x in offsprings):
                    continue

                verbs.extend(offsprings)
            elif "compound" in l:
                verbs.append(n)

        verbs = [x for x in verbs
                 if x.LOC <= root.LOC or "compound" in dep_graph.get_dependency(root, x)]

        # logger.debug("Verb: before continuous component ")
        # logger.debug("\n".join(str(verb) for verb in verbs))

        verbs = continuous_component(verbs, root)

        # add aux
        verbs.extend(n for n, l in dep_graph.children(root) if "aux" in l)

        # logger.debug("Verb: after continuous component ")
        # for verb in verbs:
        #    logger.debug(verb)

        verbs.sort(key=lambda x: x.LOC)
        last_loc = verbs[-1].LOC

        #        next_node = dep_graph.get_node_by_loc(last_loc + 1)
        #        if next_node and next_node.LEMMA == "not":
        #            verbs.append(next_node)

        if len(verbs) > 1:
            verb_phrases.append((verbs, root))

    for verbs, root in verb_phrases:
        verb_node = merge_dep_nodes(verbs, UPOS="VERB", LOC=root.LOC, FEATS=root.FEATS)

        dep_graph.replace_nodes(verbs, verb_node)


def to_verb(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """
    to_verb_phrase = []
    for root in dep_graph.nodes(filter=lambda x: x.UPOS in {"VERB"}):
        if any("to" in rels.values() for parent, rels in dep_graph.parents(root)):
            continue

        for child, rels in dep_graph.children(root):
            if "mark" in rels and child.LEMMA == "to" and child.LOC == root.LOC - 1 and \
                    not (isinstance(child, DependencyGraphSuperNode) and child.is_conj):
                to_verb_phrase.append((child, root))

    for to, verb in to_verb_phrase:
        noun_node = merge_dep_nodes([to, verb],
                                    UPOS=verb.UPOS,
                                    LOC=verb.LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.replace_nodes([to, verb], noun_node)


def reverse_passive_verb(dep_graph: DependencyGraph):
    """
    I'd forgotten how blown away I was by some of the songs the first time I saw it in NY.
    :param dep_graph:
    :return:
    """
    pattern = DependencyGraph()

    subj_node = pattern.create_node()
    verb_node = pattern.create_node(UPOS="VERB", FEATS={"Tense": "Past"})
    be_node = pattern.create_node(LEMMA=r"\bbe\b")

    pattern.add_dependency(verb_node, subj_node, r"\w*subj")
    pattern.add_dependency(verb_node, be_node, "cop")

    for match in list(dep_graph.match(pattern)):

        dep_subj_node = match[subj_node]
        dep_verb_node = match[verb_node]
        dep_be_node = match[be_node]

        if not (dep_verb_node.LOC < dep_subj_node.LOC < dep_be_node.LOC):
            continue

        new_verb_phrase = [dep_be_node, dep_verb_node]
        dep_new_verb = merge_dep_nodes(new_verb_phrase, UPOS="VERB", LOC=dep_be_node.LOC)
        dep_graph.replace_nodes(new_verb_phrase, dep_new_verb)


def xcomp_verb(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :return:
    """

    pattern = DependencyGraph()

    pred_node = pattern.create_node()
    xcomp_verb_node = pattern.create_node(UPOS="VERB|AUX")
    xcomp_mark_node = pattern.create_node(UPOS="PART")

    pattern.add_dependency(pred_node, xcomp_verb_node, "xcomp")
    pattern.add_dependency(xcomp_verb_node, xcomp_mark_node, "mark")

    for match in list(dep_graph.match(pattern)):

        dep_pred_node = match[pred_node]
        dep_xcomp_verb_node = match[xcomp_verb_node]
        dep_xcomp_mark_node = match[xcomp_mark_node]

        if dep_xcomp_mark_node.LEMMA != "to":
            # print('--------------------------LEMMA:      ',dep_xcomp_mark_node.LEMMA)
            # raise Exception("Unexpected Situation: xcomp mark != to let's throw out to see what happens")
            continue

        if dep_xcomp_mark_node.LOC > dep_xcomp_verb_node.LOC:
            raise Exception("Unexpected Situation: xcomp mark after the xcomp verb")

        pred_nodes = list(dep_graph.parents(dep_xcomp_verb_node, filter=lambda n, l: "xcomp" in l))

        if len(pred_nodes) > 1:
            raise Exception("Unexpected Situation: Multiple xcomp parents found")

        new_verb_phrase = [dep_xcomp_mark_node, dep_xcomp_verb_node]
        dep_new_verb = merge_dep_nodes(new_verb_phrase, UPOS="VERB", LOC=dep_xcomp_verb_node.LOC)
        dep_graph.replace_nodes(new_verb_phrase, dep_new_verb)


def ccomp_mark_sconj(dep_graph: DependencyGraph):
    """
    See them as they are
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()
    pred1_node = pattern.create_node(UPOS="VERB")
    pred2_node = pattern.create_node()
    sconj_node = pattern.create_node(UPOS="SCONJ")

    pattern.add_dependency(pred1_node, pred2_node, r'ccomp')
    pattern.add_dependency(pred2_node, sconj_node, 'mark')

    for match in list(dep_graph.match(pattern)):

        dep_pred1_node = match[pred1_node]
        dep_pred2_node = match[pred2_node]
        dep_sconj_node = match[sconj_node]

        if dep_sconj_node.LEMMA == "as":
            dep_graph.remove_dependency(dep_pred2_node, dep_sconj_node)
            new_verb = [dep_pred1_node, "{1}", dep_sconj_node, "{2}"]

            new_verb_node = merge_dep_nodes(new_verb,
                                            UPOS=dep_pred1_node.UPOS,
                                            LOC=dep_pred1_node.LOC
                                            )
            # print("Noun detected", noun_node.ID)
            dep_graph.replace_nodes(new_verb, new_verb_node)
