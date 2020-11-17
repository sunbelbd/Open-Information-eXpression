"""
sentence to oia_graph
"""
import json

from oix.oia.graphs.oia_graph import OIAGraphVisualizer
from oix.oia.graphs.utils import CompactJSONEncoder

from oix.parser.ud2oia.rule.parser import sentence2oia


import click

@click.command()
@click.argument("language", type=click.Choice(['en', 'cn']))
@click.argument("sentence", type=click.STRING)
@click.argument("output_prefix")
@click.option("--debug/--no-debug", default=False)
def predict(language, sentence, output_prefix, debug):
    """

    @param sentence:
    @type sentence:
    @param output_prefix:
    @type output_prefix:
    @return:
    @rtype:
    """

    oia_graph, context = sentence2oia(language, output_prefix, sentence, debug)

    data_file_path = output_prefix + ".json"
    visualization_file = output_prefix + ".png"

    with open(data_file_path, 'w', encoding="UTF8") as f:
        content = json.dumps(oia_graph.data(), cls=CompactJSONEncoder, ensure_ascii=False)
        f.write(content)

    oia_visualizer = OIAGraphVisualizer()

    oia_visualizer.visualize(oia_graph, filename=visualization_file)


if __name__ == "__main__":
    predict()