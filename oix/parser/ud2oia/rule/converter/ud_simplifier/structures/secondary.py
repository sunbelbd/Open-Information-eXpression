"""
secondary predicate
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph


def secondary_predicate(dep_graph: DependencyGraph):
    """
    detect the case of xcomp as a secondary predicate,
    and add implicit (be) node to make a predicate
    :param dep_graph:
    :return:
    """

    pattern = DependencyGraph()

    pred_node = pattern.create_node()
    xcomp_node = pattern.create_node(UPOS=r'(?!VERB\b)\b\w+')
    xcomp_subj_node = pattern.create_node()

    pattern.add_dependency(pred_node, xcomp_node, "xcomp")
    pattern.add_dependency(xcomp_node, xcomp_subj_node, "nsubj")
    pattern.add_dependency(pred_node, xcomp_subj_node, "obj")

    for match in list(dep_graph.match(pattern)):

        dep_pred_node = match[pred_node]
        dep_xcomp_node = match[xcomp_node]
        dep_xcomp_subj_node = match[xcomp_subj_node]

        # if not (dep_pred_node.LOC < dep_xcomp_subj_node.LOC and dep_pred_node.LOC < dep_xcomp_node.LOC):
        #    raise Exception("Unexpected Situation, let's throw out to see what happens")
        # the position of dep_xcomp_subj_node and dep_xcomp_node may be reversed in questions
        # I can't tell you how ominous I found Bush's performance in that interview.

        if dep_pred_node.LOC < dep_xcomp_subj_node.LOC < dep_xcomp_node.LOC:

            dep_graph.remove_dependency(dep_pred_node, dep_xcomp_node)
            dep_graph.remove_dependency(dep_pred_node, dep_xcomp_subj_node)
            dep_graph.remove_dependency(dep_xcomp_node, dep_xcomp_subj_node)

            if dep_xcomp_node.UPOS == "ADJ" or dep_xcomp_node.UPOS == "ADV":
                new_pred_nodes = ["(be)", dep_xcomp_node]
                dep_be_node = merge_dep_nodes(new_pred_nodes,
                                              UPOS="VERB",
                                              LOC=dep_xcomp_node.LOC
                                              )

                dep_graph.add_node(dep_be_node)

                dep_graph.add_dependency(dep_pred_node, dep_be_node, "obj")
                dep_graph.add_dependency(dep_be_node, dep_xcomp_subj_node, "nsubj")

                for child, l in list(dep_graph.children(dep_xcomp_node)):
                    dep_graph.remove_dependency(dep_xcomp_node, child)
                    dep_graph.add_dependency(dep_be_node, child, l)

                dep_graph.remove_node(dep_xcomp_node)

            else:
                dep_be_node = dep_graph.create_node(FORM="(be)",
                                                    LEMMA="(be)",
                                                    UPOS="VERB",
                                                    LOC=dep_xcomp_node.LOC - 0.5
                                                    )
                dep_be_node.aux = True

                dep_graph.add_dependency(dep_pred_node, dep_be_node, "obj")
                dep_graph.add_dependency(dep_be_node, dep_xcomp_subj_node, "nsubj")
                dep_graph.add_dependency(dep_be_node, dep_xcomp_node, "obj")

        elif dep_xcomp_node.LOC < dep_pred_node.LOC:

            dep_graph.remove_dependency(dep_pred_node, dep_xcomp_node)
            dep_graph.remove_dependency(dep_pred_node, dep_xcomp_subj_node)
            dep_graph.remove_dependency(dep_xcomp_node, dep_xcomp_subj_node)

            # in question, for example : how ominous
            # I can't tell you how ominous I found Bush's performance in that interview.

            dep_be_node = dep_graph.create_node(FORM="(be)",
                                                LEMMA="(be)",
                                                UPOS="VERB",
                                                LOC=dep_xcomp_node.LOC - 0.5
                                                )
            dep_be_node.aux = True

            dep_graph.add_dependency(dep_pred_node, dep_be_node, "obj")
            dep_graph.add_dependency(dep_be_node, dep_xcomp_subj_node, "nsubj")

            if dep_xcomp_node.UPOS == "ADJ" or dep_xcomp_node.UPOS == "ADV":
                dep_graph.add_dependency(dep_be_node, dep_xcomp_node, "amod")
            else:
                dep_graph.add_dependency(dep_be_node, dep_xcomp_node, "obj")
