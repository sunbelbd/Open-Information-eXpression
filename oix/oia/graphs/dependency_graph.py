# -*- coding: UTF-8 -*-
"""
dependency graph
"""
import copy
import inspect
import re
import traceback
import uuid
from collections import OrderedDict
import itertools
from networkx.algorithms.isomorphism import DiGraphMatcher, MultiDiGraphMatcher
from loguru import logger

from uda.structure.graph.graph import Node, Edge, DirectedGraph
from uda.structure.graph.visualizer import GraphVisualizer

UD_FIELDS = ['ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC']


class DependencyGraphNode(Node):
    """
    DependencyGraphNode
    """

    def __init__(self, **kwargs):

        super().__init__()
        for x in kwargs:
            if x not in UD_FIELDS and x != "LOC":
                raise Exception("Unknown fields")

        self._ID = kwargs["ID"] if "ID" in kwargs else None
        #: Word index, integer starting at 1 for each new sentence; may be a range for multiword
        # tokens; may be a decimal number for empty nodes (decimal numbers can be lower than 1 but must be greater
        # than 0).
        self.FORM = kwargs["FORM"] if "FORM" in kwargs else None
        #: Word form or punctuation symbol.
        self.LEMMA = kwargs["LEMMA"] if "LEMMA" in kwargs else self.FORM
        #: Lemma or stem of word form.
        self.UPOS = kwargs["UPOS"] if "UPOS" in kwargs else None
        #: Universal part-of-speech tag.
        self.XPOS = kwargs["XPOS"] if "XPOS" in kwargs else None
        #: Language-specific part-of-speech tag; underscore if not available.
        self.FEATS = kwargs["FEATS"] if "FEATS" in kwargs else dict()
        # : List of morphological features from the universal feature inventory or from a defined
        # language-specific extension; underscore if not available.
        self.HEAD = kwargs["HEAD"] if "HEAD" in kwargs else None
        #: Head of the current word, which is either a value of ID or zero (0).
        self.DEPREL = kwargs["DEPREL"] if "DEPREL" in kwargs else None
        #: Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined
        # language-specific subtype of one.
        self.DEPS = kwargs["DEPS"] if "DEPS" in kwargs else None
        #: Enhanced dependency graph in the form of a list of head-deprel pairs.
        self.MISC = kwargs["MISC"] if "MISC" in kwargs else None
        # : Any other annotation.

        self.LOC = kwargs["LOC"] if "LOC" in kwargs else None

        self.aux = False  # for added aux node

        self.contexts = list()

    @property
    def ID(self):
        """

        :return:
        :rtype:
        """

        return self._ID

    @ID.setter
    def ID(self, id):
        """

        :param id:
        :type id:
        :return:
        :rtype:
        """
        self._ID = id

    @property
    def position(self):
        """

        @return:
        @rtype:
        """
        return [self.LOC]

    def set_pos(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        self.UPOS = kwargs["UPOS"] if "UPOS" in kwargs else None
        self.XPOS = kwargs["XPOS"] if "XPOS" in kwargs else None

    @staticmethod
    def from_ltp(word):
        """

        :param word:
        :return:
        """

    @staticmethod
    def from_conll(line):
        """
        Returns a Word named tuple from the given line; the latter is expected
            to be a [] of strings. If the line does not define a word with an
            integer ID, the method returns None.

            Raises a ValueError or an AssertionError if the line does not conform
            to the format specified by the UD version in self.ud_version.

            Helper for self.gen_sentences.
        :param line_in_conll:
        :return:
        """

        assert len(line) == 10 and all([item for item in line]), line

        info = dict(zip(UD_FIELDS, line))

        #        if info['ID'].isdigit():  # id
        #            info['ID'] = int(info['ID'])
        #        else:
        #            assert all([c.isdigit() or c in ('-', '.') for c in info['ID']])

        # assert line[3] in self.POS_TAGS or line[3] == '_'  # upostag

        if info['FEATS'] == '_':  # feats
            info['FEATS'] = {}
        else:
            info['FEATS'] = {key: frozenset(value.split(','))
                             for key, value in map(lambda x: x.split('='), info['FEATS'].split('|'))}

        if info['HEAD'] != '_':  # head
            info['HEAD'] = info['HEAD']

        return DependencyGraphNode(**info)

    def __str__(self):
        """

        :return:
        """
        fields = ['ID', 'FORM', 'UPOS', 'FEATS', 'DEPS', 'LOC']
        return "\t".join(field + "=" + str(getattr(self, field)) for field in fields)

    def __eq__(self, another):
        """

        :param another:
        :return:
        """
        return hasattr(another, 'ID') and self.ID == another.ID

    def __hash__(self):
        """

        :return:
        """
        return hash(self.ID)

    def copy_from(self, node):
        """

        :param node:
        :return:
        """

        self.ID = node.ID if node.ID else self.ID

        self.FORM = node.FORM if node.FORM else self.FORM

        self.LEMMA = node.LEMMA if node.LEMMA else self.LEMMA

        #: Lemma or stem of word form.
        self.UPOS = node.UPOS if node.UPOS else self.UPOS
        #: Universal part-of-speech tag.
        self.XPOS = node.XPOS if node.XPOS else self.XPOS
        #: Language-specific part-of-speech tag; underscore if not available.
        self.FEATS = node.FEATS if node.FEATS else self.FEATS
        # : List of morphological features from the universal feature inventory or from a defined
        # language-specific extension; underscore if not available.
        self.HEAD = node.HEAD if node.HEAD else self.HEAD
        #: Head of the current word, which is either a value of ID or zero (0).
        self.DEPREL = node.DEPREL if node.DEPREL else self.DEPREL
        #: Universal dependency relation to the HEAD (root iff HEAD = 0) or a defined
        # language-specific subtype of one.
        self.DEPS = node.DEPS if node.DEPS else self.DEPS
        #: Enhanced dependency graph in the form of a list of head-deprel pairs.
        self.MISC = node.MISC if node.MISC else self.MISC
        # : Any other annotation.

        self.LOC = node.LOC if node.LOC else self.LOC

        self.aux = node.aux


class DependencyGraphSuperNode(DependencyGraphNode):
    """TODO: add doc string
    """
    def __init__(self, nodes, is_conj=False, **kwargs):

        # if any(x in kwargs for x in {"ID", "FORM", "LEMMA"}):
        #    raise Exception("ID, FORM, LEMMA should not be assigned manually")

        self.nodes = []
        for node in nodes:
            if isinstance(node, DependencyGraphSuperNode):
                self.nodes.extend(node.nodes)
            else:
                self.nodes.append(node)

        if all([isinstance(n, DependencyGraphNode) for n in self.nodes]):
            self.nodes = list(set(self.nodes))
            try:
                self.nodes.sort(key=lambda x: x.LOC)
            except Exception as e:
                logger.debug("Error in create Super Node ")
                for node in self.nodes:
                    logger.debug(node)
                raise

        self.is_conj = is_conj

        if "ID" not in kwargs:
            kwargs["ID"] = " ".join([x.ID if isinstance(x, DependencyGraphNode) else x for x in self.nodes])

        if "FORM" not in kwargs:
            kwargs["FORM"] = " ".join([x.FORM if isinstance(x, DependencyGraphNode) else x for x in self.nodes])

        if "LEMMA" not in kwargs:
            kwargs["LEMMA"] = " ".join([x.LEMMA if isinstance(x, DependencyGraphNode) else x for x in self.nodes])

        self.position_ = []
        for x in self.nodes:
            if isinstance(x, DependencyGraphNode):
                self.position_.extend(x.position)
            else:
                self.position_.append(x)

        super().__init__(**kwargs)

    @property
    def position(self):
        """

        @return:
        @rtype:
        """

        return self.position_


import networkx as nx


def position(node):
    """

    :param node:
    :return:
    """
    if "_" in node.ID or "-" in node.ID:
        return None

    if "." in node.ID:
        node_pos = map(int, node.ID.split("."))
    else:
        node_pos = (int(node.ID),)

    return node_pos


def in_interval(node, low, high):
    """

    :param node:
    :param low:
    :param high:
    :return:
    """

    if not node:
        return False

    result = True
    if low is not None:
        result = result and node.LOC > low.LOC
    if high is not None:
        result = result and node.LOC < high.LOC

    return result


class DependencyGraphEdge(Edge):
    """
    a set of relations between a pair of nodes for multiple edges.
    behaves like a single relation (that is, a string)
    for code compatability
    """

    def __init__(self):
        super().__init__()
        self.rels = set()
        self.contexts = []

    def startswith(self, prefix):
        """

        :param x:
        :return:
        """
        return any(x.startswith(prefix) for x in self.rels)


    def endswith(self, prefix):
        """

        :param x:
        :return:
        """
        return any(x.endswith(prefix) for x in self.rels)

    def values(self):
        """

        :return:
        """
        return [x.split(":")[1] for x in self.rels if ":" in x]

    def __len__(self):
        """

        :return:
        """
        return len(self.rels)

    def __contains__(self, item):
        """

        :param item:
        :return:
        """
        return any(item in x for x in self.rels)

    def __iter__(self):
        """

        :return:
        """
        return (x for x in self.rels)

    def __eq__(self, other):
        """

        :param other:
        :return:
        """

        if isinstance(other, str):
            return any(x == other for x in self.rels)
        elif isinstance(other, DependencyGraphEdge):
            return set(self.rels).intersection(other.rels)

    def __str__(self):
        """

        :return:
        """
        return "|".join(self.rels)

    def intersect(self, other):
        """

        :param other:
        :return:
        """
        return set(self.rels).intersection(set(other))

    def __bool__(self):
        """

        :return:
        """
        return len(self.rels) > 0

    def remove(self, rel):
        """

        :param rel:
        :return:
        """
        try:
            self.rels.remove(rel)
        except Exception as e:

            return


class DependencyGraph(DirectedGraph):
    """
    Dependency graph
    """

    def __init__(self):

        super().__init__()

        self.context_hook = lambda: None

        self.enhanced = False

    def set_context_hook(self, hook):
        """

        :param hook:
        :return:
        """
        self.context_hook = hook

    @staticmethod
    def from_sentence(sentence, stanza_pipeline):
        """
        Convert natural language sentence and its stanford_nlp result to Dependency Graph data structure.

        :param sentence:
        :param stanford_nlp:
        :return:
        """
        doc = stanza_pipeline(sentence)
        dep_graphs = []

        if len(doc.sentences) > 1:
            logger.warning("Multiple sentences found")
            logger.warning(sentence)
            raise Exception("Multiple sentences")

        for sent in doc.sentences:

            dep_graph = DependencyGraph()
            nodes = []
            root = DependencyGraphNode(ID='0', FORM='\xa0', LEMMA='\xa0', UPOS='ROOT', LOC=-1)
            dep_graph.add_node(root)
            for ind, word in enumerate(sent.words):
                node_dict = dict()
                node_dict['ID'] = str(word.id)
                node_dict['FORM'] = word.text
                node_dict['LEMMA'] = word.lemma if word.lemma is not None else '_'
                node_dict['UPOS'] = word.upos if word.upos is not None else '_'
                node_dict['XPOS'] = word.xpos if word.xpos is not None else '_'
                # node_dict['FEATS'] = word.feats if word.feats is not None else {}
                node_dict['FEATS'] = {key: frozenset(value.split(','))
                                      for key, value in map(lambda x: x.split('='), word.feats.split(
                        '|'))} if word.feats is not None and word.feats != '_' else {}
                node_dict['HEAD'] = str(word.head) if word.head is not None else '_'
                node_dict['DEPREL'] = word.deprel if word.deprel is not None else '_'
                node_dict['LOC'] = ind
                new_node = DependencyGraphNode(**node_dict)
                dep_graph.add_node(new_node)
                nodes.append(new_node)

            for node in nodes:
                if node.DEPREL is not None:
                    head_node = dep_graph.get_node(node.HEAD)
                    if head_node is None:
                        continue
                    dep_graph.add_dependency(head_node, node, node.DEPREL)

            dep_graphs.append(dep_graph)

        if len(dep_graphs) > 1:
            raise Exception("multiple graph found")

        return dep_graphs[0]

    @staticmethod
    def from_ddparser(ddp_result):
        """
        Convert ddparser result to Dependency Graph data structure.

        :param ddp_result:
            [{'word': ['百度', '是', '一家', '高科技', '公司'], 'postag': ['ORG', 'v', 'm', 'n', 'n'], 'head': [2, 0, 5, 5, 2],
            'deprel': ['SBV', 'HED', 'ATT', 'ATT', 'VOB'], 'prob': [1.0, 1.0, 1.0, 1.0, 1.0]}]
        :return:
        """
        dep_graph = DependencyGraph()

        # print(ddp_result)

        words = ddp_result["word"]
        postags = ddp_result["postag"]
        heads = ddp_result["head"]
        deprels = ddp_result["deprel"]

        nodes = []
        root = DependencyGraphNode(ID='0', FORM='\xa0', LEMMA='\xa0', UPOS='ROOT', LOC=-1)
        nodes.append(root)

        index = 0
        for word in words:

            index += 1

            if isinstance(word, str):
                word = word.strip()
                if not word:
                    continue
            else:
                raise Exception("Unknown Word Type.")

            node = DependencyGraphNode(ID=str(index), FORM=word, LEMMA=word, UPOS=postags[index - 1], XPOS=postags[index - 1],
                                       HEAD=str(heads[index - 1]), DEPREL=deprels[index - 1], LOC=str(index - 1))
            # print(node.__str__())
            nodes.append(node)

        dep_graph.add_nodes(nodes)

        for node in nodes:
            if node.DEPREL is not None and node.UPOS != 'ROOT':
                head_node = dep_graph.get_node(str(node.HEAD))
                if head_node is None:
                    continue
                dep_graph.add_dependency(head_node, node, node.DEPREL)

        return dep_graph

    @staticmethod
    def from_ltp(ltp_result):
        """
        Convert ltp parser result to Dependency Graph data structure.

        :param ltp_result:
        :return:
        """
        dep_graph = DependencyGraph()
        # sdp_graph = DependencyGraph()

        words = ltp_result["seg"][0]
        postags = ltp_result["pos"][0]
        # ner = ltp_result["ner"][0]
        # srl = ltp_result["srl"][0]
        dep = ltp_result["dep"][0]
        # sdp = ltp_result["sdp"][0]
        # heads = ltp_result["heads"][0]
        # relations = ltp_result["relations"][0]

        nodes = []
        # sdp_nodes = []

        root = DependencyGraphNode(ID='0', FORM='\xa0', LEMMA='\xa0', UPOS='ROOT', LOC=-1)
        nodes.append(root)
        # sdp_nodes.append(root)

        index = 0
        for word in words:

            index += 1

            if isinstance(word, str):
                word = word.strip()
                if not word:
                    continue
            else:
                raise Exception("Unknown word type")

            head_id = 0
            rel = None

            for relation in dep:
                current_id = relation[0]
                if current_id == index:
                    head_id = relation[1]
                    rel = relation[2]
                    break
                # else:
                #     logger.error("node {0}, {1} does not have relation.".format(index, words[index-1]))

            node = DependencyGraphNode(ID=str(index), FORM=word, LEMMA=word, UPOS=postags[index - 1],
                                       XPOS=postags[index - 1], HEAD=str(head_id), DEPREL=rel,
                                       LOC=str(index - 1))
            nodes.append(node)

            # sdp_pairs = []
            # for relation in sdp:
            #     tail = relation[0]
            #     if int(tail) == index:
            #         sdp_pairs.append(relation)
            #
            # sdp_node = DependencyGraphNode(ID=str(index), FORM=word, LEMMA=word, UPOS=postags[index - 1],
            #                                XPOS=postags[index - 1], DEPS=sdp_pairs, LOC=str(index - 1))
            # sdp_nodes.append(sdp_node)

        dep_graph.add_nodes(nodes)
        # sdp_graph.add_nodes(sdp_nodes)

        for node in nodes:
            if node.DEPREL is not None and node.UPOS != 'ROOT':
                head_node = dep_graph.get_node(node.HEAD)
                if head_node is None:
                    continue
                dep_graph.add_dependency(head_node, node, node.DEPREL)

        # for node in sdp_nodes:
        #     if node.DEPS is not None and node.UPOS != 'ROOT':
        #         for relation in node.DEPS:
        #             head_node = sdp_graph.get_node(relation[1])
        #             sdp_graph.add_dependency(head_node, node, relation[2])

        return dep_graph

    @staticmethod
    def from_conll(sentence_in_conll, need_root=True, enhanced=False):
        """

        :param sentence_in_conll:
        :return:
        """

        graph = DependencyGraph()

        if isinstance(sentence_in_conll, str):
            lines = sentence_in_conll.split('\n')
        elif isinstance(sentence_in_conll, list):
            lines = sentence_in_conll
        else:
            raise Exception("Unknown input type")

        nodes = []
        for line in lines:

            if isinstance(line, str):
                line = line.strip()

                if not line or line[0] == "#":
                    continue
                line = line.split("\t")

            if not isinstance(line, list):
                raise Exception("Unknown line type")

            nodes.append(DependencyGraphNode.from_conll(line))

        if need_root:
            root = DependencyGraphNode(ID='0', FORM='\xa0', LEMMA='\xa0', UPOS='ROOT', LOC=-1)
            graph.add_node(root)

        for idx, node in enumerate(nodes):
            # if type(node.ID) is int:
            node.LOC = idx
            graph.add_node(node)
            # else:
            #    raise Exception("unknown node id {0}".format(node.ID))

        if enhanced:
            for node in nodes:
                for head_deps in node.DEPS.split("|"):
                    if ":" in head_deps:
                        head, deps = head_deps.split(":", 1)
                        head_node = graph.get_node(head)
                        graph.add_dependency(head_node, node, deps)
        else:
            for node in nodes:
                if node.DEPREL is not None:
                    head_node = graph.get_node(node.HEAD)
                    if head_node is None:
                        continue
                    graph.add_dependency(head_node, node, node.DEPREL)

        if enhanced:
            graph.enhanced = True

        return graph

    def create_node(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        node = DependencyGraphNode(**kwargs)
        self.add_node(node)

        return node

    def add_node(self, node, reuse_id=True):
        """

        :param node:
        :return:
        """
        # logger.warning("add node with ID: {0} of type {1}".format(node.ID, type(node.ID)))
        if not node.ID:
            node.ID = str(uuid.uuid4())

        context = self.context_hook()
        if context:
            node.contexts.extend(context)

        return super().add_node(node, reuse_id=reuse_id)

    def add_nodes(self, nodes):
        """

        :param nodes:
        :return:
        """
        for node in nodes:
            self.add_node(node)

    def nodes_num(self):
        """

        :return:
        """
        return self.g.number_of_nodes()

    def remove_node(self, node):
        """

        :param node:
        :return:
        """

        if self.g.has_node(str(node.ID)):
            self.g.remove_node(node.ID)
            self.context_hook()


    def get_node(self, node_id):
        """

        :param node_id: must be a string!!!!
        :return:
        """
        try:
            # for node in self.nodes():
            #     if node.LOC == int(node_id):
            #         return node
            return super().get_node(node_id)
        except:
            logger.warning("Node does not exist with id {}.".format(node_id))

            return None

    def get_node_by_loc(self, loc):
        """

        :param loc:
        :return:
        """
        for node in self.nodes():
            if node.LOC == loc:
                return node

    def get_node_by_spans(self, spans):
        """

        :param spans:
        :return:
        """

        def span2position(spans):
            """

            @param spans:
            @type spans:
            @return:
            @rtype:
            """
            position = []
            assert isinstance(spans, list) or isinstance(spans, tuple)

            for span in spans:
                if isinstance(span, int):
                    position.append(span)
                elif isinstance(span, str):
                    position.append(span)
                elif isinstance(span, list) or isinstance(span, tuple):
                    start, end = span
                    for i in range(start, end + 1):
                        position.append(i)
                else:
                    raise Exception("unknow span type: {}".format(type(spans)))

            return position

        positions = set(span2position(spans))

        #logger.debug("position = {}".format(position))
        #for node in self.nodes():
        #    logger.debug("node pos = {}".format(node.position))

        matched = [node for node in self.nodes() if all(x in positions for x in node.position)]

        if len(matched) == 1:
            return matched[0]
        elif len(matched) == 0:
            logger.debug("No node found for spans {0}".format(spans))
            return []
        else:
            logger.debug("Multiple node found for spans {0}".format(spans))
            return matched


    def nodes(self, filter=None):
        """

        :return:
        """

        for node_id in self.g.nodes:
            node = self.get_node(str(node_id))
            if not filter or filter(node):
                yield node

    def origin_nodes(self):
        """

        @return:
        @rtype:
        """
        for node in self.nodes():

            if isinstance(node, DependencyGraphSuperNode):
                for origin_node in node.nodes:
                    if isinstance(origin_node, DependencyGraphNode) and not origin_node.aux:
                        yield origin_node
            elif isinstance(node, DependencyGraphNode):
                if not node.aux:
                    yield node

            else:
                raise Exception("unknown node type")

    def get_dependency(self, node1, node2):
        """

        :param node1:
        :param node2:
        :return:
        """
        try:
            return super().get_edge(node1, node2)
        except:
            return DependencyGraphEdge()


    def has_node(self, node):
        """

        :param node:
        :return:
        """
        if not isinstance(node, DependencyGraphNode) and not isinstance(node, DependencyGraphSuperNode):
            return False
        node_id = node.ID
        return self.g.has_node(node_id)

    def get_context_dependencies(self, node):
        """

        :param node:
        :return:
        """
        if not self.has_node(node):
            raise Exception("Graph does not have node.")

        prior_node = self.get_node(str(node.HEAD))
        if prior_node is None:
            print(node.ID, node.LEMMA)
            print(node.HEAD)
            raise Exception("no prior node")
        latter_node_dependencies = []
        for n in self.nodes():
            if n.HEAD == node.ID:
                latter_node_dependencies.append(self.get_dependency(node, n))

        return {"prior": self.get_dependency(prior_node, node),
                "latter": latter_node_dependencies}

    def dependencies(self):
        """

        :return:
        """
        for node1_id, node2_id in self.g.edges():
            node1 = self.get_node(str(node1_id))
            node2 = self.get_node(str(node2_id))
            yield node1, node2, self.get_dependency(node1, node2)

    def connected_components(self):
        """

        :return:
        """
        components = nx.algorithms.components.weakly_connected_components(self.g)

        for component in components:
            yield [self.get_node(str(x)) for x in component]

    def add_dependency(self, source, target, rel):
        """

        :param node1:
        :param node2:
        :param rel:
        :return:
        """
        edge = self.get_dependency(source, target)

        if isinstance(rel, DependencyGraphEdge):
            edge.rels.update(rel.rels)
        elif isinstance(rel, set):
            edge.rels.update(rel)
        else:
            edge.rels.add(rel)

        context = self.context_hook()
        if context:
            edge.contexts.extend(context)

        self.g.add_edge(source.ID, target.ID, Edge=edge)

    def remove_dependency(self, source, target, rel=None):
        """

        :param source:
        :param target:
        :return:
        """
        self.context_hook()
        if self.g.has_edge(source.ID, target.ID):
            if not rel:
                self.g.remove_edge(source.ID, target.ID)
            else:
                dep = self.get_dependency(source, target)
                dep.remove(rel)
                if len(dep) == 0:
                    self.g.remove_edge(source.ID, target.ID)

    def set_dependency(self, source, target, dep):
        """

        :param source:
        :param target:
        :param dep:
        :return:
        """
        self.remove_dependency(source, target)
        self.add_dependency(source, target, dep)

    def children(self, node, filter=None):
        """

        :param node:
        :return:
        """
        for child_id in self.g.successors(node.ID):

            child = self.get_node(child_id)
            rel = self.get_dependency(node, child)

            if not filter or filter(child, rel):
                yield child, rel

    def parents(self, node, filter=None):
        """

        :param node:
        :return:
        """
        # if node not in self.g.nodes:
        #     print('%s node does not exist!!!!!' % (node.ID))
        #     for n in self.g.nodes:
        #         print(n)
        for parent_id in self.g.predecessors(node.ID):

            parent = self.get_node(parent_id)
            rel = self.get_dependency(parent, node)

            if not filter or filter(parent, rel):
                yield parent, rel

    def offsprings(self, node, filter=None):
        """

        :param node:
        :return:
        """

        for node_id in nx.dfs_preorder_nodes(self.g, node.ID):
            node = self.get_node(node_id)
            if not filter or filter(node):
                yield self.get_node(node_id)

    def subgraph(self, nodes):
        """

        :param nodes:
        :return:
        """
        node_ids = [n.ID if isinstance(n, DependencyGraphNode) else n for n in nodes]

        subgraph = self.g.subgraph(node_ids).copy()

        result = DependencyGraph()
        result.graph = subgraph

        return result

    def has_path(self, node1, node2):
        """

        :param node1:
        :param node2:
        :return:
        """
        return nx.algorithms.shortest_paths.has_path(self.g, node1.ID, node2.ID)

    def is_connected(self):
        """

        :return:
        """
        return nx.algorithms.components.is_weakly_connected(self.g)

    def copy(self):
        """

        :return:
        """
        import copy
        copied = copy.deepcopy(self)
        return copied

    def match(self, pattern):
        """

        :param subgraph:
        :return:
        """

        def node_match(node, pattern_node):
            """

            :param node:
            :param pattern_node:
            :return:
            """
            node = node["Node"]
            pattern_node = pattern_node["Node"]

            result = True
            fields = ['FORM', 'LEMMA', 'UPOS', 'XPOS', 'HEAD', 'DEPREL', 'DEPS', 'MISC']
            for field in fields:
                if getattr(pattern_node, field) is not None:
                    if getattr(node, field) is None:
                        result = False
                    else:
                        pattern_field_value = getattr(pattern_node, field)
                        instance_field_value = getattr(node, field)
                        if not any(re.match(pattern_field_value, x) for x in instance_field_value.split("|")):
                            result = False

            if pattern_node.FEATS:
                for key, value in pattern_node.FEATS.items():
                    if key not in node.FEATS or value not in node.FEATS[key]:
                        result = False

            # print("Node Matched")
            # print("In node match", node.ID, pattern_node.ID, result)
            return result

        def edge_match(edges, pattern_edges):
            """

            :param edge:
            :param pattern_edge:
            :return:
            """

            edges = edges["Edge"].rels
            pattern_edges = pattern_edges["Edge"].rels

            result = False
            for edge, pattern_edge in itertools.product(edges, pattern_edges):
                match = re.match(pattern_edge, edge)
                if match:
                    result = True

            return result

        match_iter = DiGraphMatcher(self.g, pattern.g,
                                    node_match=node_match, edge_match=edge_match).subgraph_isomorphisms_iter()

        for result in match_iter:
            result = dict((pattern.get_node(v), self.get_node(k)) for k, v in result.items())

            yield result

    def __str__(self):
        """

        :return:
        """
        info = []

        for node1, node2, edge in self.g.edges.data():
            info.append((str(self.get_node(node1)), edge["Edge"], str(self.get_node(node2))))

        return "\n".join("\t".join(x) for x in info)

    def visualize(self, filename=None):
        """

        :return:
        """

        g = nx.DiGraph()

        for node_id in self.g.nodes():
            node = self.get_node(node_id)
            if node is None:
                logger.error("Cannot get node with ID {0}".format(node_id))

            if not node.contexts:
                g.add_node(node_id, label="{0}[{1}]({2})".format(
                    node.FORM, str(node.ID), node.UPOS))
            else:
                g.add_node(node_id, label="{0}[{1}]({2})\n@{3}".format(
                    node.FORM, str(node.ID), node.UPOS, "|".join(node.contexts)))

        for s, e in self.g.edges():
            node_s = self.get_node(s)
            node_e = self.get_node(e)
            edge = self.get_dependency(node_s, node_e)
            if not edge.contexts:
                g.add_edge(s, e, label="|".join(edge.rels))

            else:
                g.add_edge(s, e, label="|".join(edge.rels) + "\n@" + "|".join(edge.contexts))

        from networkx.drawing.nx_agraph import to_agraph

        A = to_agraph(g)

        if filename:
            A.draw(filename, prog="dot")

        return A.to_string()

    def replace_nodes(self, nodes, target_node):
        """
        replace the nodes with the target node
        if there is any edge connecting to the node in nodes other than head, raise exception
        :param nodes:
        :param head_node:
        :param target_node:
        :return:
        """
        actural_nodes = [n for n in nodes if isinstance(n, DependencyGraphNode)]
        if len(actural_nodes) == 1 and actural_nodes[0].ID == target_node.ID:
            # assert nodes[0] == head, nodes[0] + " " + head
            # assert head == target_node

            actural_nodes[0].copy_from(target_node)

            return

        self.add_node(target_node)

        nodes = set(actural_nodes)

        out_edges = []
        in_edges = []

        for node1_id, node2_id in self.g.edges():
            node1 = self.get_node(node1_id)
            node2 = self.get_node(node2_id)

            if node1 not in nodes and node2 not in nodes:
                continue
            elif node1 in nodes and node2 in nodes:
                continue
            elif node1 in nodes:
                # assert node1 == head
                rels = self.get_dependency(node1, node2)
                out_edges.append((node2, rels))

            elif node2 in nodes:
                # assert node2 == head
                rels = self.get_dependency(node1, node2)
                in_edges.append((node1, rels))

        for node, rels in out_edges:
            for rel in rels:
                self.add_dependency(target_node, node, rel)

        for node, rels in in_edges:
            for rel in rels:
                self.add_dependency(node, target_node, rel)

        for node in nodes:
            if isinstance(node, DependencyGraphNode):
                self.g.remove_node(node.ID)



class UDGraphVisualizer(GraphVisualizer):
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
        components.append(str(node.LOC))
        node_text = self.escape(node.FORM)
        components.append(node_text)
        components.append(node.UPOS)

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

        style['shape'] = "record"

        return style


    def edge_label(self, graph, edge, *args, **kwargs):
        """

        @param edge:
        @param debug:
        @return:
        """

        edge_label = "{0}".format("|".join(edge.rels))

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