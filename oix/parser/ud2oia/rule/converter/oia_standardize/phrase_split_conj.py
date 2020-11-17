"""
fix the order of conjunctions
"""

from loguru import logger

from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph, OIAWordsNode, OIANode

import more_itertools

from oix.oia.envolve.envolver import Envolver

from oix.oia.graphs.oia_graph import OIAGraph, OIAAuxNode


def is_conjunction_without_args(node: OIANode, oia_graph: OIAGraph):
    """

    :param node:
    :param dep_graph:
    :return:
    """

    if not isinstance(node, OIAWordsNode):
        return False

    if len(node.spans) > 1:
        return False

    if node.spans[0] == "AND":
        return True

    if isinstance(node.spans[0], int) and oia_graph.words[node.spans[0]] in {"and", "but", "or"}:
        return True

    return False


class PhraseSplitCONJ(Envolver):

    """
    MakeSCONJRoot
    """

    def forward(self, oia_graph: OIAGraph, dep_graph: DependencyGraph=None, **kwargs):
        """
        note that this only process the situation that
        @param oia_graph:
        @type oia_graph:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """

        for node in list(oia_graph.nodes()):

            node_words = oia_graph.node_text(node).split(" ")

            if not any([x in {"and", "or"} for x in node_words]):
                continue

            if any(["{" in x and "}" in x for x in node_words]):
                continue

            arguments = []
            conjs = []
            current_words = []

            for span in node.spans:
                if isinstance(span, str):
                    current_words.append(span)
                else:
                    start, end = span
                    for idx in range(start, end + 1):
                        if oia_graph.words[idx].lower() in {"and", "or"}:
                            arguments.append(current_words)
                            conjs.append(idx)
                            current_words = []
                        else:
                            current_words.append(idx)

            arguments.append(current_words)

            logger.debug("conj found = {}".format(conjs))
            logger.debug("argument found = {}".format(arguments))

            if all(not arg or all(oia_graph.words[x] in {",", ";", ".", " "} for x in arg) for arg in arguments):  # single words
                continue

            if len(conjs) == 1:
                conj_words = conjs

            else: # len(conjs) >= 2:
                logger.warning("We are processing conjs with more than two args")
                conj_words = ['{1}']
                for idx, conj in enumerate(conjs):
                    conj_words.append(conj)
                    conj_words.append("{{{0}}}".format(idx + 2))

            conj_node = oia_graph.add_words(conj_words)


            for idx, arg in enumerate(arguments):
                arg_node = oia_graph.add_words(arg)
                oia_graph.add_relation(conj_node, arg_node, "pred.arg.{0}".format(idx + 1))


            for p, l in list(oia_graph.parents(node)):
                oia_graph.add_relation(p, conj_node, l.label)
                oia_graph.remove_relation(p, node)

            for c, l in list(oia_graph.children(node)):
                oia_graph.add_relation(conj_node, c, l.label)
                oia_graph.remove_relation(node, c)

            oia_graph.remove_node(node)



    def backward(self, oia_graph: OIAGraph, ** kwargs):
        """

        @param oia_graph:
        @type oia_graph:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """

        fixed = False
        for node in list(oia_graph.nodes()):
            if not is_conjunction_without_args(node, oia_graph):
                continue

            relations = [(n, l.label) for n, l in oia_graph.children(node)]

            relations = list(filter(lambda x: x[1].startswith("pred.arg."), relations))

            if not relations:
                continue

            if any(len(list(oia_graph.children(child))) for child, rel in relations):
                # child nodes also has child, not merge
                continue

            merged_words = sum([list(child.words()) for child, rel in relations], [])
            start = min([x for x in merged_words if isinstance(x, int)])
            end = max([x for x in merged_words if isinstance(x, int)])
            new_node = oia_graph.add_spans([(start, end)])

            fixed = True
            for child, rel in relations:
                oia_graph.remove_node(child)

            oia_graph.replace(node, new_node)

            logger.debug("Merging {0} to {1}".format("|".join(oia_graph.node_text(child)
                                                              for child, rel in relations),
                                                     oia_graph.node_text(new_node)))

        return fixed
