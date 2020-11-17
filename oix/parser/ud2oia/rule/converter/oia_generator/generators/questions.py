"""
questions
"""

# from oix.oiagraph.graphs.oia_graph import OIAGraph, OIAWordsNode
from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphSuperNode, DependencyGraphNode
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext


def adv_question(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    question_node = pattern.create_node(UPOS="ADV|ADJ", LEMMA=r"(\bhow\b|\bwhat\b|\bwhere\b|\bwhen\b|why\b)\w*")
    verb_node = pattern.create_node(UPOS="VERB|AUX")
    # subj_node = pattern.create_node()

    pattern.add_dependency(verb_node, question_node, "advmod|amod")
    # pattern.add_dependency(verb_node, subj_node, r"\w*subj")

    for match in list(dep_graph.match(pattern)):

        dep_question_node, dep_verb_node = \
            [match[x] for x in (question_node, verb_node)]

        #        if not dep_question_node.LOC < dep_subj_node.LOC:
        #            # not a question
        #            continue

        oia_question_node = oia_graph.add_words(dep_question_node.position)
        oia_verb_node = oia_graph.add_words(dep_verb_node.position)

        oia_graph.remove_relation(oia_verb_node, oia_question_node)

        for parent, rel in list(oia_graph.parents(oia_verb_node)):

            if rel.mod:
                continue

            oia_graph.remove_relation(parent, oia_verb_node)
            oia_graph.add_relation(parent, oia_question_node, rel)

        oia_graph.add_function(oia_question_node, oia_verb_node)


def general_question(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for verb in dep_graph.nodes(filter=lambda n: n.UPOS == "VERB"):

        if any(any(x in n.LEMMA for x in {"what", "how", "why", "when", "where"}) for n in dep_graph.offsprings(verb)):
            continue

        parents = [n for n, _ in dep_graph.parents(verb)]

        # if not(len(parents) == 1 and parents[0].ID == "0"):
        #    continue
        # check subj and aux

        subj = None
        aux = None
        for child, rel in dep_graph.children(verb):
            if "subj" in rel:
                subj = child
            if "aux" in rel:
                aux = child

        is_be_verb = False

        if not isinstance(verb, DependencyGraphSuperNode):
            is_be_verb = verb.LEMMA == "be"
        else:
            assert isinstance(verb, DependencyGraphSuperNode)
            assert aux is None
            for n in verb.nodes:
                if isinstance(n, DependencyGraphNode):
                    if n.LEMMA == "be":
                        is_be_verb = True
                        # print('verb.nodes:', str(" ".join(str(xx.LEMMA) for xx in verb.nodes)))
                        # print('is_be_verb222:', is_be_verb)
                    if n.UPOS == "AUX":
                        aux = n
        # print('is_be_verb:', is_be_verb)
        if aux is None and not is_be_verb:
            # cannot be a general question
            continue

        expl_child = [n for n, l in dep_graph.children(verb) if l == "expl"]
        if expl_child:
            assert len(expl_child) == 1
            subj = expl_child[0]

        if subj is None:
            logger.warning("subject is none, cannot decide whether it is a question")
            continue
        #        print('subj.LOC:', subj.LOC)
        #        print('subj.LOC type:', type(subj.LOC))
        oia_verb_node = oia_graph.add_words(verb.position)

        is_there_be_verb = is_be_verb and ("there" in verb.LEMMA.split(' ') or "here" in verb.LEMMA.split(' '))

        is_question = False

        if is_there_be_verb:

            assert isinstance(verb, DependencyGraphSuperNode)
            be_node = [n for n in verb.nodes if n.LEMMA == "be"][0]
            there_node = [n for n in verb.nodes if n.LEMMA == "there" or n.LEMMA == "here"][0]
            # print('there_node:', there_node)
            if be_node.LOC < there_node.LOC:
                is_question = True

        elif (is_be_verb and verb.LOC < subj.LOC):

            is_question = True

        elif (aux is not None and aux.LOC < subj.LOC):

            is_question = True

        if is_question:
            # if aux is not None and aux.LEMMA == "do":
            #    oia_question_node = oia_graph.add_word_with_head(aux.LOC)
            # else:

            oia_question_node = oia_graph.add_aux("WHETHER")

            oia_graph.add_function(oia_question_node, oia_verb_node)
