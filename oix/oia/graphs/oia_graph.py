"""
oia graph
"""
import io
import json
import os
import uuid
from collections import defaultdict, Counter
from io import StringIO
from typing import Union

import numpy as np
from oix.oia.graphs.utils import CompactJSONEncoder
from uda.structure.graph.graph import Graph, DirectedGraph, Node, Edge
from oix.oia.standard import QUESTION_WORDS, language
from loguru import logger
import itertools
import copy

from oix.oia.graphs.dependency_graph import DependencyGraphSuperNode, DependencyGraphNode, DependencyGraph

from oix.oia.standard import NODES, EDGES
from uda.structure.graph.visualizer import GraphVisualizer
import re

arg_placeholder_pattern = re.compile(r'{\d}')

def is_arg_placeholder(string):
    """

    @param string:
    @return:
    """
    return re.match(arg_placeholder_pattern, string) is not None


class OIANode(Node):
    """
    OIANode
    """

    def __init__(self):
        super().__init__()
        self.id = None

    @property
    def ID(self):
        """

        :return:
        """
        return self.id

    @ID.setter
    def ID(self, id):
        """
        setter
        """
        self.id = id

    def __hash__(self):
        """

        :return:
        """
        return hash(self.ID)

    def __eq__(self, another):
        """

        :param another:
        :return:
        """
        return self.ID == another.ID


import collections.abc

def standardize_spans(spans):
    """

    @param spans:
    @type spans:
    @return:
    @rtype:
    """
    standardized = []
    for span in spans:
        if isinstance(span, int):
            standardized.append((span, span))
        elif isinstance(span, str):
            standardized.append(span)
        else:
            standardized.append(tuple(span))

    return tuple(standardized)

def readable_spans(spans):
    """

    @param spans:
    @type spans:
    @return:
    @rtype:
    """

    readable = []
    for span in spans:
        if isinstance(span, int):
            readable.append(span)
        elif isinstance(span, str):
            readable.append(span)
        else:
            start, end = span
            if start == end:
                span = start

            readable.append(span)

    return tuple(readable)


class OIAWordsNode(OIANode):
    """
    OIANode
    """

    def __init__(self, spans):

        super().__init__()
        self._spans = standardize_spans(spans)

        self.contexts = list()

    def has_symbols(self):
        """

        @return:
        @rtype:
        """

        for span in self._spans:
            if isinstance(span, str):
                return True

        return False

    def add_span_to_head(self, span):
        """

        @param span:
        @type span:
        @return:
        @rtype:
        """
        if isinstance(span, str):
            self._spans = list(self._spans)
            self._spans.insert(0, span)
            self._spans = tuple(self._spans)
            return

        if isinstance(span, int):
            span = [span, span]
        if isinstance(self._spans[0], (list, tuple)) and \
             span[1] == self._spans[0][0] - 1:
                self._spans = tuple([(span[0], self._spans[0][1])] + list(self._spans)[1:])
        else:
            x = list(self._spans)
            x.insert(0, span)
            self._spans = tuple(x)

    def add_span_to_tail(self, span):
        """

        @param span:
        @type span:
        @return:
        @rtype:
        """
        if isinstance(span, str):
            self._spans = list(self._spans)
            self._spans.append(span)
            self._spans = tuple(self._spans)
            return

        if isinstance(span, int):
            span = [span, span]

        if isinstance(self._spans[-1], (list, tuple)) and \
                span[0] == self._spans[-1][1] + 1:
            self._spans = tuple(list(self._spans)[:-1]  + [(self._spans[-1][0], span[1])])
        else:
            x = list(self._spans)
            x.append(span)
            self._spans = tuple(x)

    def add_spans_to_head(self, spans):
        """

        @param span:
        @type span:
        @return:
        @rtype:
        """

        for span in reversed(spans):
            self.add_span_to_head(span)

    def add_spans_to_tail(self, spans):
        """

        @param span:
        @type span:
        @return:
        @rtype:
        """

        for span in spans:
            self.add_span_to_tail(span)


    @property
    def spans(self):
        """

        @return:
        @rtype:
        """
        return self._spans

    @spans.setter
    def spans(self, spans):
        """

        @param spans:
        @type spans:
        @return:
        @rtype:
        """
        self._spans = standardize_spans(spans)

    @property
    def readable_spans(self):
        """

        @return:
        @rtype:
        """
        return readable_spans(self._spans)

    def __str__(self):
        """

        :return:
        """
        return ",".join(map(str, self.spans))

    def __contains__(self, word_id):
        """

        :param word_id:
        :return:
        """

        for span in self._spans:
            if isinstance(span, str):
                if span == word_id:
                    return True
                else:
                    continue
            else:
                start, end = span
                if start <= word_id <= end:
                    return True
        return False

    def words(self):
        """

        :return:
        """
        for span in self._spans:
            if isinstance(span, str):
                yield span
            else:
                start, end = span
                for i in range(start, end + 1):
                    yield i


class OIAAuxNode(OIANode):
    """
    OIANode
    """

    def __init__(self, label):
        super().__init__()
        self.label = label
        self.contexts = list()


    def __str__(self):
        """

        :return:
        """
        return self.label


import networkx as nx
import inspect




class OIAGraphEdge(Edge):
    """
    a set of relations between a pair of nodes for multiple edges.
    behaves like a single relation (that is, a string)
    for code compatability
    """

    def __init__(self, label=None, mod=False):
        super().__init__()
        self.label = label
        self.mod = mod
        self.contexts = []

    def __bool__(self):
        """

        :return:
        """
        return self.label is not None

    @property
    def value(self):
        """
        :return:
        :rtype:
        """
        return self.label

    @value.setter
    def value(self, value):
        """
        :return:
        :rtype:
        """
        self.label = value


def positions2spans(words):
    """
    check
    """

    if isinstance(words, int):
        words = tuple([words])
    elif isinstance(words, list) or isinstance(words, tuple):
        words = tuple(words)
    else:
        raise Exception("the words must be an int or a list of int/str")

    spans = []
    idx = 0
    while idx < len(words):
        if isinstance(words[idx], str):
            spans.append(words[idx])
            idx += 1
        else:
            start_idx = idx
            while start_idx + 1 < len(words) \
                and words[start_idx + 1] == words[start_idx] + 1:
                start_idx += 1

            spans.append((words[idx], words[start_idx]))
            idx = start_idx + 1

    return tuple(spans)

class OIAGraph(DirectedGraph):
    """
    Dependency graph
    """

    def __init__(self):
        super().__init__()
        self.meta = None
        self.words = []
        self.context_hook = lambda: None

        self.spans2node = dict()

    def __copy__(self):
        """

        :return:
        """
        from copy import copy
        copied = DirectedGraph.__copy__(self)
        copied.meta = copy(self.meta)
        copied.words = copy(self.words)
        copied.context_hook = self.context_hook
        return copied

    def __deepcopy__(self, memodict={}):
        """

        :param memodict:
        :type memodict:
        :return:
        :rtype:
        """

        from copy import deepcopy

        copied = DirectedGraph.__deepcopy__(self)
        copied.meta = deepcopy(self.meta)
        copied.words = deepcopy(self.words)
        copied.context_hook = deepcopy(self.context_hook)
        return copied

    def set_words(self, words):
        """

        :param words:
        :return:
        """
        if isinstance(words, list):
            self.words = words
        else:
            raise Exception("words input not list.")

    def add_words(self, words):
        """

        :param head:
        :return:
        """

        if len(words) == 1 and isinstance(words[0], float):
            words = tuple(words)
            if words not in self.spans2node:
                self.spans2node[words] = self.add_aux("(be)")

            return self.spans2node[words]

        if any(isinstance(x, float) for x in words):
            raise Exception("float found" )

        spans = positions2spans(words)

        return self.add_spans(spans)

    def set_context_hook(self, hook):
        """

        :param hook:
        :return:
        """
        self.context_hook = hook

    def add_node(self, node, reuse_id=False):
        """

        :param node:
        :return:
        """
        assert isinstance(node, OIAWordsNode) or isinstance(node, OIAAuxNode)

        context = self.context_hook()
        # logger.error("context called {}".format(context))
        if context:
            node.contexts.extend(context)
        return super().add_node(node, reuse_id=reuse_id)

    def add_spans(self, spans):
        """

        :param node:
        :return:
        """

        spans = standardize_spans(spans)

        if spans not in self.spans2node:
            added_node = OIAWordsNode(spans)
            self.spans2node[spans] = self.add_node(added_node)

        return self.spans2node[spans]

    def has_node(self, node: OIANode):
        """

        @param node:
        @type node:
        @return:
        @rtype:
        """
        if self.g.has_node(node.ID):
            return True
        else:
            return False

    def has_word(self, words):
        """

        :param word:
        :return:
        """
        spans = positions2spans(words)
        for node in self.nodes():
            if isinstance(node, OIAWordsNode) and node.spans == spans:
                added_node = node
                return True
        return False

    # def find_node_by_word(self, word):
    #     """
    #     find the node containing the given word
    #     :param word:
    #     :return:
    #     """
    #     for node in self.nodes():
    #         if isinstance(node, OIAWordsNode):
    #             if word in node:
    #                 return node
    #     return None

    def get_node_by_words(self, positions):
        """

        @param positions:
        @type positions:
        @return:
        @rtype:
        """
        spans = positions2spans(positions)

        for node in self.nodes():
            if isinstance(node, OIAWordsNode):
                if node.spans == spans:
                    return node
        return None

    def has_relation(self, node1: Union[DependencyGraphNode, OIANode],
                     node2: Union[DependencyGraphNode, OIANode],
                     direct_link=True):
        """

        :return:
        @param node1:
        @type node1:
        @param node2:
        @type node2:
        """
        if isinstance(node1, DependencyGraphNode):
            node1 = self.get_node_by_words(node1.position)

        if isinstance(node2, DependencyGraphNode):
            node2 = self.get_node_by_words(node2.position)

        if node1 is None or node2 is None:
            return False

        if direct_link and (self.g.has_edge(node1.ID, node2.ID) or self.g.has_edge(node2.ID, node1.ID)):
            return True
        elif not direct_link and (
                nx.algorithms.shortest_paths.generic.has_path(self.g, node1.ID, node2.ID) or
                nx.algorithms.shortest_paths.generic.has_path(self.g, node2.ID, node1.ID)):
            return True

        return False

    def add_aux(self, label):
        """

        :param label:
        :return:
        """

        node = OIAAuxNode(label)

        self.add_node(node)

        return node

    def get_aux(self, label):
        """

        :param label:
        :return:
        """
        for node_id in self.g.nodes:
            node = self.get_node(node_id)
            if isinstance(node, OIAAuxNode) and node.label == label:
                yield node

    # def find_node(self, word):
    #     """
    #
    #     :param word:
    #     :return:
    #     """
    #     for node in self.nodes():
    #         if isinstance(node, OIAWordsNode):
    #             if word in node:
    #                 return node

    # def has_spans(self, spans):
    #     """
    #
    #     :param words:
    #     :return:
    #     """
    #     return self.g.has_node(spans)

    def get_edge(self, node1, node2):
        """

        :param node1:
        :param node2:
        :return:
        """
        try:
            return super().get_edge(node1, node2)
        except:
            return None

    def spans(self):
        """

        @return:
        @rtype:
        """

        spans = []

        for x in self.nodes():
            if isinstance(x, OIAWordsNode):
                for span in x.spans:
                    if isinstance(span, str):
                        continue
                    elif isinstance(span, int):
                        span = (span, span)
                        spans.append(span)
                    else:
                        spans.append(tuple(span))

        spans.sort(key=lambda x: x[0])

        return spans

    def parents_on_path(self, node, ancestor):
        """

        :param node:
        :param ancestor:
        :return:
        """
        for path in nx.all_simple_paths(self.g, ancestor.ID, node.ID):
            yield self.get_node(path[-2])

    def replace(self, old_node, new_node):
        """

        :param old_node:
        :param new_node:
        :return:
        """

        if new_node.ID == old_node.ID:
            raise Exception("Bad business logic: cannot replace a node with itself")

        if self.g.has_node(new_node.ID):
            raise Exception("Bad business logic: the new node is already in the graph")

        self.add_node(new_node)

        for child, rel in self.children(old_node):
            self.g.add_edge(new_node.ID, child.ID, Edge=rel)

        for parent, rel in self.parents(old_node):
            self.g.add_edge(parent.ID, new_node.ID, Edge=rel)

        self.remove_node(old_node)

    def add_edge(self, start_node, end_node, edge):
        """

        @param start_node:
        @type start_node:
        @param end_node:
        @type end_node:
        @param edge:
        @type edge:
        @return:
        @rtype:
        """
        context = self.context_hook()
        if context:
            edge.contexts.extend(context)

        if start_node.ID not in self.g.nodes():
            raise ValueError('start node not in graph')
        if end_node.ID not in self.g.nodes():
            raise ValueError('end node not in graph')
        #self.add_node(start_node, reuse_id=True)
        #self.add_node(end_node, reuse_id=True)
        edge.start = start_node.ID
        edge.end = end_node.ID
        self.g.add_edge(start_node.ID, end_node.ID, Edge=edge)

    def add_argument(self, pred_node, arg_node, index, mod=False):
        """

        :param node1:
        :param node2:
        :param rel:
        :return:
        """

        # if isinstance(pred_node.ID, int) or isinstance(pred_node.ID, str):
        #     raise Exception("Bad ID")
        # if isinstance(arg_node.ID, int) or isinstance(arg_node.ID, str):
        #     raise Exception("Bad ID")

        edge_label = "pred.arg.{0}".format(index)

        edge = OIAGraphEdge(label=edge_label, mod=mod)

        if edge.mod:
            edge.label = "as:" + edge.label
            self.add_edge(arg_node, pred_node, edge)
        else:
            self.add_edge(pred_node, arg_node, edge)

    def add_mod(self, modifier, center):
        """

        :param target:
        :param source:
        :return:
        """

        edge = OIAGraphEdge(label="mod", mod=False)

        self.add_edge(center, modifier, edge)

    def add_function(self, functor, argument, index=None):
        """

        :param functor:
        :param argument:
        :return:
        """
        if index is None:
            index = "1"
        edge_label = "func.arg.{}".format(index)

#        if isinstance(functor.ID, int) or isinstance(functor.ID, str):
#            raise Exception("Bad ID")
#        if isinstance(argument.ID, int) or isinstance(argument.ID, str):
#            raise Exception("Bad ID")

        edge = OIAGraphEdge(label=edge_label, mod=False)

        functor.is_func = True

        self.add_edge(functor, argument, edge)

    def add_ref(self, source, ref):
        """

        :param target:
        :param source:
        :return:
        """

        edge = OIAGraphEdge(label="ref", mod=False)

        self.add_edge(source, ref, edge)

    def add_relation(self, node1, node2, rel):
        """

        :param node1:
        :param node2:
        :param rel:
        :return:
        """
        if isinstance(rel, str):
            edge = OIAGraphEdge(label=rel)
        elif isinstance(rel, OIAGraphEdge):
            edge = rel
        else:
            raise Exception("Unknown rel type")

        self.add_edge(node1, node2, edge)

    def remove_relation(self, node1, node2):
        """

        :param node1:
        :param node2:
        :return:
        """
        super().remove_edge_between(node1, node2)

    def relations(self):
        """

        :return:
        """
        return super().edges()

# #    def copy(self):
#         """
#
#         :return:
#         """
#         import copy
#         return copy.deepcopy(self)

    def node_text(self, node):
        """

        @param node:
        @type node:
        @return:
        @rtype:
        """

        if isinstance(node, OIAWordsNode):
            node_texts = []
            for span in node.spans:
                if isinstance(span, str):
                    node_texts.append(span)
                else:
                    start, end = span
                    for i in range(start, end + 1):
                        node_texts.append(self.words[i])

            node_text = " ".join(node_texts)
        else:
            node_text = node.label

        return node_text


    def topological_sort(self):
        """

        :return:
        """

        for id in nx.topological_sort(self.g):
            yield self.get_node(id)

    @staticmethod
    def parse(json_obj):
        """

        :param oia_graph:
        :return:
        """
        if isinstance(json_obj, str):
            json_obj = json.loads(json_obj)

        assert isinstance(json_obj, dict)

        graph = OIAGraph()
        graph.meta = json_obj["meta"]
        graph.words = [0] * len(json_obj["words"])
        for id, word in json_obj["words"]:
            graph.words[id] = word
        nodes = [None] * len(json_obj["oia"]["nodes"])
        for id, spans in json_obj["oia"]["nodes"]:
            if isinstance(spans, str):
                if spans not in NODES:
                    raise Exception("Invalid node {0} ".format(spans))
                node = graph.add_aux(spans)
            else:
                for span in spans:
                    if isinstance(span, str) and span not in NODES:
                        raise Exception("Invalid node {0} ".format(span))
                node = graph.add_spans(spans)
            nodes[id] = node
        for n1_id, edge_label, n2_id in json_obj["oia"]["edges"]:
            node1 = nodes[n1_id]
            node2 = nodes[n2_id]
#            if edge_label not in EDGES:
#                raise Exception("Invalid edge {0} ".format(edge_label))
            graph.add_relation(node1, node2, edge_label)
        return graph

    def data(self):
        """

        @return:
        @rtype:
        """

        oia = dict()

        oia["nodes"] = []
        node2idx = dict()
        for idx, node in enumerate(self.nodes()):
            node2idx[node.ID] = idx
            if isinstance(node, OIAWordsNode):
                oia["nodes"].append((idx, node.spans))
            else:
                oia["nodes"].append((idx, node.label))

        oia["edges"] = []
        for idx, (n1, edge, n2) in enumerate(self.relations()):
            n1_id = node2idx[n1.ID]
            n2_id = node2idx[n2.ID]
            oia["edges"].append((n1_id, edge.label, n2_id))

        data = dict()
        data["meta"] = self.meta
        data['words'] = [(idx, word) for idx, word in enumerate(self.words)]
        data['oia'] = oia

        return data

    def save(self, output_file_path):
        """

        :param output_file_path:
        :return:
        """

        data = self.data()

        with open(output_file_path, "w", encoding="UTF8") as output_file:
            json.dump(data, output_file, cls=CompactJSONEncoder, ensure_ascii=False)

    def is_predicate_node(self, node):
        """

        :param node:
        :return:
        """

        if isinstance(node, OIAAuxNode):
            return True

        for n, l in self.children(node):
            if l.label.startswith("pred.arg"):
                return True

        return False

    def is_function_node(self, node):
        """

        :param node:
        :return:
        """
        if isinstance(node, OIAAuxNode):
            if node.label == "WHETHER":
                return True
            else:
                return False

        for n, l in self.children(node):
            if "func.arg" in l.label:
                return True

        for word_id in node.words():
            if isinstance(word_id, str):
                continue
            if self.words[word_id].lower() in QUESTION_WORDS[language]:
                return True
            if self.words[word_id].lower() == "if":
                if len(list(self.children(node))) > 1:  # if - else
                    return False
                else:
                    if any(isinstance(n, OIAWordsNode) for n, l in self.parents(node)):
                        return True
        return False

    #
    # def visualize(self, simple=False, filename=None):
    #     """
    #     return the dot string of current graph
    #     :return:
    #     """
    #
    #     dot_string = StringIO()
    #
    #     dot_string.write("strict digraph {\n")
    #
    #     node2index = dict()
    #     for index, node_id in enumerate(self.g.nodes()):
    #         node = self.get_node(node_id)
    #
    #         node_text = self.node_label(node, not simple)
    #
    #
    #         node2index[node.ID] = index
    #
    #         node_text = node_text.replace("\"", "\\\"")
    #         node_text = node_text.replace("\'", "\\\'")
    #         # logger.error(node_text)
    #
    #         vis_node_label = '{0}\t[label="{1}", shape={2}, style=filled, fillcolor={3}]; \n'.format(
    #             index, node_text + " @" + str(index), shape, fillcolor
    #         )
    #
    #         dot_string.write(vis_node_label)
    #         # if simple:
    #         #     g.add_node(id2index[node_id], label=node_text, shape=shape)
    #         # else:
    #         #     g.add_node(node_id, label=node_text, shape=shape)
    #
    #     for s, e in self.g.edges():
    #         edge = self.g[s][e]["Edge"]
    #
    #         edge_label = self.edge_label(edge, not simple)
    #
    #         s = node2index[s]
    #         e = node2index[e]
    #
    #         dot_string.write('{0}\t->\t{1}\t[label="{2}"];\n'.format(
    #             s, e, edge_label
    #         ))
    #
    #     dot_string.write("}\n")
    #
    #     dot_string = dot_string.getvalue()
    #     try:
    #
    #         g = nx.DiGraph(nx.drawing.nx_pydot.read_dot(StringIO(dot_string)))
    #     except Exception as e:
    #         logger.error("Dot Strings")
    #         logger.error(str(dot_string))
    #         with open("error.dot", "w") as f:
    #             f.write(dot_string)
    #         raise
    #
    #     from networkx.drawing.nx_agraph import to_agraph
    #
    #     A = to_agraph(g)
    #
    #     if filename:
    #         # dot_file_name = os.path.basename(filename) + ".dot"
    #         # with open(dot_file_name, "w") as f:
    #         #     f.write(A.to_string())
    #         try:
    #             A.draw(filename, prog="dot")
    #         except Exception as e:
    #             with open("error.dot", "w") as f:
    #                 f.write(dot_string)
    #
    #     return dot_string
    #
    # def dump_to_dict(self):
    #     """TODO: add doc string
    # """
    #     return nx.to_dict_of_dicts(self.g)
    #
    # def build_from_dict(self, dict):
    #     """TODO: add doc string
    # """
    #     self.g = nx.from_dict_of_dicts(dict)


class OIAGraphVisualizer(GraphVisualizer):
    """
    OIAVisualizer
    """

    def __init__(self, debug=False):

        self.debug = debug


    def escape(self, node_text):
        """

        @param node_text:
        @return:
        """
        special_tokens = '{}<>"'

        for token in special_tokens:
            node_text = node_text.replace(token, "\\" + token)

        return node_text

    def node_label(self, graph, node, *args, **kwargs):
        """

        :param node:
        :param dep_graph:
        :return:
        """
        components = []
        components.append(str(node.ID))
        node_text = self.escape(graph.node_text(node))
        components.append(node_text)

        if isinstance(node, OIAWordsNode):
            span_str = self.escape(str(tuple(node.readable_spans)))
            components.append(span_str)

        label = "{0}".format("|".join(components))

        if self.debug and node.contexts:

            label = "{{{0}}}".format("|".join([label, "\n".join(node.contexts)]))

        return label

    def node_style(self, graph, node, *args, **kwargs):
        """

        @param node:
        @return:

        """
        style = {}

        if graph.is_predicate_node(node):
            style['shape']  = "record"
            style['fillcolor'] = "blue"
        elif graph.is_function_node(node):
            style['shape']  = "record"
            style['fillcolor'] = "red"
        else:
            style['shape'] = "record"
            style['fillcolor'] = "grey"

        return style


    def edge_label(self, graph, edge, *args, **kwargs):
        """

        @param edge:
        @param debug:
        @return:
        """

        edge_label = edge.label

        if self.debug and edge.contexts:
            edge_label = "{{{0}}}".format("|".join([edge_label, "\n".join(edge.contexts)]))

        return edge_label

    def edge_style(self, graph, edge, *args, **kwargs):
        """

        @param node:
        @return:

        """
        style = {}


        return style

        



