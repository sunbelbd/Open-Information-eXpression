"""
Advp phrases
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph

valid_adj_form = {"flat", "fixed", "compound", "advmod"}


def valid_adjv_element(n, dep_graph):
    """

    :param n:
    :param valid_elements:
    :return:
    """
    elements = [n]
    for child, rel in dep_graph.children(n):
        if rel.intersect(valid_adj_form):
            elements.extend(valid_adjv_element(child, dep_graph))
    return elements


def advp_phrase(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    case: english-UD-12774
    """
    # return 
    phrases = []
    remove_rels = []
    for node in dep_graph.nodes(filter=lambda n: n.UPOS in {"ADP"}):
        # is_root = True
        need_merge_node = set()
        # if str(node.FORM).lower() != 'after':
        #     continue
        # print('advp node:', str(node.FORM))

        for parent, rel in dep_graph.parents(node):

            if "case" in rel and \
                    any(node.FORM in l.values() or node.LEMMA in l.values() for x, l in dep_graph.parents(parent)):
                break

            remove_rel = False

            # we find neighborhood adjvs
            silibings = list(dep_graph.children(parent))
            silibings.sort(key=lambda x: x[0].LOC)

            start_loc = -1
            for child, ch_rel in reversed(silibings):
                # print(str(node.FORM))
                if child.LOC >= node.LOC:
                    start_loc = child.LOC
                    continue

                if "advmod" in ch_rel and child.UPOS in {"ADJ", "ADV"} and child.LOC == start_loc - 1:
                    # is_root = True
                    need_merge_node.update(set(valid_adjv_element(child, dep_graph)))
                    remove_rel = True
                    start_loc = child.LOC
                    # adjv_element = valid_adjv_element(child, dep_graph)
            if remove_rel:
                if 'case' in rel:
                    remove_rels.append((parent, node, 'case'))
        if len(need_merge_node) == 0:
            continue
        need_merge_node.add(node)
        adjv_element = sorted(list(need_merge_node), key=lambda x: x.LOC)
        phrases.append((adjv_element, node))
    for src, trg, rel in remove_rels:
        dep_graph.remove_dependency(src, trg, rel)
    for adjv_phrase, node in phrases:
        advp_node = merge_dep_nodes(adjv_phrase,
                                    # UPOS=node.UPOS,
                                    UPOS='ADV',
                                    LOC=node.LOC
                                    )
        # print("Noun detected", noun_node.ID)
        dep_graph.replace_nodes(adjv_phrase, advp_node)
