"""
appositive
"""
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode


def appositive_phrase(dep_graph, oia_graph, context: UD2OIAContext):
    """
    ##### Apposition:  Trump, president of US, came #####
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()

    subj_node = DependencyGraphNode()

    appos_node = DependencyGraphNode()

    pattern.add_nodes([subj_node, appos_node])

    pattern.add_dependency(subj_node, appos_node, r'\w*appos\w*')

    for match in dep_graph.match(pattern):

        dep_subj_node = match[subj_node]
        dep_appos_node = match[appos_node]

        oia_appos_node = oia_graph.add_words(dep_appos_node.position)
        oia_subj_node = oia_graph.add_words(dep_subj_node.position)

        if oia_appos_node and oia_subj_node:
            pred_node = oia_graph.add_aux(label="APPOS")

            oia_graph.add_argument(pred_node, oia_subj_node, 1)
            oia_graph.add_argument(pred_node, oia_appos_node, 2)

#
# def appositive_clause(dep_graph, oia_graph):
#     """
#     TODO: Need review. It seems buggy
#     ##### (It) Cleft #####
#     ##### It is clear that she is happy
#     :param dep_graph:
#     :param oia_graph:
#     :return:
#     """
#
#     pattern = DependencyGraph()
#
#     subj_node = DependencyGraphNode(FORM=r'(?!there|There)')
#
#     be_node = DependencyGraphNode(UPOS="VERB")
#     adv_node = DependencyGraphNode()
#     that_node = DependencyGraphNode()
#
#     pattern.add_nodes([adv_node, be_node, subj_node, that_node])
#
#     pattern.add_dependency(that_node, subj_node, r'\w*expl\w*')
#     pattern.add_dependency(adv_node, be_node, r'\w*cop\w*')
#
#     for match in dep_graph.match(pattern):
#
#         dep_subj_node = match[subj_node]
#         dep_obj_node = match[adv_node]
#         dep_be_node = match[be_node]
#
#         def __valid_aux(n, l):
#             return l == "aux" and in_interval(n, dep_subj_node, dep_be_node)\
#
#         aux_node = list(dep_graph.children(dep_obj_node, filter=__valid_aux))
#
#         if aux_node:
#             aux_node = aux_node[0][0]
#             pred = (aux_node.ID, dep_be_node.ID, dep_obj_node.ID)
#         else:
#             pred = (dep_be_node.ID, dep_obj_node.ID)
#
#         pred_node = oia_graph.add_word(pred)
#         subj_node = oia_graph.add_word_with_head(subj_node)
#
#         oia_graph.add_argument(pred_node, subj_node, 1)
