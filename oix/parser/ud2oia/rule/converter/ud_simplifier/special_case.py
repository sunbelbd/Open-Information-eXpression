"""TODO: add doc string
    """
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph


def ever_since(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    ever_nodes = []
    since_nodes = []
    for node in dep_graph.nodes():
        if node.LEMMA == "ever":
            ever_nodes.append(node)
        elif node.LEMMA == "since":
            since_nodes.append(node)
    if not ever_nodes or not since_nodes:
        return
    since_LOCs = [node.LOC for node in since_nodes]
    rel_remove = []
    union_nodes = []
    for ever_node in ever_nodes:
        expect_LOC = ever_node.LOC + 1
        if expect_LOC not in since_LOCs:
            continue
        union_nodes.append((ever_node, since_nodes[since_LOCs.index(expect_LOC)]))
        for p_node, p_rel in dep_graph.parents(ever_node):
            if 'advmod' not in p_rel:
                continue
            rel_remove.append((p_node, ever_node, 'advmod'))
    for src, trg, rel in rel_remove:
        dep_graph.remove_dependency(src, trg, rel)
    for ever_node, since_node in union_nodes:
        new_since_node = merge_dep_nodes([ever_node, since_node],
                                         UPOS=since_node.UPOS,
                                         LOC=since_node.LOC
                                         )
        dep_graph.replace_nodes([ever_node, since_node], new_since_node)


def special_case(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    case_list = [ever_since]
    for case in case_list:
        case(dep_graph)
