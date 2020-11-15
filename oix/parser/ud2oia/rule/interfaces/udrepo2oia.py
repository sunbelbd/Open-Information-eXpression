"""
sentence to oia_graph
"""
import json
import os

from oix.oia.graphs.oia_graph import OIAGraphVisualizer
from oix.oia.graphs.utils import CompactJSONEncoder
from oix.parser.ud2oia.rule.parser import ud2oia, sentence2oia

import click
from loguru import logger
from oix.oia import standard

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


@click.group()
def predict_cmd():
    """TODO: add doc string
    """
    pass


@predict_cmd.command()

@click.argument("lang", type=click.Choice(["en"]))
@click.argument("source", type=click.Choice(["train", "dev", "test"]))
@click.argument("number", type=click.INT)
@click.argument("output_path")
@click.option("--debug/--no-debug", default=False)
@click.option("--use_ud/--no-use_ud", default=True)
def random(lang, source, number, output_path, debug, use_ud):
    """

    :param output_path:
    :return:
    """

    repo = get_udrepo(lang)

    oia_visualizer = OIAGraphVisualizer()


    for i in range(number):

        index, sentence, ud_data = random.choice(getattr(repo, source))

        if use_ud:
            oia_graph, context = ud2oia(lang, index, ud_data, enhanced=True, debug=debug)
        else:
            oia_graph, context = sentence2oia(lang, index, sentence, debug=debug)

        data_file_path = os.path.join(output_path, "{0}_{1}.json".format(source, index))
        visualization_file = os.path.join(output_path, "{0}_{1}.png".format(source, index))

        with open(data_file_path, 'w', encoding="UTF8") as f:
            content = json.dumps(oia_graph.data(), cls=CompactJSONEncoder, ensure_ascii=False)
            f.write(content)

        oia_visualizer.visualize(oia_graph, filename=visualization_file)


@predict_cmd.command()
@click.argument("lang", type=click.Choice(["en"]))
@click.argument("source", type=click.Choice(["train", "dev", "test"]))
@click.argument("output_path")
@click.option("--start", type=click.INT, default=0)
@click.option("--debug/--no-debug", default=False)
@click.option("--use_ud/--no-use_ud", default=True)
def all(lang, source, output_path, start, debug, use_ud):
    """

    :param output_path:
    :return:
    """

    repo = get_udrepo(lang)

    oia_visualizer = OIAGraphVisualizer()

    for index, sentence, ud_data in getattr(repo, source):
        if index < start:
            continue

        if use_ud:
            oia_graph, context = ud2oia(lang, index, ud_data, debug=debug)
        else:
            oia_graph, context = sentence2oia(lang, index, sentence, debug=debug)

        data_file_path = os.path.join(output_path, "{0}_{1}.json".format(source, index))
        visualization_file = os.path.join(output_path, "{0}_{1}.png".format(source, index))

        with open(data_file_path, 'w', encoding="UTF8") as f:
            content = json.dumps(oia_graph.data(), cls=CompactJSONEncoder, ensure_ascii=False)
            f.write(content)

        oia_visualizer.visualize(oia_graph, filename=visualization_file)


@predict_cmd.command()
@click.argument("lang", type=click.Choice(["en"]))
@click.argument("source", type=click.Choice(["train", "dev", "test"]))
@click.argument("index", type=click.INT)
@click.argument("output_path")
@click.option("--debug/--no-debug", default=False)
@click.option("--use_ud/--no-use_ud", default=True)
def one(lang, source, index, output_path, debug, use_ud):
    """

    :param output_path:
    :return:
    """
    repo = get_udrepo(lang)

    results = repo.get(index, source)

    if not results:
        raise Exception("UD dataset for language {} not found".format(lang))

    index, sentence, ud_data = results[0]

    if use_ud:
        oia_graph, context = ud2oia(lang, index, ud_data, debug=debug)
    else:
        oia_graph, context = sentence2oia(lang, index, sentence, debug=debug)

    logger.debug("oia graph generated ")
    data_file_path = os.path.join(output_path, "{0}_{1}.json".format(source, index))

    visualization_file = os.path.join(output_path, "{0}_{1}.png".format(source, index))

    with open(data_file_path, 'w', encoding="UTF8") as f:
        content = json.dumps(oia_graph.data(), cls=CompactJSONEncoder, ensure_ascii=False)
        f.write(content)

    oia_visualizer = OIAGraphVisualizer()

    oia_visualizer.visualize(oia_graph, filename=visualization_file)


if __name__ == "__main__":
    cli = click.CommandCollection(sources=[predict_cmd])
    cli()
