"""
rule based univesal dependencies to oia converter
"""
from oix.parser.support.rule.workflow import WorkFlowOptions
from oix.parser.ud2oia.rule.converter.converter import UD2OIAConverter
from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia import standard
from loguru import logger


def ud2oia(lang, uri, ud_data, enhanced=True, debug=False):

    """

    @param ud:
    @type ud:
    @return:
    @rtype:
    """

    standard.language = lang


    oia_converter = UD2OIAConverter()

    options = WorkFlowOptions()
    options.uri = uri
    options.debug = debug

    dep_graph = DependencyGraph.from_conll(ud_data, need_root=True, enhanced=enhanced)
    dep_graph.enhanced = enhanced
    try:
        oia_graph, context = oia_converter.convert(dep_graph, options)
    except Exception as e:
        logger.error("Exception in processing ud:")
        for line in ud_data:
            logger.error("\t".join(line))
        raise e

    return oia_graph, context



stanza_pipeline = None


def sentence2oia(lang, uri, sentence, debug=False):
    """

    @param sentence:
    @type sentence:
    @param debug:
    @type debug:
    @return:
    @rtype:
    """


    standard.language = lang


    global stanza_pipeline

    if stanza_pipeline is None:
        import stanza
        stanza_pipeline = stanza.Pipeline(lang, processors='tokenize,mwt,pos,lemma,depparse',
                                                     tokenize_pretokenized=True)

    dep_graph = DependencyGraph.from_sentence(sentence, stanza_pipeline)

    oia_converter = UD2OIAConverter()
    options = WorkFlowOptions()
    options.uri = uri
    options.debug = debug

    try:
        oia_graph, context = oia_converter.convert(dep_graph, options)
    except Exception as e:
        logger.error("Exception in converting sentence " + sentence)
        raise e

    return oia_graph, context