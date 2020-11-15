"""
ud simplifier
"""
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext
from oix.parser.ud2oia.rule.converter.debugger import UD2OIADebugger
from oix.parser.ud2oia.rule.converter.ud_simplifier.fixes.acl_cooccur import acl_loop
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.adjv import adjv_phrase
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.advp import advp_phrase
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.noun import noun_phrase, det_adjv_phrase, noun_all, \
    whose_noun, \
    noun_of_noun, det_of_noun
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.number import num_pair, number_per_unit
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.plain import goeswith
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.plain import multi_words_case, multi_words_mark, \
    multi_word_sconj, \
    multi_word_fix_flat, and_or, part, multi_words_cc, aux_not
from oix.parser.ud2oia.rule.converter.ud_simplifier.phrases.verbs import verb_phrase, xcomp_verb, reverse_passive_verb, \
    to_verb, \
    ccomp_mark_sconj
from oix.parser.ud2oia.rule.converter.ud_simplifier.special_case import special_case
from oix.parser.ud2oia.rule.converter.ud_simplifier.structures.be_verbs import be_adj_verb_phrase, there_be_verb_phrase, \
    copula_phrase, be_adp_phrase, \
    get_adj_verb_phrase, subj_adp_phrase, be_not_phrase
from oix.parser.ud2oia.rule.converter.ud_simplifier.structures.comparative import separated_asas, continuous_asas, \
    gradation
from oix.parser.ud2oia.rule.converter.ud_simplifier.structures.conjunction import conjunction
from oix.parser.ud2oia.rule.converter.ud_simplifier.structures.prepositions import such_that, amod_obl, acl_verb_obl_case, \
    amod_xcomp_to_acl
from oix.parser.ud2oia.rule.converter.ud_simplifier.structures.secondary import secondary_predicate
from oix.parser.support.rule.workflow import WorkFlow, WorkFlowContext, WorkFlowOptions
from oix.oia.graphs.dependency_graph import DependencyGraph

from loguru import logger


class UDSimplifier(WorkFlow):
    """
    UD Simplifier
    """

    def __init__(self):
        self.simplifiers = [
            acl_loop,

            # make simple noun phrase
            part,
            and_or,
            goeswith,
            aux_not,
            multi_word_fix_flat,
            number_per_unit,
            multi_words_case,
            multi_words_mark,
            multi_words_cc,
            multi_word_sconj,

            special_case,
            adjv_phrase,
            advp_phrase,
            det_adjv_phrase,  # be the least loyal, must before the be_adj_verb_phrase

            noun_phrase,
            noun_all,
            whose_noun,
            num_pair,

            noun_of_noun,
            conjunction,

            noun_of_noun,

            det_of_noun,

            be_adj_verb_phrase,
            get_adj_verb_phrase,
            there_be_verb_phrase,
            verb_phrase,
            to_verb,

            # ideally, above simplifier only merge nodes

            # conjunction,

            reverse_passive_verb,
            be_adp_phrase,  # must before copula_phrase
            subj_adp_phrase,  #
            copula_phrase,
            be_not_phrase,

            verb_phrase,  # call verb_phrase again for new added verbs
            ccomp_mark_sconj,

            acl_verb_obl_case,
            amod_xcomp_to_acl,

            xcomp_verb,

            such_that,
            amod_obl,

            separated_asas,
            continuous_asas,
            # noun_phrase_with_of,
            # timeadv_phrase,

            gradation,
            secondary_predicate,

        ]

        super().__init__(self.simplifiers)
        self.simplified = False

    def simplify(self, dep_graph: DependencyGraph, context: UD2OIAContext, options: WorkFlowOptions):
        """

        @param dep_graph:
        @type dep_graph:
        @return:
        @rtype:
        """

        def __simplify_hook():
            self.simplified = True
            return self.working_stack()

        dep_graph.set_context_hook(__simplify_hook)

        if options.debug:
            context.debugger.record("simplify", "init", dep_graph)

        for index, simplifier in enumerate(self.simplifiers):
            logger.debug("simplify by: {0}".format(simplifier.__name__))
            try:
                self.simplified = False
                simplifier(dep_graph)
                if options.debug and self.simplified:
                    context.debugger.record("simplify", simplifier.__name__, dep_graph)

            except Exception as e:

                logger.opt(exception=True).error("Error when running Simplifier: ", simplifier.__name__)
                raise e
