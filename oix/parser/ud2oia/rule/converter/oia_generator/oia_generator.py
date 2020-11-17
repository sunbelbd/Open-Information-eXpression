"""
ud enhancer
"""
import sys
import traceback

from oix.parser.support.rule.workflow import WorkFlow, WorkFlowOptions
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.parser.ud2oia.rule.converter.debugger import UD2OIADebugger

from oix.parser.ud2oia.rule.converter.oia_generator.generators.apposition import appositive_phrase
from oix.parser.ud2oia.rule.converter.oia_generator.generators.clause import simple_clause
from oix.parser.ud2oia.rule.converter.oia_generator.generators.compond import adnominal_clause_mark, adverbial_clause, aclwhose, \
    object_relative_clause, oblique_relative_clause, subject_relative_clause, adv_relative_clause, \
    subject_relative_clause_loop
from oix.parser.ud2oia.rule.converter.oia_generator.generators.conjunction import advcl_mark_sconj
from oix.parser.ud2oia.rule.converter.oia_generator.generators.conjunction import and_or_conjunction
from oix.parser.ud2oia.rule.converter.oia_generator.generators.connector import discourse, vocative, parataxis, parallel_list, \
    dislocated, \
    reparandum
from oix.parser.ud2oia.rule.converter.oia_generator.generators.fallback import fallback_sconj
from oix.parser.ud2oia.rule.converter.oia_generator.generators.it_clause import it_be_adjv_that, it_verb_clause
from oix.parser.ud2oia.rule.converter.oia_generator.generators.modifier import adj_modifier, nmod_with_case, acl_mod_verb, \
    adv_verb_modifier, adv_ccomp, \
    adv_adj_modifier, acl_mod_adjv, obl_modifier, nmod_without_case, det_predet
from oix.parser.ud2oia.rule.converter.oia_generator.generators.oblique import oblique_with_prep, oblique_without_prep
from oix.parser.ud2oia.rule.converter.oia_generator.generators.postprocess import make_dag, single_root
from oix.parser.ud2oia.rule.converter.oia_generator.generators.questions import adv_question, general_question
from oix.parser.ud2oia.rule.converter.oia_generator.generators.trivial import single_node, two_node_with_case

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
from oix.oia.graphs.oia_graph import OIAGraph

from loguru import logger
import copy


class OIAGenerator(WorkFlow):
    """
    UD Simplifier
    """

    def __init__(self):
        self.generators = [
            advcl_mark_sconj,
            adnominal_clause_mark,
            adverbial_clause,
            aclwhose,

            adv_relative_clause,
            object_relative_clause,
            oblique_relative_clause,
            subject_relative_clause,
            subject_relative_clause_loop,

            # modifier
            adj_modifier,
            nmod_with_case,
            adv_ccomp,
            acl_mod_verb,
            acl_mod_adjv,
            it_be_adjv_that,
            it_verb_clause,
            simple_clause,
            appositive_phrase,
            # appositive_phrase,
            # so,

            and_or_conjunction,
            # negation,
            # case_case,
            oblique_with_prep,
            oblique_without_prep,

            vocative,
            discourse,
            parataxis,
            parallel_list,
            dislocated,
            reparandum,

            adv_question,
            general_question,

            # fall back

            adv_verb_modifier,
            adv_adj_modifier,

            obl_modifier,
            nmod_without_case,

            det_predet,

            single_node,
            fallback_sconj,
            make_dag,
            single_root,
            two_node_with_case

        ]

        super().__init__(self.generators)
        self.oia_updated = False

    def generate(self, dep_graph: DependencyGraph, context: UD2OIAContext,
                 options: WorkFlowOptions):
        """

        @param dep_graph:
        @type dep_graph:
        @return:
        @rtype:
        """

        oia_graph = OIAGraph()

        node_dict = dict((node.ID, node) for node in dep_graph.origin_nodes() if node.LOC >= 0)
        node_list = sorted(node_dict.values(), key=lambda node: node.LOC)
        oia_graph.set_words([x.FORM for x in node_list])

        logger.debug(oia_graph.words)
        def __oia_updated_hook():
            self.oia_updated = True
            return self.working_stack()

        oia_graph.set_context_hook(__oia_updated_hook)

        for index, generator in enumerate(self.generators):
            try:
                self.oia_updated = False
                generator(dep_graph, oia_graph, context)
                if options.debug and self.oia_updated:
                    context.debugger.record("generate", generator.__name__, oia_graph)

            except Exception as e:
                if options.debug:
                    context.debugger.record("generate", generator.__name__, oia_graph, str(e))

                traceback.print_exc(file=sys.stderr)
                logger.error(e)

        return oia_graph
