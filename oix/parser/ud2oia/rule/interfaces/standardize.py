"""
standardize the labeled data
"""

from oix.data.en.oia.oia_repo import OIARepo
from oix.parser.support.rule.workflow import WorkFlowOptions
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext

from oix.oia.graphs.oia_graph import OIAGraph
from oix.parser.ud2oia.rule.converter.oia_standardize.standardizer import standardize, OIAStandardizer
from oix.oia.validate.update_to_new_standard import upgrade_to_new_standard
import tqdm
import copy
from loguru import logger

import click

@click.command()
@click.argument("output_file_path")
@click.option("--old-standard/--no-old-standard", default=False)
def standardize_oia_repo(output_file_path, old_standard):
    """

    @param output_file_path:
    @type output_file_path:
    @return:
    @rtype:
    """

    source_oia_repo = OIARepo()
    target_oia_repo = OIARepo(output_file_path)

    standardizer = OIAStandardizer()
    context = UD2OIAContext()
    options = WorkFlowOptions()

    for source in ["train", "dev", "test"]:

        standardized_graphs = []
        for oia in tqdm.tqdm(source_oia_repo.all(source), "Standardize {}:".format(source)):

            origin_oia_graph = OIAGraph.parse(oia)

            uri = origin_oia_graph.meta["uri"]
            oia_graph = copy.deepcopy(origin_oia_graph)

            logger.info("Standardizing {}:{}".format(source, uri))

            if old_standard:
                upgrade_to_new_standard(oia_graph)
                logger.info("Update to new standard {}:{}".format(source, uri))

            try:
                standardizer.standardize(None, oia_graph, context, options)
            except Exception as e:
                logger.error("Sentence {0} standardize error".format(uri))
                logger.error("Sentence = " + " ".join(oia_graph.words) )
                raise e

            standardized_graphs.append(oia_graph)

        target_oia_repo.insert(source, standardized_graphs)


if __name__ == "__main__":
    standardize_oia_repo()
