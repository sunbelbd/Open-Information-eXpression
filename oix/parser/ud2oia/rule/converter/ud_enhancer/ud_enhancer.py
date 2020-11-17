"""
ud enhancer
"""
from oix.parser.support.rule.workflow import WorkFlowContext, WorkFlow, WorkFlowOptions
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.parser.ud2oia.rule.converter.debugger import UD2OIADebugger
from oix.parser.ud2oia.rule.converter.ud_enhancer.rules import add_case_information, conjuncts_propagation, \
    raised_subjects, relative_clauses, DependencyGraph
from loguru import logger



class UDEnhancer(WorkFlow):
    """
    UD Simplifier
    """

    def __init__(self):
        self.enhancers = [
            add_case_information,
            conjuncts_propagation,
            raised_subjects,
            relative_clauses,

        ]

        super().__init__(self.enhancers)
        self.enhanced = False

    def enhance(self, dep_graph: DependencyGraph, context: UD2OIAContext, options: WorkFlowOptions):
        """

        @param dep_graph:
        @type dep_graph:
        @return:
        @rtype:
        """

        def __enhance_hook():
            self.enhanced = True
            return self.working_stack()

        dep_graph.set_context_hook(__enhance_hook)

        for index, enhancer in enumerate(self.enhancers):
            try:
                self.enhanced = False

                enhancer(dep_graph)

                if options.debug and self.enhanced:
                    enhancer_name = enhancer.__name__
                    context.debugger.record("enhance", enhancer_name, dep_graph)

            except Exception as e:

                logger.opt(exception=True).error("Error when running Enhancer: ", enhancer.__name__)
                raise e

