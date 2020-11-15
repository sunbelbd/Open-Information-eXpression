"""
conjunction
"""

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext

from oix.oia.standard import language, CONJUNCTION_WORDS

def and_or_conjunction(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    #### Coordination ####
    #### I like apples, bananas and oranges. conj:and/or with punct
    #### @return a list of list of conjuncted entities
    :param sentence:
    :return:
    """

    for node in dep_graph.nodes():

        conj_components = list(dep_graph.children(node,
                                                  filter=lambda n, l: l.startswith("arg_con")))

        if not conj_components:
            continue

        oia_conj_root_node = oia_graph.add_words(node.position)

        for child, rels in conj_components:
            soake_child_node = oia_graph.add_words(child.position)
            arg_index = int(rels.values()[0])

            oia_graph.add_argument(oia_conj_root_node, soake_child_node, arg_index)


def advcl_mark_sconj(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()
    pred1_node = pattern.create_node()
    pred2_node = pattern.create_node()
    # sconj_node = pattern.create_node(UPOS="SCONJ")
    sconj_node = pattern.create_node()

    pattern.add_dependency(pred1_node, pred2_node, r'advcl\w*')
    # pattern.add_dependency(pred1_node, pred2_node, r'\w*')
    # pattern.add_dependency(pred2_node, sconj_node, r'mark|advmod')
    pattern.add_dependency(pred2_node, sconj_node, 'mark')

    for match in list(dep_graph.match(pattern)):

        dep_pred1_node = match[pred1_node]
        dep_pred2_node = match[pred2_node]
        dep_sconj_node = match[sconj_node]
        # advcl_rel = dep_graph.get_dependency(dep_pred1_node, dep_pred2_node)
        if dep_sconj_node.LEMMA not in CONJUNCTION_WORDS[language]:
             continue

        context.processed(dep_pred2_node, dep_sconj_node)
        context.processed(dep_pred1_node, dep_pred2_node)

        oia_pred1_node = oia_graph.add_words(dep_pred1_node.position)
        oia_pred2_node = oia_graph.add_words(dep_pred2_node.position)

        if dep_sconj_node.LEMMA == "if":
            # check whether there is "then"
            dep_then_nodes = [n for n, l in dep_graph.children(dep_pred1_node) if n.LEMMA == "then" and l == "advmod"]

            if dep_then_nodes:
                assert len(dep_then_nodes) == 1
                dep_then_node = dep_then_nodes[0]
                context.processed(dep_pred1_node, dep_then_node)

                if_then_position = dep_sconj_node.position + ["{1}"] + dep_then_node.position + ["{2}"]
                oia_condition_node = oia_graph.add_words(if_then_position)
            else:
                oia_condition_node = oia_graph.add_words(dep_sconj_node.position)

            oia_graph.add_argument(oia_condition_node, oia_pred2_node, 1)
            oia_graph.add_argument(oia_condition_node, oia_pred1_node, 2)
        else:
            oia_condition_node = oia_graph.add_words(dep_sconj_node.position)
            if dep_sconj_node.LEMMA in CONJUNCTION_WORDS[language]:
                oia_graph.add_argument(oia_condition_node, oia_pred2_node, 1)
                oia_graph.add_argument(oia_condition_node, oia_pred1_node, 2)
            else:
                oia_graph.add_argument(oia_condition_node, oia_pred1_node, 1, mod=True)

                oia_graph.add_argument(oia_condition_node, oia_pred2_node, 2)


