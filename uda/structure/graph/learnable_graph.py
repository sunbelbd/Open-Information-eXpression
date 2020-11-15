#!/usr/bin/python3
"""
graph tensors
"""
import sys
import torch
import numpy as np
import typing

import uda.tensor as T
from .graph import Graph, Node, Edge
from .graph import DirectedGraph
import networkx as nx

class LearnableElement(object):
    """
    LearnableElement
    """

    def __init__(self, value=None):
        self.value_ = value

    @property
    def value(self):
        return self.value_

    @value.setter
    def value(self, value_):
        """

        :param id:
        :type id:
        :return:
        :rtype:
        """
        self.value_ = value_



class LearnableNode(Node, LearnableElement):
    """
    LearnableNode
    """

    def __init__(self, ID=None, value=None):
        self.id = ID
        self.value_ = value

        Node.__init__(self, ID)
        LearnableElement.__init__(self, value)

    @property
    def ID(self):

        return self.id

    @ID.setter
    def ID(self, id):
        """

        :param id:
        :type id:
        :return:
        :rtype:
        """
        self.id = id



class LearnableEdge(Edge, LearnableElement):
    """
    Edge
    """

    def __init__(self, start=None, end=None, value=None):
        """

        :param object:
        :param rep:
        :param state:
        :param prob:
        """

        self.start = start
        self.end = end

        Edge.__init__(self, start, end)
        LearnableElement.__init__(self, value)


class LearnableStructure(object):
    """
    LearnableGraph
    """

    def node_types(self):
        """

        :return:
        :rtype:
        """
        raise NotImplementedError

    def adjmatrix(self):
        """

        :return:
        :rtype:
        """
        raise NotImplementedError

    def to_tensor(self):
        """

        :return:
        """
        node_types = self.node_types()
        a_in, a_out = self.adjmatrix()
        return node_types, a_in, a_out





class LearnableGraph(Graph, LearnableStructure):
    """
    Learnable Graph
    """

    def __init__(self, g=None):
        """

        :param edge_identifier:
        """
        Graph.__init__(self, g)
        LearnableStructure.__init__(self)

    def node_types(self):
        """

        :return:
        """

        sorted_nodes = sorted(list(self.nodes()), key=lambda x: x.ID)

        node_types = [x.value for x in sorted_nodes]

        return np.array(node_types, dtype=np.int32)

    def adjmatrix(self):
        """

        :return:
        """

        n_nodes = self.number_of_nodes()

        in_a = np.zeros([n_nodes, n_nodes], dtype=np.int32)
        out_a = np.zeros([n_nodes, n_nodes], dtype=np.int32)

        for u_id, v_id in self.g.edges:

            u = self.get_node(u_id)
            v = self.get_node(v_id)

            edge = self.get_edge(u, v)

            e_type = edge.value

            in_a[v_id][u_id] = e_type
            out_a[v_id][u_id] = e_type
            in_a[u_id][v_id] = e_type
            out_a[u_id][v_id] = e_type

        return (in_a, out_a)


    @staticmethod
    def from_tensor(node_types, edges_in, edges_out):
        """

        :param node_types:
        :type node_types:
        :param edges_in:
        :type edges_in:
        :param edges_out:
        :type edges_out:
        :return:
        :rtype:
        """
        raise NotImplementedError


class LearnableDirectedGraph(DirectedGraph, LearnableStructure):
    """
    LearnableDirectedGraph
    """

    def __init__(self, g=None):
        """

        :param edge_identifier:
        """

        super().__init__(g)

    def node_types(self):
        """

        :return:
        """
        sorted_nodes = list(self.topological_sort())

        node_types = [x.value for x in sorted_nodes]
        return np.array(node_types, dtype=np.int32)

    def adjmatrix(self):
        """

        :return:
        :rtype:
        """

        n_nodes = self.number_of_nodes()

        sorted_nodes = list(self.topological_sort())
        id_pos_map = dict((x.ID, i) for i, x in enumerate(sorted_nodes))

        in_a = np.zeros([n_nodes, n_nodes], dtype=np.int32)
        out_a = np.zeros([n_nodes, n_nodes], dtype=np.int32)

        for u_id, v_id in self.g.edges:
            u = self.get_node(u_id)
            v = self.get_node(v_id)

            edge = self.get_edge(u, v)

            e_type = edge.value

            pos_u = id_pos_map[u_id]
            pos_v = id_pos_map[v_id]

            assert pos_v > pos_u

            in_a[pos_v][pos_u] = e_type
            out_a[pos_u][pos_v] = e_type

        return (in_a, out_a)


    @staticmethod
    def from_tensor(node_types, edges_in, edges_out):
        """
        :param graph:
        :param node_types:
        :param edges_in:
        :param edges_out:
        :return:
        """
        node_num, node_num = edges_in.shape

        actual_node_num = node_num

        graph = LearnableDirectedGraph()

        for i in range(node_num):
            obj = node_types[i]
            node = LearnableNode(ID=i, value=obj)
            graph.add_node(node, reuse_id=True)

        for i in range(actual_node_num):
            for j in range(i + 1, actual_node_num):
                if edges_out[i][j] > 0:
                    node_i = graph.get_node(i)
                    node_j = graph.get_node(j)
                    graph.add_edge(node_i, node_j, e=LearnableEdge(value=edges_out[i][j]))

        return graph


def is_isomorphic(graph_a: typing.Union[LearnableGraph, LearnableDirectedGraph],
                  graph_b: typing.Union[LearnableGraph, LearnableDirectedGraph]):
    """

    :param source_g:
    :param pred_g:
    :return:
    """

    def __node_match(n1_attrib, n2_attrib):
        '''returns False if either does not have a color or if the colors do not match'''

        return n1_attrib['Node'].value == n2_attrib['Node'].value

    def __edge_match(n1_attrib, n2_attrib):
        '''returns False if either does not have a color or if the colors do not match'''
        return n1_attrib['Edge'].value == n2_attrib['Edge'].value


    return nx.is_isomorphic(graph_a.g, graph_b.g,
                            node_match=__node_match, edge_match=__edge_match)


class GraphBatch(object):
    """
    GraphTensorBatch
    """

    def __init__(self, node_obj, edge_in, edge_out):
        self.node_obj = T.Tensor(node_obj).long()
        self.edge_in = T.Tensor(edge_in).long()
        self.edge_out = T.Tensor(edge_out).long()

    @property
    def device(self):
        """

        :return:
        """

        return self.node_obj.device

    def to(self, device):
        """

        :param device:
        :type device:
        :return:
        :rtype:
        """

        self.node_obj = self.node_obj.to(device)
        self.edge_in = self.edge_in.to(device)
        self.edge_out = self.edge_out.to(device)

        return self 

    def batch_size(self):
        """

        :return:
        """
        return T.dynamic_size(self.node_obj)[0]

    def node_num(self):
        """

        :return:
        """
        return T.dynamic_size(self.node_obj)[1]

    def edge_voc_size(self):
        """

        :return:
        """

        return T.dynamic_size(self.edge_in)[-1]

    @staticmethod
    def from_graphs(graphs, edge_voc_size):
        """

        :param graphs:
        :return:
        """
        if all(isinstance(x, Graph) for x in graphs):
            graphs = [x.to_tensor(edge_voc_size) for x in graphs]

        assert all(len(x) == 3 for x in graphs)
        # print "graphs 0: ", graphs[0][1].shape
        # print "graphs 1: ", graphs[1][1].shape
        node_objs = np.stack([x[0] for x in graphs],
                             axis=0)
        edge_in = np.stack([x[1] for x in graphs], axis=0)
        edge_out = np.stack([x[2] for x in graphs], axis=0)

        graph_batch = GraphBatch(node_objs, edge_in, edge_out)

        return graph_batch

    def to_graphs(self, graph_class, directed=False):
        """

        :return:
        """

        node_obj = T.numpy(self.node_obj)
        edge_in = T.numpy(self.edge_in)
        edge_out = T.numpy(self.edge_out)

        graph = graph_class()

        return [graph.from_tensor(cur_node_obj, cur_edge_in, cur_edge_out)
                for cur_node_obj, cur_edge_in, cur_edge_out in zip(node_obj, edge_in, edge_out)]

    def out_degrees(self):
        """

        :return:
        """
        return T.sum(T.sum(self.edge_out, dim=-1), dim=-1)

    def in_degrees(self):
        """

        :return:
        """
        return T.sum(T.sum(self.edge_in, dim=-1), dim=-1)

    def node_types(self, node_ids):
        """

        :param node_ids:
        :return:
        """

        # assert T.static_size(node_ids)[0] == self.batch_size()

        return T.dimwise_gather(self.node_obj, (T.range(self.batch_size()), node_ids))

    def in_edges(self, node_ids):
        """

        :param node_ids:
        :return: batch, parent_id, edge_type, node_id
        """
        batch_size = T.dynamic_size(node_ids)[0]
        index = T.cast(
                    T.nonzero(
                        T.dimwise_gather(
                            self.edge_in,
                            (
                                T.cast(T.range(batch_size, self.device), "int64"),
                                node_ids
                            )
                        )
                    ),
                    "int64"
        )

        def _append_index():
            gathered_node_ids = T.gather(node_ids, 0, index[:, 0])
            return T.cat([index, T.view(gathered_node_ids,
                                            (T.numel(gathered_node_ids), 1))], dim=1)

        return T.if_else(T.numel(index) == 0,
                    lambda: index,
                    _append_index
                    )

    def out_edges(self, node_ids):
        """

        :param node_ids:
        :return:
        """
        batch_size = T.size(node_ids)[0]
        index = self.edge_out[np.arange(batch_size), node_ids].nonzero()

        gathered_node_ids = T.gather(T.Tensor(node_ids), 0,  index[:, 0])
        return T.cat([index, T.view(gathered_node_ids,
                                        (T.numel(gathered_node_ids), 1))], dim=1)

    def edge_label(self):

        """

        :param edge_bin:
        :return:
        """

        label = T.copy(self.edge_out)

        missing_edge = T.cast(T.nonzero(
                            T.equal(T.sum(label, dim=-1), 0)
                        ),
                        "int64"
                    )

        def _set_missing_label():
            zero_coord = T.cast(
                T.zeros((T.dynamic_size(missing_edge)[0], 1), missing_edge.device), 
                "int64")
            coords = T.cat([missing_edge, zero_coord], dim=-1)
            values = T.cast(
                T.ones((T.dynamic_size(coords)[0],), missing_edge.device), 
                label.dtype)

            update = T.sparse_to_full(coords, values, size=T.dynamic_size(label))

            return label + update

        label = T.if_else(T.numel(missing_edge) > 0,
                            _set_missing_label,
                            lambda: label)

        return label

    def non_parents(self, node_ids):
        """
        return the non parents nodes
        :param node_ids:
        :return:
        """
        batch_size = T.dynamic_size(node_ids)[0]
        index = T.cast(T.nonzero(

                        T.equal(
                            T.sum(
                                T.dimwise_gather(self.edge_in,
                                                   (T.cast(T.range(batch_size), "int64"),
                                                    node_ids)),
                                dim=-1
                            ),
                            0
                        )
                    ),
                    "int64"

        )

        gathered_node_ids = T.gather(node_ids, 0, index[:, 0])

        return T.cat([index, T.view(gathered_node_ids,
                                        (T.numel(gathered_node_ids), 1))],
                         dim=1)

    # def identical_nodes(self, node_ids):
    #     """
    #     return the nodes identical with node ids
    #     :param node_ids:
    #     :return:
    #     """
    #
    #     batch_size = self.batch_size()
    #     node_num = self.node_num()
    #     edge_type_num = self.edge_in.size()[-1]
    #
    #     cur_in_edges = self.edge_in[np.arange(batch_size), node_ids]  # shape = (batch_size, node_num, edge_type_num)
    #     rep_in_edges =cur_in_edges.unsqueeze(1).expand(batch_size, node_num, node_num, edge_type_num)
    #


def id_to_binary(id_array, voc):
    """

    :param id_array:
    :param voc:
    :return:
    """

    if isinstance(id_array, torch.autograd.Variable):
        id_array = id_array.data

    assert id_array.dim() == 1

    id_array = id_array.long()

    batch_size = id_array.numel()

    binary = T.zeros((batch_size, voc)).int()


    try:
        binary[np.arange(batch_size), id_array] = 1
    except Exception as e:

        print (id_array)
        raise e

    return binary

#
# class DynamicGraphBatch(object):
#     """
#     The graph batch in the learning procedure
#     """
#     def __init__(self):
#
#         self.nodes = []
#         self.edges = []
#
#         self.node_reps = []
#         self.edge_reps = []
#
#         self.node_states = []
#         self.edge_states = []
#
#         self.node_contexts = []
#         self.edge_contexts = []
#
#     def add_node(self, types, reps, states, contexts):
#         """
#
#         :param nodes:
#         :param reps:
#         :param states:
#         :param contexts:
#         :return:
#         """
#
#         self.nodes.append(types)
#         self.node_reps.append(reps)
#         self.node_states.append(states)
#         self.node_contexts.append(contexts)
#
#     def add_edge(self, i, j, types, reps=None, states=None):
#
#         """
#         Add an edge from i-th node to j-th node
#         :param i:
#         :param j:
#         :param types:
#         :param reps:
#         :param states:
#         :return:
#         """
#
#         self.edges.append((i, j, types))
#
#         # assert self.edge_num == i * (i - 1)/2 + j
#         self.edge_reps.append(reps)
#         self.edge_states.append(states)
#
#     def last_node(self):
#         """
#
#         :return:
#         """
#
#         return (self.nodes[-1],
#                 self.node_reps[-1],
#                 self.node_states[-1],
#                 self.node_contexts[-1])
#
#     def last_edge(self):
#         """
#
#         :return:
#         """
#         return (self.edge_reps[-1],
#                 self.edge_states[-1])
#
#     def node(self, i):
#         """
#
#         :param i:
#         :return:
#         """
#         return (self.nodes[i],
#                 self.node_reps[i],
#                 self.node_states[i],
#                 self.node_contexts[i])
#
#     def to_graph_tensor(self, edge_voc_size, with_rep=False):
#         """
#
#         :param edge_voc_size:
#         :return:
#         """
#
#         nodes = torch.stack(self.nodes, dim=1)
#
#         batch_size, node_num = nodes.size()
#
#         edge_in = T.Variable(torch.zeros((batch_size, node_num, node_num,
#                                              edge_voc_size + 2)))
#         edge_out = T.Variable(torch.zeros((batch_size, node_num, node_num,
#                                               edge_voc_size + 2)))
#
#         for i, j, edge in self.edges:
#
#             types_bin = id_to_binary(edge, edge_voc_size + 2)
#
#             # except for start node, all edge with type 0 will not be recorded as edge
#             types_bin[:, 0] = 0
#
#             edge_out[:, i, j, :] = types_bin
#             edge_in[:, j, i, :] = types_bin
#
#         if with_rep:
#
#             node_reps = torch.stack(self.node_reps, dim=1)
#
#             return nodes, edge_in, edge_out, node_reps
#         else:
#
#             return nodes, edge_in, edge_out


def build_from_tensor(graph, node_types, edges_in, edges_out):
    """

    :param graph:
    :param node_types:
    :param edges_in:
    :param edges_out:
    :return:
    """

    import numpy as np
    node_num, node_num, edge_type_num = edges_in.shape

    for i in range(node_num):
        obj = node_types[i]
        #
        # if env.scalar(obj) == node_type_num + 1:  # end node
        #     break

        node = Node(id=i, object=obj)
        graph.add_node(node, reuse_id=True)

    for i in range(node_num):

        for j in range(node_num):

            # if np.any(edges_in[i][j]):
            #     assert(np.sum(edges_in[i][j]) == 1)
            #     edge_obj = np.argmax(edges_in[i][j])
            #     assert(edges_in[i][j][edge_obj] == 1)
            #
            #     node_i = graph.get_node(i)
            #     node_j = graph.get_node(j)
            #
            #     graph.add_edge(node_j, node_i, e=Edge(object=edge_obj))

            if np.any(edges_out[i][j]):
                assert (np.sum(edges_out[i][j]) == 1)
                edge_obj = np.argmax(edges_out[i][j])
                assert (edges_out[i][j][edge_obj] == 1)

                node_i = graph.get_node(i)
                node_j = graph.get_node(j)

                graph.add_edge(node_i, node_j, e=Edge(object=edge_obj))

    return graph




def adjmatrix2d_to_3d(adjmatrix2d, edge_type_num):
    """
    Convert 2d matrix to 3d matrix
    Arguments:
        adjmatrix2d {[type]} -- [description]
        edge_type_num {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    import numpy as np
    # n_nodes = np.shape(adjmatrix2d)[0]
    n_nodes = adjmatrix2d.shape[0]
    adjmatrix3d = np.zeros([n_nodes, n_nodes, edge_type_num], dtype=np.int32)
    for i in range(n_nodes):
        for j in range(n_nodes):
            edge_type = adjmatrix2d[i][j]
            assert edge_type < edge_type_num
            if edge_type != 0:
                adjmatrix3d[i][j][edge_type] = 1
    return adjmatrix3d


def graphTensor2d_to_3d(graphTensor2d, edge_type_num):
    """"[summary]"

    [description]

    Arguments:
        graphTensor2d_to_3d {[type]} -- [description]
    """
    node_types, a_in, a_out = graphTensor2d
    a_in_3d = adjmatrix2d_to_3d(a_in, edge_type_num)
    a_out_3d = adjmatrix2d_to_3d(a_out, edge_type_num)
    return node_types, a_in_3d, a_out_3d


def is_exact_same_graph(graph1, graph2, edge_type_num):
    """
    Whether the two graph is exactly the same.
    Arguments:
        graph1 {[type]} -- [description]
        graph2 {[type]} -- [description]
    """

    import numpy as np
    g1_nodes, g1_a_in, g1_a_out = graph1.to_tensor(edge_type_num)
    g2_nodes, g2_a_in, g2_a_out = graph2.to_tensor(edge_type_num)

    node_equal = np.all(g1_nodes == g2_nodes)
    a_in_equal = np.all(g1_a_in == g2_a_in)
    a_out_equal = np.all(g1_a_out == g2_a_out)

    ans = node_equal and a_in_equal and a_out_equal
    return ans
