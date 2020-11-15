"""
update to new standard
"""
from oix.oia.envolve.envolver import Envolver

from oix.oia.graphs.oia_graph import OIAGraph, OIAAuxNode


class PredefinedPredicate2Edge(Envolver):

    """
    MakeSCONJRoot
    """

    def forward(self, oia_graph: OIAGraph, **kwargs):
        """

        @param oia_graph:
        @type oia_graph:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """

        node_edge_mapping = {
            "VOC": "vocative",
            "APPOS": "appos",
            "DISCOURSE": "discourse",
            "REPARANDUM": "reparandum",
            "TOPIC": "topic",
            "TIME_IN": "mod"
        }

        for node in list(oia_graph.nodes()):

            if not (isinstance(node, OIAAuxNode) and node.label in {'VOC', 'APPOS', 'TIME_IN',
                                  'TOPIC', 'DISCOURSE', 'REPARANDUM'}):

                continue

            children = list(oia_graph.children(node))
            parents = list(oia_graph.parents(node))

            assert 0 < len(children) <= 2

            if len(children) == 2:
                arg1 = [child for child, edge in children if edge.label == "pred.arg.1"]
                arg2 = [child for child, edge in children if edge.label == "pred.arg.2"]
                assert len(arg1) == 1 and len(arg2) == 1
                arg1 = arg1[0]
                arg2 = arg2[0]

                oia_graph.add_relation(arg1, arg2, node_edge_mapping[node.label])

                for parent, edge in parents:
                    oia_graph.add_relation(parent, arg1, edge.label)

                oia_graph.remove_node(node)
            else:
                child, edge = children[0]
                if edge.label == "pred.arg.1":
                    arg1 = child
                    arg2 = [p for p, l in parents if l == "as:pred.arg.2"]
                    assert len(arg2) == 1
                    arg2 = arg2[0]

                    oia_graph.add_relation(arg2, arg1, "as:" + node_edge_mapping[node.label])
                    oia_graph.remove_node(node)
                elif edge.label == "pred.arg.2":
                    arg2 = child
                    arg1 = [p for p, l in parents if l.label == "as:pred.arg.1"]
                    assert len(arg1) == 1, [l.label for p, l in parents]
                    arg1 = arg1[0]

                    oia_graph.add_relation(arg1, arg2, node_edge_mapping[node.label])
                    oia_graph.remove_node(node)
                else:
                    raise Exception("Unknow edges: {}".format(edge.label))


    def backward(self, oia_graph: OIAGraph, ** kwargs):
        """

        @param oia_graph:
        @type oia_graph:
        @return:
        @rtype:
        """
        raise NotImplementedError


