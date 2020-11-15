"""
fix labeled data
"""
import click
from oix.data.en.ud_repo import UDRepo
from oix.oia.en.envolve.correct_conj_arg_order import correct_conj_order
from oix.oia.en.envolve.fix_verb_adp import fix_verb_adp
# from oix.oiagraph.en.envolve.correct_connector_order import fix_connector_order
from oix.oia.en.envolve.merge_noun_conj import merge_noun_conj
from loguru import logger
from networkx.drawing.nx_agraph import to_agraph

from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph, OIAGraphResult


def fix_labeled_data(labeled_oia: OIAGraph, dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    fixed1 = merge_noun_conj(labeled_oia, dep_graph)
    #    fix_noun_prep_noun
    #    fix_remove_desc
    fixed2 = correct_conj_order(labeled_oia, dep_graph)
    fixed3 = fix_verb_adp(labeled_oia, dep_graph)
    # data with desc always means error in annotation
    #    fixed4 = remove_desc(labeled_oia, dep_graph)
    #    merge_noun_adp_noun should be applied after the idiom discovery. for example: I'm in love with X.
    #     fixed4 = merge_noun_adp_noun(labeled_oia, dep_graph)
    #    fixed4 = fix_connector_order(labeld_oia, dep_graph) # this seems not useful since the testing label for connector is rubbish

    return fixed1 or fixed2 or fixed3


repo = UDRepo()


@click.group()
def fix_cmd():
    """TODO: add doc string
    """
    pass


@fix_cmd.command()
@click.argument("source", type=click.File())
@click.argument("target", type=click.File(mode='w'))
def one(source, target):
    """

    :param output_path:
    :return:
    """

    result = OIAGraphResult()
    result.load(source, ud=False)

    ud_results = repo.get(result.sentence_index)
    index, sentence, ud_data = ud_results[0]

    dep_graph = DependencyGraph.from_conll(ud_data, need_root=True)
    oia_graph = result.recover(dep_graph)

    if fix_labeled_data(oia_graph, dep_graph):

        try:
            labeled_A = to_agraph(result.graph)

            labeled_A.draw("{0}.label.png".format(index), prog="dot")
        except:
            pass

        result.from_oia_graph(oia_graph, dep_graph)

        try:
            fixed_A = to_agraph(result.graph)

            fixed_A.draw("{0}.fixed.png".format(index), prog="dot")
        except:
            pass

        result.write(target)
    else:

        logger.info("No fix needed")


@fix_cmd.command()
@click.argument("source", type=click.Path(file_okay=False, dir_okay=True, exists=True))
@click.argument("target", type=click.Path(file_okay=False, dir_okay=True, exists=True))
def batch(source, target):
    """

    :param :
    :return:
    """

    import os
    source_file_paths = [os.path.join(source, f) for f in sorted(os.listdir(source))
                         if os.path.isfile(os.path.join(source, f)) and f.endswith(".dot")]

    for file_path in source_file_paths:
        with open(file_path, "r") as source_file:

            logger.info("Processing {0}".format(file_path))
            result = OIAGraphResult()

            try:
                result.load(source_file, ud=False)
            except Exception as e:

                logger.error("Failed to process file: {0}".format(file_path))
                continue

        ud_results = repo.get(result.sentence_index)
        index, sentence, ud_data = ud_results[0]

        dep_graph = DependencyGraph.from_conll(ud_data, need_root=True)
        try:
            oia_graph = result.recover(dep_graph)
        except Exception as e:
            logger.error("Failed to process sample {0} with error {1}".format(index, e))
            continue

        if fix_labeled_data(oia_graph, dep_graph):

            try:
                labeled_A = to_agraph(result.graph)

                labeled_A.draw("{0}.label.png".format(index), prog="dot")
            except:
                pass

            result.from_oia_graph(oia_graph, dep_graph)

            try:
                fixed_A = to_agraph(result.graph)

                fixed_A.draw("{0}.fixed.png".format(index), prog="dot")
            except:
                pass

            target_file_path = os.path.join(target, "{0}.dot".format(result.sentence_index))
            with open(target_file_path, "w") as target_file:
                logger.info("Writing results to  {0}".format(target_file_path))
                result.write(target_file)


if __name__ == "__main__":
    cli = click.CommandCollection(sources=[fix_cmd])
    cli()
