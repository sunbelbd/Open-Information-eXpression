"""
debugger for ud2oia
"""
from collections import defaultdict, OrderedDict, namedtuple
import copy

from oix.oia.graphs.dependency_graph import DependencyGraph, UDGraphVisualizer
from oix.oia.graphs.oia_graph import OIAGraphVisualizer, OIAGraph
from uda.structure.graph.visualizer import GraphVisualizer



UD2OIAStates = namedtuple("CTB2OIAStates",
                              ["ctb_node", "processor", "processed", "context", "oia_graph"])


class UD2OIADebugger(object):

    def __init__(self, ud_graph, options):
        """

        @param save_files:
        """
        self.ud_graph = copy.deepcopy(ud_graph)

        self.options = options
        self.records = defaultdict(OrderedDict)

        self.history = OrderedDict()

    def record(self, phrase, processor, graph, message=None):
        """

        @param phrase:
        @param processor:
        @param result:
        @return:
        """

        self.records[phrase][processor] = (copy.deepcopy(graph), message)


    def visualize(self, as_image=False):
        """

        @return:
        @rtype:
        """

        oia_visualizer = OIAGraphVisualizer()
        ud_visualizer = UDGraphVisualizer()

        all_results = defaultdict(OrderedDict)

        for phrase in self.records:

            for processor_name, (result, message) in self.records[phrase].items():


                if as_image:

                    file_name = "{0}.{1}.{2}.png".format(self.options.uri, phrase, processor_name)
                    if isinstance(result, DependencyGraph):
                        graph_dot = ud_visualizer.visualize(result, file_name=file_name)
                    elif isinstance(result, OIAGraph):
                        graph_dot = oia_visualizer.visualize(result, file_name=file_name)
                    else:
                        raise Exception("Unknown debugger result")
                else:

                    if isinstance(result, DependencyGraph):
                        graph_dot = ud_visualizer.visualize(result)
                    elif isinstance(result, OIAGraph):
                        graph_dot = oia_visualizer.visualize(result)
                    else:
                        raise Exception("Unknown debugger result")

                all_results[phrase][processor_name] = (graph_dot, message)

        return all_results


    def record2(self, ctb_node, processor, processed, context, oia_graph):
        """

        @param ctb_node:
        @type ctb_node:
        @param processor:
        @type processor:
        @param processed:
        @type processed:
        @param oia_graph:
        @type oia_graph:
        @return:
        @rtype:
        """

        oia_history = copy.deepcopy(oia_graph)


        debug_info = UD2OIAStates(ctb_node=ctb_node, processor=processor,
                                      processed=processed, context=copy.deepcopy(context),
                                      oia_graph=oia_history)

        if ctb_node in self.history:
            self.history[ctb_node].append(debug_info)
        else:
            self.history[ctb_node] = [debug_info]
