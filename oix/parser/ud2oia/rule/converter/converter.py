"""
converter from universal dependency with Enhance ++ to oia graph
"""

# from oix.oiagraph.en.conversions.be_clause import copula, expletive
import copy
import sys
import traceback

from oix.parser.support.rule.workflow import WorkFlowOptions

from loguru import logger

from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.parser.ud2oia.rule.converter.debugger import UD2OIADebugger
from oix.parser.ud2oia.rule.converter.oia_generator.oia_generator import OIAGenerator
from oix.parser.ud2oia.rule.converter.ud_enhancer.ud_enhancer import UDEnhancer
from oix.parser.ud2oia.rule.converter.ud_simplifier.ud_simplifer import UDSimplifier
from oix.parser.ud2oia.rule.converter.oia_standardize.standardizer import OIAStandardizer
from oix.oia.graphs.dependency_graph import DependencyGraph


class UD2OIAConverter(object):
    """
    UD2OIAConverter

    """

    def __init__(self):

        self.dep_graph_enhancer = UDEnhancer()
        self.dep_graph_simplifier = UDSimplifier()
        self.oia_generator = OIAGenerator()
        self.oia_standardizer = OIAStandardizer()



    def convert(self, dep_graph: DependencyGraph, options: WorkFlowOptions):
        """

        :param debug:
        :param dep_graph:
        :param prefix:
        :return:
        @param options:
        @type options:
        """

        original_dep_graph = copy.deepcopy(dep_graph)


        context = UD2OIAContext()

        if options.debug:

            context.debugger = UD2OIADebugger(dep_graph, options)
            context.debugger.record("start", "init", dep_graph)

        try:
            if not dep_graph.enhanced:
                logger.debug("Enhance the dependency graph ")

                self.dep_graph_enhancer.enhance(dep_graph, context, options)

                dep_graph.enhanced = True

            self.dep_graph_simplifier.simplify(dep_graph, context, options)

            oia_graph = self.oia_generator.generate(dep_graph, context, options)

            self.oia_standardizer.standardize(original_dep_graph, oia_graph, context, options)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            logger.error(e)

            try:
                oia_graph
            except NameError:
                oia_graph = None

        return oia_graph, context
