"""
compound_sentence
"""

#####
from oix.parser.ud2oia.rule.converter.context import UD2OIAContext

from oix.oia.graphs.dependency_graph import DependencyGraph, DependencyGraphNode
from oix.oia.graphs.oia_graph import OIAGraph
from loguru import logger

from oix.oia.standard import CONJUNCTION_WORDS, language


def adverbial_clause(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    Adverbial Clause
##### run in order to catch it. advcl with mark (in order to) #####
##### he worked hard, replacing his feud. advcl without mark #####

    :param dep_graph:
    :param oia_graph:
    :return:
    """
    pattern = DependencyGraph()
    verb_node = pattern.create_node()
    modifier_node = pattern.create_node()

    pattern.add_dependency(verb_node, modifier_node, "advcl")

    for match in list(dep_graph.match(pattern)):

        dep_verb_node = match[verb_node]
        dep_modifier_node = match[modifier_node]

        if context.is_processed(dep_verb_node, dep_modifier_node):
            continue

        oia_verb_node = oia_graph.add_words(dep_verb_node.position)
        oia_modifier_node = oia_graph.add_words(dep_modifier_node.position)

        logger.debug("adverbial clause: verb={0}, modifier={1}".format(dep_verb_node.position,
                                                                      dep_modifier_node.position))

        if oia_graph.has_relation(oia_verb_node, oia_modifier_node):
            continue

        mark = list(dep_graph.children(dep_modifier_node, filter=lambda n, rel: "mark" in rel))

        if mark:
            mark, rel = mark[0]
            pred_node = oia_graph.add_words(mark.position)
            if pred_node is None:
                continue

            if mark.LEMMA in CONJUNCTION_WORDS[language]:
                continue

            oia_graph.add_argument(pred_node, oia_verb_node, 1, mod=True)
            oia_graph.add_argument(pred_node, oia_modifier_node, 2)
        else:

            oia_graph.add_mod(oia_modifier_node, oia_verb_node)


# in subject_relative_clause and object_relativ_clause,
# the subject/object means that
# the role the modified entity (or what, that) in the clause

def subject_relative_clause(dep_graph, oia_graph, context: UD2OIAContext):
    """
    ##### Subject-extracted/referred relative clause #####
    ##### the person who is tall / that is killed -- with ref #####
    ##### the person waiting for the baby -- without ref #####
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()
    entity_node = DependencyGraphNode()
    relcl_node = DependencyGraphNode()
    pattern.add_node(entity_node)
    pattern.add_node(relcl_node)
    # pattern.add_dependency(relcl_node, subj_node, r'\w*subj\w*')
    pattern.add_dependency(entity_node, relcl_node, r'\w*acl:relcl\w*')

    for match in dep_graph.match(pattern):

        dep_entity_node = match[entity_node]
        dep_relcl_node = match[relcl_node]

        subj_nodes = [n for n, l in dep_graph.children(dep_relcl_node,
                                                       filter=lambda n, l: "subj" in l)]
        if subj_nodes and subj_nodes[0].ID != dep_entity_node.ID:
            continue

        oia_verb_node = oia_graph.add_words(dep_relcl_node.position)
        oia_enitity_node = oia_graph.add_words(dep_entity_node.position)

        def __valid_ref(n, l):
            return l == "ref" and dep_entity_node.LOC < n.LOC < dep_relcl_node.LOC

        ref_nodes = list(n for n, l in dep_graph.children(dep_entity_node, filter=__valid_ref))
        ref_nodes.sort(key=lambda x: x.LOC)

        if ref_nodes:
            ref_node = ref_nodes[-1]
            oia_ref_node = oia_graph.add_words(ref_node.position)

            case_nodes = list(n for n, l in dep_graph.children(ref_node, filter=lambda n, l: "case" in l))
            case_nodes.sort(key=lambda x: x.LOC)

            if case_nodes:
                # with which xxxx, the with will become the root pred
                case_node = case_nodes[-1]
                oia_case_node = oia_graph.add_words(case_node.position)

                oia_graph.add_argument(oia_case_node, oia_verb_node, 1)
                oia_graph.add_argument(oia_case_node, oia_ref_node, 2, mod=True)
                oia_graph.add_ref(oia_enitity_node, oia_ref_node)
            else:

                oia_graph.add_argument(oia_verb_node, oia_ref_node, 1, mod=True)
                oia_graph.add_ref(oia_enitity_node, oia_ref_node)
        else:

            oia_graph.add_argument(oia_verb_node, oia_enitity_node, 1,
                                     mod=True)  # function and pred, seems we need another label


def subject_relative_clause_loop(dep_graph, oia_graph, context: UD2OIAContext):
    """
    The loop version is because that the match algorithm donot match part of the loop, see test_match for more detail
    ##### Subject-extracted/referred relative clause #####
    ##### the person who is tall / that is killed -- with ref #####
    ##### the person waiting for the baby -- without ref #####
    :param dep_graph:
    :param oia_graph:
    :return:
    """

    pattern = DependencyGraph()
    entity_node = DependencyGraphNode()
    relcl_node = DependencyGraphNode()
    pattern.add_node(entity_node)
    pattern.add_node(relcl_node)
    pattern.add_dependency(relcl_node, entity_node, r'\w*subj\w*')
    pattern.add_dependency(entity_node, relcl_node, r'\w*acl:relcl\w*')

    for match in dep_graph.match(pattern):

        dep_entity_node = match[entity_node]
        dep_relcl_node = match[relcl_node]


        oia_verb_node = oia_graph.add_words(dep_relcl_node.position)
        oia_enitity_node = oia_graph.add_words(dep_entity_node.position)

        def __valid_ref(n, l):
            return l == "ref" and dep_entity_node.LOC < n.LOC < dep_relcl_node.LOC

        ref_nodes = list(n for n, l in dep_graph.children(dep_entity_node, filter=__valid_ref))
        ref_nodes.sort(key=lambda x: x.LOC)

        if ref_nodes:
            ref_node = ref_nodes[-1]
            oia_ref_node = oia_graph.add_words(ref_node.position)

            dep_case_nodes = list(n for n, l in dep_graph.children(ref_node, filter=lambda n, l: "case" in l))
            dep_case_nodes.sort(key=lambda x: x.LOC)

            if dep_case_nodes:
                # with which xxxx, the with will become the root pred
                dep_case_node = dep_case_nodes[-1]
                oia_case_node = oia_graph.add_words(dep_case_node.position)

                oia_graph.add_argument(oia_case_node, oia_verb_node, 1)
                oia_graph.add_argument(oia_case_node, oia_ref_node, 2)
                oia_graph.add_ref(oia_enitity_node, oia_ref_node)

            else:

                oia_graph.add_argument(oia_verb_node, oia_ref_node, 1)
                oia_graph.add_ref(oia_enitity_node, oia_ref_node)
        else:

            oia_graph.add_argument(oia_verb_node, oia_enitity_node, 1,
                                     mod=True)  # function and pred, seems we need another label


    pattern = DependencyGraph()
    verb_node = DependencyGraphNode()
    entity_node = DependencyGraphNode()
    subj_node = DependencyGraphNode(LEMMA=r"what|who|which|that")

    pattern.add_nodes([verb_node, entity_node, subj_node])

    pattern.add_dependency(verb_node, subj_node, r'\w*subj\w*')
    pattern.add_dependency(entity_node, verb_node, r'\w*acl:relcl\w*')


    for match in dep_graph.match(pattern):

        dep_entity_node = match[entity_node]
        dep_verb_node = match[verb_node]
        dep_subj_node = match[subj_node]


        context.processed(dep_verb_node, dep_subj_node)
        context.processed(dep_entity_node, dep_verb_node)

        oia_verb_node = oia_graph.add_words(dep_verb_node.position)
        oia_enitity_node = oia_graph.add_words(dep_entity_node.position)
        oia_subj_node = oia_graph.add_words(dep_subj_node.position)


        oia_graph.add_mod(oia_verb_node, oia_enitity_node)
        oia_graph.add_ref(oia_enitity_node, oia_subj_node)
        oia_graph.add_argument(oia_verb_node, oia_subj_node, 1)



def object_relative_clause(dep_graph: DependencyGraph, oia_graph: OIAGraph, context: UD2OIAContext):
    """
    ##### Object-extracted/referred relative clause #####
    ##### the person that Andy knows #####
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()
    verb_node = DependencyGraphNode()
    entity_node = DependencyGraphNode()
    subj_node = DependencyGraphNode()

    pattern.add_nodes([verb_node, entity_node, subj_node])

    pattern.add_dependency(verb_node, subj_node, r'\w*subj\w*')
    pattern.add_dependency(entity_node, verb_node, r'\w*acl:relcl\w*')

    for match in dep_graph.match(pattern):

        dep_entity_node = match[entity_node]
        dep_subj_node = match[subj_node]
        dep_verb_node = match[verb_node]


        if dep_subj_node.LEMMA in {"what", "who", "which", "that"}:
            continue

        logger.debug("we found a objective relative clause")
        logger.debug("entity: {0}".format(dep_entity_node))
        logger.debug("subject: {0}".format(dep_subj_node))
        logger.debug("verb: {0}".format(dep_verb_node))

        if context.is_processed(dep_entity_node, dep_verb_node):
            logger.debug("processed")
            continue

        context.processed(dep_verb_node, dep_subj_node)
        context.processed(dep_entity_node, dep_verb_node)

        oia_entity_node = oia_graph.add_words(dep_entity_node.position)
        oia_verb_node = oia_graph.add_words(dep_verb_node.position)
        oia_subj_node = oia_graph.add_words(dep_subj_node.position)

        if oia_graph.has_relation(oia_entity_node, oia_verb_node):
            logger.debug("has relation between entity and verb")
            continue

        oia_graph.add_argument(oia_verb_node, oia_subj_node, 1)

        def __valid_ref(n, l):
            return l == "ref" and dep_entity_node.LOC < n.LOC < dep_verb_node.LOC

        ref_nodes = list(n for n, l in dep_graph.children(dep_entity_node, filter=__valid_ref))
        ref_nodes.sort(key=lambda x: x.LOC)

        if ref_nodes:
            ref_node = ref_nodes[-1]

            oia_ref_node = oia_graph.add_words(ref_node.position)

            oia_graph.add_ref(oia_entity_node, oia_ref_node)

            logger.debug("we are coping with ref between:")
            logger.debug(dep_verb_node)
            logger.debug(ref_node)

            ref_relation = dep_graph.get_dependency(dep_verb_node, ref_node)

            case_nodes = list(n for n, l in dep_graph.children(ref_node, filter=lambda n, l: "case" in l))
            case_nodes.sort(key=lambda x: x.LOC)

            if ref_relation:
                if case_nodes:
                    # with which xxxx, the with will become the root pred
                    case_node = case_nodes[-1]
                    oia_case_node = oia_graph.add_words(case_node.position)

                    oia_graph.add_argument(oia_case_node, oia_verb_node, 1, mod=True)
                    oia_graph.add_argument(oia_case_node, oia_ref_node, 2)
                    oia_graph.add_mod(oia_verb_node, oia_entity_node)
                else:

                    if "obj" in ref_relation:
                        oia_graph.add_argument(oia_verb_node, oia_ref_node, 2)
                    elif ref_relation == "advmod":
                        oia_graph.add_mod(oia_ref_node, oia_verb_node)
                    else:
                        raise Exception("unknown relation: {}".format(ref_relation))
                    # oia_graph.add_argument(oia_verb_node, oia_entity_node, 2, mod=True)


        oia_graph.add_argument(oia_verb_node, oia_subj_node, 1)
        oia_graph.add_argument(oia_verb_node, oia_entity_node, 2, mod=True)

        rels = dep_graph.get_dependency(dep_entity_node, dep_verb_node)

        #if rels.endswith("obj"):
        for node, l in dep_graph.children(dep_verb_node):
            if l == "ccomp":
                oia_ccomp_node = oia_graph.add_words(node.position)
                oia_graph.add_argument(oia_verb_node, oia_ccomp_node, 3)




def adv_relative_clause(dep_graph, oia_graph: OIAGraph, context: UD2OIAContext):
    """

    #### When/Where Relative clause #####
    #### a time when US troops won/ a place where US troops won. acl:relcl with time/place
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()
    modified_node = pattern.create_node()
    modifier_node = pattern.create_node()
    adv_rel_node = pattern.create_node()

    pattern.add_dependency(modified_node, modifier_node, r'acl:relcl\w*')
    pattern.add_dependency(modifier_node, adv_rel_node, r'advmod')

    for match in dep_graph.match(pattern):

        dep_modified_node = match[modified_node]
        dep_modifier_node = match[modifier_node]
        dep_rel_node = match[adv_rel_node]

        if not any(x in dep_rel_node.LEMMA for x in {"when", "where", "how", "why", "what"}):
            continue

        oia_pred_node = oia_graph.add_words(dep_rel_node.position)
        oia_modified_node = oia_graph.add_words(dep_modified_node.position)
        oia_modifier_node = oia_graph.add_words(dep_modifier_node.position)

        if oia_graph.has_relation(oia_modifier_node, oia_modified_node):
            continue

        oia_graph.add_argument(oia_pred_node, oia_modified_node, 1, mod=True)
        oia_graph.add_argument(oia_pred_node, oia_modifier_node, 2)


def oblique_relative_clause(dep_graph, oia_graph, context: UD2OIAContext):
    """
##### Oblique relative Clause #####
##### An announcement, in which he stated that #####
    :param sentence:
    :return:
    """
    pattern = DependencyGraph()
    a = DependencyGraphNode()
    b = DependencyGraphNode()
    c = DependencyGraphNode(FEATS={"PronType": "Rel"})
    d = DependencyGraphNode()

    pattern.add_nodes([a, b, c, d])

    pattern.add_dependency(a, d, r'acl:relcl\w*')
    pattern.add_dependency(a, c, r'ref')
    pattern.add_dependency(d, c, r'obl')
    pattern.add_dependency(c, b, r'case')

    for match in dep_graph.match(pattern):
        dep_a, dep_b, dep_c, dep_d = [match[x] for x in [a, b, c, d]]

        a_node, b_node, c_node, d_node = [oia_graph.add_words(x.position) for x in [dep_a, dep_b, dep_c, dep_d]]

        oia_graph.add_argument(b_node, d_node, 1)
        oia_graph.add_argument(b_node, c_node, 2)
        oia_graph.add_ref(c_node, a_node)


def adnominal_clause_mark(dep_graph, oia_graph, context: UD2OIAContext):
    """
    #### Adnominal clause with marker #####
    #### the way to go / the proof that doing this is helpful #####
    :param sentence:
    :return:
    """
    pattern = DependencyGraph()
    a = pattern.create_node()
    b = pattern.create_node()
    mark = pattern.create_node()

    pattern.add_dependency(a, b, r'.*acl:.*')
    pattern.add_dependency(b, mark, "mark")

    for match in dep_graph.match(pattern):

        dep_a, dep_b, dep_mark = [match[x] for x in [a, b, mark]]

        if oia_graph.has_relation(dep_a, dep_b, direct_link=False):
            continue


        dep = dep_graph.get_dependency(dep_a, dep_b)
        for rel in dep:
            if "acl:" in rel:
                # print('-----------------rel:        ',rel)
                prefix, value = rel.split(":")
                if (value.replace("_", " ") in {dep_mark.FORM, dep_mark.LEMMA} or
                        value in dep_mark.FORM.split(" ") or
                        value in dep_mark.LEMMA.split(" ")):
                    a_node, b_node, mark_node = [oia_graph.add_words(x.position)
                                                 for x in [dep_a, dep_b, dep_mark]]
                    # TODO: decide whether function or argument
                    oia_graph.add_argument(mark_node, a_node, 1, mod=True)
                    oia_graph.add_argument(mark_node, b_node, 2)

                    context.processed(dep_a, dep_b)
                    context.processed(dep_b, dep_mark)


def aclwhose(dep_graph, oia_graph, context: UD2OIAContext):
    """

#### the person whose/who's cat is cute
#### @return a list of four-tuple (noun, whose/who's, possessee, aclmodifier)
    :param sentence:
    :return:
    """

    pattern = DependencyGraph()
    a = DependencyGraphNode()  # person
    b = DependencyGraphNode(FEATS={"PronType": "Int"})  # whose
    c = DependencyGraphNode()  # cat
    d = DependencyGraphNode()  # cute

    pattern.add_nodes([a, b, c, d])

    pattern.add_dependency(a, d, r'.*acl:relcl.*')
    pattern.add_dependency(d, c, r'.*nsubj|obj|iobj.*')
    pattern.add_dependency(c, b, r'.*nmod:poss.*')
    #    pattern.add_dependency(b, a, r'.*ref.*')

    for match in dep_graph.match(pattern):
        dep_a, dep_b, dep_c, dep_d = [match[x] for x in [a, b, c, d]]

        a_node, b_node, c_node, d_node = [oia_graph.add_words(x.position) for x in [dep_a, dep_b, dep_c, dep_d]]

        oia_graph.add_function(d_node, a_node)
        oia_graph.add_function(b_node, c_node)
        oia_graph.add_ref(b_node, a_node)
