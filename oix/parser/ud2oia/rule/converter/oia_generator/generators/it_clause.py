"""
be clause
"""
from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext


def it_be_adjv_that(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    ##### Expletive #####
    ##### it is xxx that #####
    #####  #####
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    it_node = pattern.create_node(LEMMA="it")
    be_node = pattern.create_node(UPOS="VERB")
    csubj_node = pattern.create_node(UPOS="ADJ|ADV")
    that_node = pattern.create_node(LEMMA="that")

    pattern.add_dependency(be_node, it_node, r'expl')
    pattern.add_dependency(be_node, csubj_node, r'csubj')
    pattern.add_dependency(csubj_node, that_node, r'mark')

    for match in dep_graph.match(pattern):
        dep_be_node, dep_it_node, dep_that_node, dep_csubj_node = \
            [match[x] for x in [be_node, it_node, that_node, csubj_node]]

        if context.is_processed(dep_be_node, dep_it_node):
            continue

        oia_it_node = oia_graph.add_words(dep_it_node.position)
        oia_csubj_node = oia_graph.add_words(dep_csubj_node.position)
        # oia_that_node = oia_graph.add_word_with_head(dep_that_node)
        oia_be_node = oia_graph.add_words(dep_be_node.position)

        oia_graph.add_argument(oia_be_node, oia_it_node, 1)

        oia_graph.add_ref(oia_csubj_node, oia_it_node)

        context.processed(dep_be_node, dep_it_node)


def it_verb_clause(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    ##### Expletive #####
    ##### it is xxx to do  #####
    #####  #####
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()

    it_node = pattern.create_node(LEMMA="it")
    verb_node = pattern.create_node(UPOS="VERB")
    subj_node = pattern.create_node(UPOS="NOUN|PRON|PROPN|VERB")

    pattern.add_dependency(verb_node, it_node, r'expl')
    pattern.add_dependency(verb_node, subj_node, r'nsubj|csubj')

    for match in dep_graph.match(pattern):

        dep_verb_node, dep_it_node, dep_subj_node = \
            [match[x] for x in [verb_node, it_node, subj_node]]

        if context.is_processed(dep_verb_node, dep_it_node):
            continue

        oia_it_node = oia_graph.add_words(dep_it_node.position)
        oia_subj_node = oia_graph.add_words(dep_subj_node.position)
        # oia_that_node = oia_graph.add_word_with_head(dep_that_node)
        oia_verb_node = oia_graph.add_words(dep_verb_node.position)

        if dep_it_node.LOC < dep_subj_node.LOC:
            # it VERB subj that ...

            oia_graph.add_argument(oia_verb_node, oia_it_node, 1)
            oia_graph.add_argument(oia_verb_node, oia_subj_node, 1)
            oia_graph.add_ref(oia_it_node, oia_subj_node)
        else:
            # subj VERB it that ...
            oia_graph.add_argument(oia_verb_node, oia_it_node, 2)
            oia_graph.add_argument(oia_verb_node, oia_subj_node, 2)
            oia_graph.add_ref(oia_it_node, oia_subj_node)

        # dep_graph.remove_dependency(dep_verb_node, dep_subj_node)

        context.processed(dep_verb_node, dep_it_node)
        context.processed(dep_verb_node, dep_subj_node)

        # oia_graph.add_ref(oia_subj_node, oia_it_node)
