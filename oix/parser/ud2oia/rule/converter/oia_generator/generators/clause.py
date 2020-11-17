"""
simple_clause
"""
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext

from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph

"""
##### Simple Clause, S V DO IO#####

##### NOT SIMPLE!!!!! #####

##### NOT INCLUDEING PASSIVE and sentences like She is smart #####

##### He gives her a book #####
##### She wants him to go #####
##### She wants to go #####
##### She thinks that he went there #####


"""


def simple_clause(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    :TODO badcase  Attached is a new link
    :param dep_graph:
    :param oia_graph:
    :return:
    """
    # for node in dep_graph.nodes():
    #     print('node:',node)
    for pred_node in dep_graph.nodes(filter=lambda x: x.UPOS in {"VERB", "ADJ", "NOUN", "AUX", "ADV"}):
        # ADJ is for "With the demand so high,"
        # NOUN is for "X the best for Y"
        # AUX is for have in "I have a cat"
        # print('pred_node', pred_node)
        expl = None
        nsubj = None
        subj = None
        objs = []

        for child, rel in dep_graph.children(pred_node):
            # print('child node:', child)
            # print('child rel:', rel)
            if ('nsubj' in rel or "csubj" in rel):  # and ":xsubj" not in rel:
                nsubj = child
            elif rel.startswith('obj'):
                objs.append((child, 1))
            elif rel.startswith('iobj'):
                objs.append((child, 0))
            elif 'ccomp' in rel or "xcomp" in rel:  # and child.UPOS == "VERB":
                objs.append((child, 2))
            elif "expl" in rel:
                expl = child

        if nsubj:
            # if pred_node.LOC < nsubj.LOC:
            #     # TODO: in what situation?
            #     objs.insert(0, nsubj)
            # else:
            subj = nsubj

        if expl:  # It VERB subj that    # VERB subj it that
            if expl.LOC < pred_node.LOC:
                subj = expl
                objs.insert(0, (subj, -1))
            else:  # expl.LOC > pred_node.LOC:
                objs.insert(0, (expl, -1))

        if not subj and not objs:
            continue

        pred_node = oia_graph.add_words(pred_node.position)

        if not pred_node:
            continue

        arg_index = 1

        if subj is not None:
            if not oia_graph.has_relation(pred_node, subj):
                subj_node = oia_graph.add_words(subj.position)
                oia_graph.add_argument(pred_node, subj_node, arg_index)

        arg_index += 1

        objs.sort(key=lambda x: x[1])

        for obj, weight in objs:
            # print('obj:',obj)
            oia_obj_node = oia_graph.add_words(obj.position)

            # def __sconj_node(n):
            #    # that conj is ommited
            #    return (n.UPOS == "SCONJ" and n.LEMMA not in {"that"})

            def __adv_question_node(n):
                return ((n.UPOS == "ADV" and n.LEMMA in {"when", "where", "how", "whether"})
                )

            #
            # def __pron_question_node(n):
            #     return (n.UPOS == "PRON" and n.LEMMA in {"what", "who", "which"})

            # def __interested_node2(n):
            #     # that conj is ommited
            #     return (n.UPOS == "PART")

            # sconj_nodes = [n for n, l in dep_graph.children(obj,
            #                      filter=lambda n,l: l == "mark" and __sconj_node(n))]
            adv_question_nodes = [n for n, l in dep_graph.children(obj,
                                                                   filter=lambda n,
                                                                                 l: l == "mark" and __adv_question_node(
                                                                       n))]

            # subj_question_nodes = [n for n, l in dep_graph.children(obj,
            #                        filter=lambda n,l: "subj" in l and __pron_question_node(n))]
            #
            # obj_question_nodes = [n for n, l in dep_graph.children(obj,
            #                         filter=lambda n,
            #                                       l: ("obj" in l or "comp") in l and __pron_question_node(
            #                             n))]
            # nodes_of_interests2 = [n for n, l in dep_graph.children(obj,
            #                      filter=lambda n,l: l == "advmod" and __interested_node2(n))]
            # print('nodes_of_interests:', nodes_of_interests)
            # if nodes_of_interests2:
            #     assert len(nodes_of_interests2) == 1
            #     interest_node = nodes_of_interests2[0]
            #     oia_interest_node = oia_graph.add_word_with_head(interest_node.LOC)
            #     oia_graph.add_argument(pred_node, oia_interest_node, arg_index)
            #     # oia_graph.add_function(oia_interest_node, oia_obj_node)
            #     arg_index += 1
            #     oia_graph.add_argument(oia_interest_node, oia_obj_node, arg_index)
            #     arg_index += 1

            if adv_question_nodes:
                assert len(adv_question_nodes) == 1
                interest_node = adv_question_nodes[0]
                oia_interest_node = oia_graph.add_words(interest_node.position)
                oia_graph.add_argument(pred_node, oia_interest_node, arg_index)
                oia_graph.add_function(oia_interest_node, oia_obj_node)

            else:
                if not oia_graph.has_relation(pred_node, obj):
                    oia_graph.add_argument(pred_node, oia_obj_node, arg_index)

            arg_index += 1

    pattern = DependencyGraph()
    parent_pred = pattern.create_node()
    child_pred = pattern.create_node()
    question_word = pattern.create_node(LEMMA=r'what|who')

    pattern.add_dependency(parent_pred, child_pred, r'subj|nsubj|iobj|obj|xcomp|ccomp')
    pattern.add_dependency(parent_pred, question_word, r'subj|nsubj|iobj|obj|xcomp|ccomp')
    pattern.add_dependency(child_pred, question_word, r'subj|nsubj|iobj|obj|xcomp|ccomp')

    for match in dep_graph.match(pattern):
        dep_parent_pred, dep_child_pred, dep_question_word = [match[x]
                                                              for x in [parent_pred, child_pred, question_word]]

        oia_parent_pred, oia_child_pred, oia_question_word = [oia_graph.add_words(x.position)
                                                                    for x in [dep_parent_pred, dep_child_pred,
                                                                              dep_question_word]]

        oia_question_word.is_func = True

        rel = oia_graph.get_edge(oia_child_pred, oia_question_word)

        oia_graph.remove_relation(oia_child_pred, oia_question_word)
        oia_graph.remove_relation(oia_parent_pred, oia_child_pred)

        oia_graph.add_relation(oia_question_word, oia_child_pred, "mod_by:" + rel.label)

    #     print('simple_clause oia node:', str(node))
