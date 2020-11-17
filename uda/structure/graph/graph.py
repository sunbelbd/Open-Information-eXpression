"""
Graph data structure designed for graph2graph learning
"""

import networkx as nx


class Node(object):
    """
    Node
    """

    def __init__(self, ID=None):
        """

        :param id:
        :param object:
        :param rep:
        :param state:
        :param prob:
        """

        self.ID = ID

    @property
    def ID(self):
        """

        :return:
        :rtype:
        """

        pass

    @ID.setter
    def ID(self, id):
        """

        :param id:
        :type id:
        :return:
        :rtype:
        """
        pass


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


class Edge(object):
    """
    Edge
    """

    def __init__(self, start=None, end=None):
        """

        :param object:
        :param rep:
        :param state:
        :param prob:
        """

        self.start = start
        self.end = end


class Graph(object):
    """
    Graph
    """

    def __init__(self, g=None):
        """
        init graph
        """
        if g is None:
            self.g = nx.Graph()
        else:
            self.g = g

        self.node_id_base = 0

    def nodes(self):
        """

        :return:
        """

        for node in self.g.nodes:

            yield self.get_node(node)

    def edges(self):
        """

        :return:
        """

        for s, e in self.g.edges():
            edge = self.g[s][e]["Edge"]

            s_node = self.get_node(s)
            e_node = self.get_node(e)

            yield (s_node, edge, e_node)

    def has_node(self, node):
        """

        :param node:
        :return:
        """

        return node.ID in self.g

    def has_edge(self, node1, node2):
        """

        :param node1:
        :param node2:
        :return:
        """

        return node2.ID in self.g[node1.ID]

    def number_of_nodes(self):
        """

        :return:
        """

        return nx.number_of_nodes(self.g)

    def number_of_edges(self):
        """

        :return:
        """

        return nx.number_of_edges(self.g)


    def get_node(self, node_id):
        """

        :param node_id:
        :return:
        """

        return self.g.nodes[node_id]["Node"]

    def remove_node(self, node):
        """

        :param node:
        :return:
        """
        self.g.remove_node(node.ID)

    def remove_edge(self, edge):
        """

        :param node:
        :return:
        """
        self.g.remove_edge(edge.start, edge.end)

    def remove_edge_between(self, node1, node2):
        """

        :param node1:
        :type node1:
        :param node2:
        :type node2:
        :return:
        :rtype:
        """
        if self.g.has_edge(node1.ID, node2.ID):
            self.g.remove_edge(node1.ID, node2.ID)

    def get_edge(self, node1, node2):
        """

        :param node1_id:
        :param node2_id:
        :return:
        """

        if isinstance(node1, Node):
            node1 = node1.ID
        if isinstance(node2, Node):
            node2 = node2.ID
        """
        if type(node1) is not int:
            node1 = node1.ID
        if type(node2) is not int:
            node2 = node2.ID
        """

        try:
            edge = self.g[node1][node2]["Edge"]
        except KeyError as e:
            raise Exception("There is no edge between node {0} and {1}".format(node1, node2))

        return edge

    def add_node(self, n, reuse_id=False):
        """

        :param n:
        :param id:
        :return:
        """

        if reuse_id:
            node_id = n.ID
        else:
            node_id = self.node_id_base
            self.node_id_base += 1

        n.ID = node_id

        self.g.add_node(node_id, Node=n)

        return n

    def add_edge(self, ni, nj, e):
        """

        :param ni:
        :param eij:
        :param nj:
        :return:
        """

        if not isinstance(ni, Node):
            ni = self.get_node(ni)
        if not isinstance(nj, Node):
            nj = self.get_node(nj)

        e.start = ni.ID
        e.end = nj.ID

        self.g.add_edge(ni.ID, nj.ID, Edge=e)

    def neighbors(self, node):
        """

        :param ni:
        :return:
        """

        for nj in self.g[node.ID]:

            eij = self.g[node.ID][nj]["Edge"]

            yield eij, self.get_node(nj)

    def breadth_first_dag(self, start_node):
        """

        :return:
        """

        dag = DirectedGraph()

        for node in self.nodes():

            dag.add_node(node.copy(), reuse_id=True)

        edges = nx.bfs_edges(self.g, start_node.ID)
        orderd_nodes = [start_node.ID] + [v for u, v in edges]
        for i, u in enumerate(orderd_nodes):
            for j, v in enumerate(orderd_nodes):

                if j <= i:
                    continue
                node_u = self.get_node(u)
                node_v = self.get_node(v)

                if self.has_edge(node_u, node_v):
                    edge = self.get_edge(node_u, node_v).copy()
                    dag.add_edge(node_u, node_v, edge)
        assert self.number_of_nodes() == dag.number_of_nodes()
        assert self.number_of_edges() == dag.number_of_edges()

        return dag

    def breadth_first_tree(self, start_node):
        """

        :return:
        """

        dag = DirectedGraph()

        dag.add_node(start_node.copy(), reuse_id=True)

        edges = nx.bfs_edges(self.g, start_node.ID)

        def __get_or_copy_node(u):

            try:
                node_u = dag.get_node(u)
            except:
                node_u = self.get_node(u).copy()
                dag.add_node(node_u, reuse_id=True)
            return node_u

        for u, v in edges:
            node_u = __get_or_copy_node(u)
            node_v = __get_or_copy_node(v)

            edge = self.get_edge(u, v)
            dag.add_edge(node_u, node_v, edge)

        return dag

    def __copy__(self):
        """

        :return:
        """
        from copy import copy
        copied = type(self)()
        copied.g = self.g.copy()
        copied.node_id_base = self.node_id_base
        return copied

    def __deepcopy__(self, memodict={}):
        """

        :param memodict:
        :type memodict:
        :return:
        :rtype:
        """

        from copy import deepcopy

#        copied_g = type(self.g)()
#
        copied = type(self)()

        memodict[id(self)] = copied

        for node in self.nodes():
            copied.add_node(deepcopy(node), reuse_id=True)

        for (s_node, edge, e_node) in self.edges():
            copied.add_edge(s_node, e_node, deepcopy(edge))

        copied.node_id_base = self.node_id_base
        return copied


    def dual(self):
        """
        return the dual graph
        the dual graph is the graph with edges corresponding nodes and
        nodes corresponding edges
        """

        dual = Graph()

        edge_node_map = dict()

        for edge in self.edges():

            node = Node(value=edge.value)

            dual.add_node(node)

            edge_node_map[(edge.start, edge.end)] = node
            edge_node_map[(edge.end, edge.start)] = node

        for node in self.nodes():

            edges = list(self.g.edges(node.ID))

            # since the end node is added
            assert len(edges) >= 2, "Edge number should larger than 2 " \
                                    "since the end node is added"

            for idx1, (edge1_start, edge1_end) in enumerate(edges):

                for (edge2_start, edge2_end) in edges[idx1 + 1:]:

                    node1 = edge_node_map[(edge1_start, edge1_end)]
                    node2 = edge_node_map[(edge2_start, edge2_end)]

                    dual.add_edge(node1, node2, Edge(value=node.value))

        return dual

    #
    # def visualize(self, file_name=None):
    #     """
    #
    #     :return:
    #     """
    #
    #     visual_g = type(self.g)()
    #
    #     for node in self.nodes():
    #         visual_g.add_node(node.ID, label=self.node_label(node))
    #
    #     for node_s, edge, node_e in self.edges():
    #
    #         visual_g.add_edge(node_s.ID, node_e.ID, label=self.edge_label(edge))
    #
    #     from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
    #
    #     A = to_agraph(visual_g)
    #     if file_name:
    #         A.draw(file_name, prog="dot")
    #
    #     return A.to_string()



class DirectedGraph(Graph):
    """
    Directed Graph
    """

    def __init__(self, g=None):
        """

        :param edge_identifier:
        """

        if g is not None:
            assert(isinstance(g, nx.DiGraph))
        else:
            g = nx.DiGraph()

        super(DirectedGraph, self).__init__(g=g)

    def is_connected(self):
        """

        :return:
        """
        return nx.algorithms.components.is_weakly_connected(self.g)

    def is_leaf(self, node):
        if len(list(self.children(node))) == 0:
            return True
        return False

    def children(self, node):
        """

        :param node:
        :return:
        """
        for child_id in self.g.successors(node.ID):
            child = self.get_node(child_id)
            rel = self.get_edge(node, child)

            yield child, rel


    def offsprings(self, node, filter=None):
        """

        :param node:
        :return:
        """

        for node_id in nx.dfs_preorder_nodes(self.g, node.ID):
            node = self.get_node(node_id)
            if not filter or filter(node):
                yield self.get_node(node_id)

    def parents(self, node):
        """

        :param node:
        :return:
        """
        for parent_id in self.g.predecessors(node.ID):
            parent = self.get_node(parent_id)
            rel = self.get_edge(parent, node)

            yield parent, rel

    def topological_sort(self):
        """

        :return:
        """

        for id in nx.topological_sort(self.g):
            yield self.get_node(id)




def valid_alignment(choices):
    """

    :param choices:
    :return:
    """
    def _inner(i):
        if i == n:
            yield tuple(result)
            return
        for elt in sets[i] - seen:
            seen.add(elt)
            result[i] = elt
            for t in _inner(i + 1):
                yield t
            seen.remove(elt)

    sets = [set(seq) for seq in choices]
    n = len(sets)
    seen = set()
    result = [None] * n
    for t in _inner(0):
        yield t


def is_valid_topology_sort(dag, node_objs):
    """
    decide whether the order of nodes in dag2 is a valid topological sort order of dag1
    :param dag:
    :param pred_node_objs donot contain the start node:
    :return:
    """
    target_nodes = list(dag.nodes())
    target_node_objects = [n.object for n in target_nodes]

    choices = []
    for i, node_obj in enumerate(node_objs):
        cur_choice = []
        for j, target_node in enumerate(target_node_objects):
            if target_node == node_obj:
                cur_choice.append(j)

        if len(cur_choice) == 0:
            return False

        choices.append(cur_choice)

    for align in valid_alignment(choices):

        if len(set(align)) != len(align):
            continue

        node_ids = [target_nodes[i].ID for i in align]

        bad_align = False
        for id, node_id in enumerate(node_ids):

            if nx.descendants(dag.g, node_id).intersection(set(node_ids[:id])):
                bad_align = True
                break

            if nx.ancestors(dag.g, node_id).intersection(set(node_ids[id + 1:])):
                bad_align = True
                break

        if not bad_align:
            return True

    return False




def not_isomorphic(graph_a, graph_b):
    """

    :param graph_a:
    :param graph_b:
    :return:
    """

    return nx.faster_could_be_isomorphic(graph_a.g, graph_b.g)

