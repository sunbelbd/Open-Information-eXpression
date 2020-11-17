"""
goeswith
"""
from oix.parser.ud2oia.rule.converter.utils import merge_dep_nodes

from oix.oia.graphs.dependency_graph import DependencyGraph


def num_pair(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    pattern = DependencyGraph()

    num1_node = pattern.create_node(UPOS="NUM")
    num2_node = pattern.create_node(UPOS="NUM")
    case_node = pattern.create_node(LEMMA=r"--|-|by")

    pattern.add_dependency(num1_node, num2_node, r'nmod')
    pattern.add_dependency(num2_node, case_node, r'case')

    num_intervals = []

    for match in dep_graph.match(pattern):

        dep_num1_node = match[num1_node]
        dep_num2_node = match[num2_node]
        dep_case_node = match[case_node]

        if dep_num1_node.LOC < dep_case_node.LOC < dep_num2_node.LOC or \
                dep_num2_node.LOC < dep_case_node.LOC < dep_num1_node.LOC:
            interval = [dep_num1_node, dep_case_node, dep_num2_node]
            interval.sort(key=lambda x: x.LOC)
            num_intervals.append(interval)

    for interval in num_intervals:
        interval_node = merge_dep_nodes(interval,
                                        UPOS="NOUN",
                                        LOC=interval[-1].LOC
                                        )

        dep_graph.replace_nodes(interval, interval_node)


def number_per_unit(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    units = []
    for node in dep_graph.nodes(filter=lambda n: n.UPOS == "SYM"):

        previous_node = dep_graph.get_node_by_loc(node.LOC - 1)
        post_node = dep_graph.get_node_by_loc(node.LOC + 1)

        if not previous_node or not post_node:
            continue

        if previous_node.UPOS == "NUM" and post_node.UPOS == "NOUN":
            units.append((previous_node, node, post_node))

    for unit in units:
        unit_node = merge_dep_nodes(unit,
                                    UPOS="NUM",
                                    LOC=unit[-1].LOC
                                    )

        dep_graph.replace_nodes(unit, unit_node)

        # oia_graph.add_word(unit_node.ID)
