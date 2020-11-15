"""
update to new standard
"""
import more_itertools

from oix.oia.envolve.envolver import Envolver

from oix.oia.graphs.oia_graph import OIAGraph, OIAAuxNode
from loguru import logger

class NounSplitOf(Envolver):

    """
    MakeSCONJRoot
    """

    def forward(self, oia_graph: OIAGraph, **kwargs):
        """
        split the noun phrase with of in it
        According to the previous merge operation,
        if there is any modification to the part after the of, the noun phrase will be not merged.
        So the noun phrases with of do not have any modification to the second part.
        @param oia_graph:
        @type oia_graph:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """

        for node in list(oia_graph.nodes()):

            node_words = oia_graph.node_text(node).split(" ")
            try:
                index = node_words.index("of")
            except Exception as e:
                continue

            if len(node_words) == 1: # that is of
                continue

            of_split_words = []
            current_words = []
            for span in node.spans:
                if isinstance(span, str):
                    current_words.append(span)
                else:
                    start, end = span
                    for idx in range(start, end + 1):
                        if oia_graph.words[idx] == "of":
                            of_split_words.append(current_words)
                            of_split_words.append(idx)
                            current_words = []
                        else:
                            current_words.append(idx)

            if not current_words:
                # of is the ending, warning, maybe something like "because of "
                logger.warning("We found a of at the last of the phrase: " + oia_graph.node_text(node))
                continue

            of_split_words.append(current_words)

            first_part_words = of_split_words[0]
            first_node = oia_graph.add_words(first_part_words)
            previous_node = first_node

            for p, l in list(oia_graph.parents(node)):
                oia_graph.add_relation(p, first_node, l.label)
                oia_graph.remove_relation(p, node)

            children = list(oia_graph.children(node))
            if children:
                logger.warning("noun of noun has {0} children, be careful!!!".format(len(children)))
                for c, l in children:
                    logger.warning("Child: {} {}".format(l.label, oia_graph.node_text(c)))
                    oia_graph.add_relation(first_node, c, l.label)
                    oia_graph.remove_relation(node, c)

            oia_graph.remove_node(node)

            for of_word, noun_words in more_itertools.chunked(of_split_words[1:], 2):
                of_node = oia_graph.add_words([of_word])
                next_node = oia_graph.add_words(noun_words)

                oia_graph.add_relation(previous_node, of_node, "as:pred.arg.1")
                oia_graph.add_relation(of_node, next_node, "pred.arg.2")
                previous_node = next_node


    def backward(self, oia_graph: OIAGraph, ** kwargs):
        """

        @param oia_graph:
        @type oia_graph:
        @return:
        @rtype:
        """
        raise NotImplementedError


