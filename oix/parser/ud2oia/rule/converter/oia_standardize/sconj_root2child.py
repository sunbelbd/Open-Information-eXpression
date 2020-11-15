"""
make sconj as root
"""
from oix.oia.envolve.envolver import Envolver
from oix.oia.graphs.oia_graph import OIAGraph
from oix.oia.standard import CONJUNCTION_WORDS, language
from loguru import logger

class SCONJRoot2Child(Envolver):

    """
    MakeSCONJRoot
    """

    def forward(self, oia_graph: OIAGraph, **kwargs):
        """
        make all rooted SCONJ as the subordinate component
        @param oia_graph:
        @type oia_graph:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """

        for node in oia_graph.nodes():

            if not oia_graph.node_text(node) in CONJUNCTION_WORDS[language]:
                continue

            logger.debug("SCONJ node found {}".format(oia_graph.node_text(node)))

            children = list(oia_graph.children(node))
            parents = list(oia_graph.parents(node))

            arg1 = [child for child, edge in children if edge.label == "pred.arg.1"]
            arg2 = [child for child, edge in children if edge.label == "pred.arg.2"]

            if len(arg1) > 1 or len(arg2) > 1:
                raise Exception("Bad oia graph ")
            elif len(arg1) == 1 and len(arg2) == 1:

                arg1 = arg1[0]
                arg2 = arg2[0]

                for parent, edge in parents:
                    oia_graph.remove_relation(parent, node)
                    oia_graph.add_relation(parent, arg2, edge.label)

                oia_graph.remove_relation(node, arg2)
                oia_graph.add_relation(arg2, node, "as:pred.arg.2")


    def backward(self, oia_graph: OIAGraph, ** kwargs):
        """

        @param oia_graph:
        @type oia_graph:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """

        raise NotImplementedError




