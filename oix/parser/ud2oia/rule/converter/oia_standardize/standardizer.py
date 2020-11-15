"""
standardize
"""
from oix.parser.support.rule.workflow import WorkFlow, WorkFlowOptions
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.parser.ud2oia.rule.converter.oia_standardize.phrase_split_conj import PhraseSplitCONJ
from oix.parser.ud2oia.rule.converter.oia_standardize.predefined_pred2edge import PredefinedPredicate2Edge
from oix.parser.ud2oia.rule.converter.oia_standardize.sconj_root2child import SCONJRoot2Child
from oix.oia.graphs.dependency_graph import DependencyGraph
from oix.oia.graphs.oia_graph import OIAGraph


def standardize(oia_graph: OIAGraph):

    """
    Standardize
    """

    envolvers = [
#        NounSplitOf(),
        PhraseSplitCONJ(),
        PredefinedPredicate2Edge(),
        SCONJRoot2Child(),
    ]

    for envolver in envolvers:
        envolver.forward(oia_graph)



from loguru import logger


class OIAStandardizer(WorkFlow):
    """
    UD Simplifier
    """

    def __init__(self):
        self.standardizers = [
#            PhraseSplitCONJ(),
            PredefinedPredicate2Edge(),
            SCONJRoot2Child(),

        ]

        super().__init__(self.standardizers)
        self.standardized = False

    def standardize(self, dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext, options: WorkFlowOptions):
        """

        @param dep_graph:
        @type dep_graph:
        @return:
        @rtype:
        """

        def __standardized_hook():
            self.standardized = True
            return self.working_stack()

        oia_graph.set_context_hook(__standardized_hook)

        if options.debug:
            context.debugger.record("standardize", "init", oia_graph)

        for index, standardizer in enumerate(self.standardizers):
            try:
                self.standardized = False
                standardizer.forward(oia_graph)
                if options.debug and self.standardized:
                    context.debugger.record("standardize", type(standardizer).__name__, oia_graph)

            except Exception as e:

                logger.opt(exception=True).error("Error when running Standardize: ", type(standardizer).__name__)
                raise e
