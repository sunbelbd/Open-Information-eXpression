"""
oblique
"""
from oix.parser.ud2oia.rule.converter.utils import continuous_component

from oix.oia.graphs.dependency_graph import DependencyGraphNode, DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext


def oblique_with_prep(dep_graph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    # cut X by a knife
    pattern = DependencyGraph()
    verb_node = DependencyGraphNode(UPOS="VERB|ADJ|ADV|NOUN|X|PROPN|PRON")
    # adj is for "has more on "
    # adv is for "south of XXXX"
    prep_node = DependencyGraphNode(UPOS=r"PRON|ADP|VERB|SCONJ|ADJ")
    # verb is for including/according, adj is for "prior to"

    oblique_node = DependencyGraphNode()
    pattern.add_node(verb_node)
    pattern.add_node(prep_node)
    pattern.add_node(oblique_node)
    pattern.add_dependency(verb_node, oblique_node, r'\bobl')
    pattern.add_dependency(oblique_node, prep_node, r"case|mark")

    for match in dep_graph.match(pattern):

        dep_prep_node = match[prep_node]
        dep_verb_node = match[verb_node]
        dep_oblique_node = match[oblique_node]

        if oia_graph.has_relation(dep_verb_node, dep_oblique_node):
            continue

        oblique_edge = dep_graph.get_dependency(dep_verb_node, dep_oblique_node)
        oblique_cases = oblique_edge.values()

        # if dep_prop_node.LEMMA.lower() not in cases:
        #    continue

        prop_nodes = [x for x, l in dep_graph.children(dep_oblique_node,
                                                       filter=lambda n, l: l == "case" or l == "mark")]
        connected_case_nodes = continuous_component(prop_nodes, dep_prep_node)

        predicate = tuple([x.ID for x in connected_case_nodes])
        head_node = None
        for node in connected_case_nodes:
            if node.LEMMA.lower() in oblique_cases:
                head_node = node

        if not head_node:
            head_node = connected_case_nodes[-1]

        pred_node = oia_graph.add_words(head_node.position)
        arg1_node = oia_graph.add_words(dep_verb_node.position)
        arg2_node = oia_graph.add_words(dep_oblique_node.position)

        oia_graph.add_argument(pred_node, arg1_node, 1, mod=True)
        oia_graph.add_argument(pred_node, arg2_node, 2)


def oblique_without_prep(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    # cut X by a knife
    pattern = DependencyGraph()
    verb_node = DependencyGraphNode(UPOS="VERB|NOUN|ADJ|PROPN|PRON")
    oblique_node = DependencyGraphNode()
    pattern.add_node(verb_node)
    pattern.add_node(oblique_node)
    pattern.add_dependency(verb_node, oblique_node, r'obl:tmod|obl:npmod|obl')

    for match in dep_graph.match(pattern):

        dep_verb_node = match[verb_node]
        dep_oblique_node = match[oblique_node]

        if oia_graph.has_relation(dep_verb_node, dep_oblique_node, direct_link=False):
            continue

        oblique_edge = dep_graph.get_dependency(dep_verb_node, dep_oblique_node)
        oblique_types = oblique_edge.values()

        if "tmod" in oblique_types:

            oia_pred_node = oia_graph.add_aux("TIME_IN")

            arg1_node = oia_graph.add_words(dep_verb_node.position)
            arg2_node = oia_graph.add_words(dep_oblique_node.position)

            oia_graph.add_argument(oia_pred_node, arg1_node, 1, mod=True)
            oia_graph.add_argument(oia_pred_node, arg2_node, 2)

        else:  # "npmod" in oblique_types and others

            oia_verb_node = oia_graph.add_words(dep_verb_node.position)
            obl_node = oia_graph.add_words(dep_oblique_node.position)

            oia_graph.add_mod(obl_node, oia_verb_node)
