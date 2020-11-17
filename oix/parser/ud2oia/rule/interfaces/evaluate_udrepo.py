"""
evaluate
"""
import sys
import traceback

import click
import networkx as nx
from loguru import logger
import os

from oix.parser.ud2oia.rule.parser import ud2oia, sentence2oia
from oix.oia import standard
from oix.oia.graphs.oia_graph import OIAGraph, OIAGraphVisualizer
from uda.structure.graph.visualizer import make_pair_image


def get_udrepo(lang):
    """

    @param lang:
    @type lang:
    @return:
    @rtype:
    """

    standard.language = lang

    if lang == "en":
        from oix.data.en.ud.ud_repo import UDRepo

        ud_repo = UDRepo()
    else:
        raise Exception("UD dataset for language {} not found".format(lang))

    return ud_repo

def get_oiarepo(lang, path):
    """

    @param lang:
    @type lang:
    @return:
    @rtype:
    """
    standard.language = lang

    if lang == "en":
        from oix.data.en.oia.oia_repo import OIARepo

        oia_repo = OIARepo(path)
    else:
        raise Exception("oia dataset for language {} not found".format(lang))

    return oia_repo


def graph_match_metric(pred_graph: OIAGraph, truth_graph: OIAGraph):
    """

    :param predict:
    :param truth:
    :return:
    """

    pred_nodes = [pred_graph.node_text(n) for n in pred_graph.nodes()]
    true_nodes = [truth_graph.node_text(n) for n in truth_graph.nodes()]

    node_true_num = len(true_nodes)
    node_pred_num = len(pred_nodes)

    node_match_num = sum(node in true_nodes for node in pred_nodes)

    pred_edges = [(pred_graph.node_text(n1),
                   edge.label.strip("\" "),
                   pred_graph.node_text(n2))
                  for n1, edge, n2 in pred_graph.edges()]
    true_edges = [(truth_graph.node_text(n1),
                   edge.label.strip("\" "),
                   truth_graph.node_text(n2))
                  for n1, edge, n2 in truth_graph.edges()]

    logger.debug(pred_edges)
    logger.debug(true_edges)

    edge_true_num = len(true_edges)
    edge_pred_num = len(pred_edges)

    edge_match_num = sum(edge in true_edges for edge in pred_edges)

    exact_same = node_match_num == node_true_num == node_pred_num and \
                 edge_match_num == edge_true_num == edge_pred_num

    return (node_pred_num, node_true_num, node_match_num), \
           (edge_pred_num, edge_true_num, edge_match_num), exact_same


@click.command()
@click.argument("lang", type=click.Choice(["en"]))
@click.argument("input_path")
@click.argument("source", type=click.Choice(["train", "dev", "test"]))
@click.argument("output_path")
@click.option("--debug/--no-debug", default=False)
@click.option("--use_ud/--no-use_ud", default=True)
def evaluate(lang, input_path, source, output_path, debug, use_ud):
    """

    :param source:
    :return:
    """

    if not debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    ud_repo = get_udrepo(lang)
    oia_repo = get_oiarepo(lang, input_path)

    total_node_pred_num = 0
    total_node_true_num = 0
    total_node_match_num = 0
    total_edge_pred_num = 0
    total_edge_true_num = 0
    total_edge_match_num = 0
    total_exact_same = 0

    total_graph_num = 0
    total_empty_num = 0

    item_measure = []

    samples = getattr(ud_repo, source)

    logger.info("evaluation sample num = {0}".format(len(samples)))

    oia_visualizer = OIAGraphVisualizer()

    results = dict()

    for oia_data in oia_repo.all(source):


        ground_oia_graph = OIAGraph.parse(oia_data)

        uri = ground_oia_graph.meta['uri']

        # try:
        #     ground_oia_graph = OIAGraph.parse(oia_repo.get(source, index))
        # except Exception as e:
        #     logger.error("error in get labeled oia for {0}_{1}".format(source, index))
        #     continue
        result = ud_repo.get(int(uri), source)
        if len(result) == 0:
            logger.error("cannot find the original ud data ")
            continue

        index, sentence, ud_data = result[0]

        logger.info("evaluating uri {0}".format(index))
        try:
            if use_ud:
                pred_oia_graph, _ = ud2oia(lang, index, ud_data, debug=debug)
            else:
                pred_oia_graph, _ = sentence2oia(lang, index, sentence, debug=debug)
        except Exception as e:
            logger.error("error in generating oia for {0}_{1}".format(source, index))
            traceback.print_exc()
            continue

        results[index] = (pred_oia_graph, ground_oia_graph)

        try:

            eval_result = graph_match_metric(pred_oia_graph, ground_oia_graph)
        except Exception as e:
            logger.error("error in evaluating {0}_{1}".format(source, index))
            traceback.print_exc()
            continue

        ((node_pred_num, node_true_num, node_match_num),
         (edge_pred_num, edge_true_num, edge_match_num), exact_same) = eval_result

        node_recall = float(node_match_num) / node_true_num if node_true_num > 0 else 1
        node_prec = float(node_match_num) / node_pred_num if node_pred_num > 0 else 1
        if node_true_num == 0 and node_pred_num == 0:
            node_f1 = 1
        elif node_match_num == 0:
            node_f1 = 0
        else:
            node_f1 = 2 * node_recall * node_prec / (node_recall + node_prec)

        edge_recall = float(edge_match_num) / edge_true_num if edge_true_num > 0 else 1
        edge_prec = float(edge_match_num) / edge_pred_num if edge_pred_num > 0 else 1
        if edge_true_num == 0 and edge_pred_num == 0:
            edge_f1 = 1
        elif edge_match_num == 0:
            edge_f1 = 0
        else:
            edge_f1 = 2 * edge_recall * edge_prec / (edge_recall + edge_prec)
        item_measure.append((index, node_f1, edge_f1))

        total_node_pred_num += node_pred_num
        total_node_true_num += node_true_num
        total_node_match_num += node_match_num
        total_edge_pred_num += edge_pred_num
        total_edge_true_num += edge_true_num
        total_edge_match_num += edge_match_num
        total_exact_same += exact_same

        total_graph_num += 1

    logger.info("Evaluation Results:")

    logger.info("Error Graph Num = {0}".format(total_empty_num))

    logger.info("Type\tTrueNum\tPredNum\tMatchNum\tRecall\tPrecision")
    logger.info("Node\t{0}\t{1}\t{2}\t{3}\t{4}".format(
        total_node_true_num, total_node_pred_num, total_node_match_num,
        float(total_node_match_num) / total_node_true_num, float(total_node_match_num) / total_node_pred_num,
    ))
    logger.info("Edge\t{0}\t{1}\t{2}\t{3}\t{4}".format(
        total_edge_true_num, total_edge_pred_num, total_edge_match_num,
        float(total_edge_match_num) / total_edge_true_num, float(total_edge_match_num) / total_edge_pred_num,
    ))
    logger.info("Graph\t{0}\t{1}\t{2}\t{3}\t{4}".format(
        total_graph_num, total_graph_num, total_exact_same,
        float(total_exact_same) / total_graph_num, float(total_exact_same) / total_graph_num,
    ))

    logger.info("Worst Items by node f1")
    item_measure.sort(key=lambda x: x[1])
    for index, node_f1, edge_f1 in item_measure:
        if node_f1 < 0.8:

            pred_oia_graph, ground_oia_graph = results[index]
            pred_img = oia_visualizer.visualize(pred_oia_graph, return_img=True)
            ground_img = oia_visualizer.visualize(ground_oia_graph, return_img=True)

            image = make_pair_image(pred_img, ground_img)
            image.save(os.path.join(output_path, "node_error_{0}_{1}.png".format(source, index)))

            logger.info ("{0}\t{1}\t{2}".format(index, node_f1, edge_f1))

    logger.info("Worst Items by edge f1")
    item_measure.sort(key=lambda x: x[2])
    for index, node_f1, edge_f1 in item_measure:
        if edge_f1 < 0.6:

            pred_oia_graph, ground_oia_graph = results[index]
            pred_img = oia_visualizer.visualize(pred_oia_graph, return_img=True)
            ground_img = oia_visualizer.visualize(ground_oia_graph, return_img=True)

            image = make_pair_image(pred_img, ground_img)
            image.save(os.path.join(output_path, "label_error_{0}_{1}.png".format(source, index)))

            logger.info("{0}\t{1}\t{2}".format(index, node_f1, edge_f1))


    # logger.info("All mismatch")
    # item_measure.sort(key=lambda x: x[2])
    # for index, node_f1, edge_f1 in item_measure:
    #     if edge_f1 != 1.0 or node_f1 != 1.0:
    #         logger.info("{0}\t{1}\t{2}".format(index, node_f1, edge_f1))


if __name__ == "__main__":
    evaluate()
