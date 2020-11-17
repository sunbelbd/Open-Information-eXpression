"""TODO: add doc string
    """
from collections import defaultdict

from oix.oia.graphs.dependency_graph import *


def rels_contain(rel_set, r):
    """TODO: add doc string
    """
    for rel in rel_set:
        if ':' in r:
            if r in rel:
                return True
        else:
            if r in rel.split(':')[0]:
                return True
    return False


def conjuncts_propagation(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    def check_rel(parent_tag, son_tag, judge_tag, r):
        """TODO: add doc string
    """
        main_r = r.split(':')[0]
        if parent_tag == 'VERB' and son_tag == 'VERB':
            # if 'nsubj' in main_r or 'obj' in main_r or 'aux' in main_r:
            if 'nsubj' in main_r or 'obj' in main_r or 'acl' in main_r:
                return True
        if (parent_tag == 'NOUN' or parent_tag == 'PRON' or parent_tag == 'PROPN') and (
                son_tag == 'NOUN' or son_tag == 'PRON' or son_tag == 'PROPN'):
            if 'nsubj' in main_r or 'obj' in main_r or 'obl' in main_r: # or 'nmod' in main_r:
                return True
        if (parent_tag == 'ADJ' or parent_tag == 'DET' or parent_tag == 'NUM') and (
                son_tag == 'ADJ' or son_tag == 'DET' or son_tag == 'NUM'):
            if 'amod' in main_r or 'nsubj' in main_r:
                return True
        return False

        # copy_rel = ['nsubj', 'obj', 'aux', 'amod', 'obl',  'acl', 'nmod']
        # copy_rel = ['nsubj', 'obj', 'amod', 'obl', 'acl', 'nmod']
        # copy_rel = ['nsubj', 'obj', 'amod',  'acl', 'nmod']
        copy_rel = ['nsubj', 'obj', 'amod', 'obl', 'acl']
        # if 'acl' in r:
        # dep_graph.visualize('wrong_vis111111111%s.png' % (r))
        for rel in copy_rel:
            if rel in r.split(':')[0]:
                return True
        return False

    def has_relation(node, relation, in_relation=True):
        """TODO: add doc string
    """
        relation_main = relation.split(':')[0]
        if in_relation:
            relation_dict = in_relation_dict
        else:
            relation_dict = out_relation_dict
        if node not in relation_dict:
            return False
        for r in relation_dict[node]:
            if relation_main in r:
                return True
        return False

    dep_add = []
    dep_remove = []
    # return [], []
    out_relation_dict = dict()
    in_relation_dict = dict()
    for node1_id, node2_id in dep_graph.g.edges():
        out_node = dep_graph.get_node(node1_id)
        in_node = dep_graph.get_node(node2_id)
        rels = dep_graph.get_dependency(out_node, in_node).rels
        if out_node not in out_relation_dict:
            out_relation_dict[out_node] = set()
        if out_node not in in_relation_dict:
            in_relation_dict[out_node] = set()
        if in_node not in out_relation_dict:
            out_relation_dict[in_node] = set()
        if in_node not in in_relation_dict:
            in_relation_dict[in_node] = set()
        for r in rels:
            out_relation_dict[out_node].add(r)
            in_relation_dict[in_node].add(r)

    for node1_id, node2_id in dep_graph.g.edges():
        out_node = dep_graph.get_node(node1_id)
        in_node = dep_graph.get_node(node2_id)
        rels = dep_graph.get_dependency(out_node, in_node).rels
        # if 'conj' not in rels:
        #     continue
        if not rels_contain(rels, 'conj'):
            continue
        # copy the relation(nsubj,obj) of out_node to the in_node
        for child, child_rel in dep_graph.children(out_node):
            child_rel = child_rel.rels
            if child == in_node:
                continue
            # if 'punct' in child_rel:
            #     continue
            # if (not rels_contain(child_rel, 'punct')) and (not rels_contain(child_rel, 'nsubj')):

            if rels_contain(child_rel, 'punct'):
                continue

            # print(str(child), child_rel)
            # print(child_rel)
            # dep_graph.add_dependency(in_node, child, child_rel)
            for c_rel in child_rel:
                if check_rel(out_node.UPOS, in_node.UPOS, child.UPOS, c_rel) and not has_relation(in_node, c_rel,
                                                                                                  in_relation=False):
                    dep_add.append((in_node, child, c_rel))
            # if 'nsubj' in child_rel:
            #     dep_graph.add_dependency(in_node, child, 'nsubj')
            # if 'obj' in child_rel:
            #     dep_graph.add_dependency(in_node, child, 'obj')
        for parent, parent_rel in dep_graph.parents(out_node):
            parent_rel = parent_rel.rels
            # if 'punct' in parent_rel:
            #     continue
            if rels_contain(parent_rel, 'punct'):
                continue
            # dep_graph.add_dependency(parent, in_node, parent_rel)
            # dep_add.append((parent, in_node, parent_rel))
            for p_rel in parent_rel:
                if check_rel(out_node.UPOS, in_node.UPOS, parent.UPOS, p_rel) and not has_relation(in_node, p_rel,
                                                                                                   in_relation=True):
                    dep_add.append((parent, in_node, p_rel))
    for out_node, in_node, rel in dep_add:
        dep_graph.add_dependency(out_node, in_node, rel)
    return dep_add, dep_remove


def raised_subjects(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    dep_add = []
    dep_remove = []
    for node1_id, node2_id in dep_graph.g.edges():
        out_node = dep_graph.get_node(node1_id)
        in_node = dep_graph.get_node(node2_id)
        rels = dep_graph.get_dependency(out_node, in_node).rels
        # if 'nsubj' not in rels:
        #     continue
        if not rels_contain(rels, 'nsubj'):
            continue
        for child, child_rel in dep_graph.children(out_node):
            child_rel = child_rel.rels
            if child == in_node:
                continue
            # if 'xcomp' in child_rel:
            if rels_contain(child_rel, 'xcomp'):
                # dep_graph.add_dependency(child, in_node, 'nsubj')
                dep_add.append((child, in_node, 'nsubj:xsubj'))
    for out_node, in_node, rel in dep_add:
        dep_graph.add_dependency(out_node, in_node, rel)
    return dep_add, dep_remove


def relative_clauses(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    def wh_words(x):
        """TODO: add doc string
    """
        # return True
        if len(x) < 2:
            return False
        x = x.lower()
        if (x[0] == 'w' or x[0] == 'W') and (x[1] == 'h'):
            return True
        if (x == 'that') or (x == 'That'):
            return True
        return False

    del_dep = []
    dep_add = []
    dep_remove = []
    nodes_has_advmod = set()
    for node1_id, node2_id in dep_graph.g.edges():
        out_node = dep_graph.get_node(node1_id)
        in_node = dep_graph.get_node(node2_id)
        rels = dep_graph.get_dependency(out_node, in_node).rels
        if not rels_contain(rels, 'advmod'):
            continue
        nodes_has_advmod.add(out_node)

    for node1_id, node2_id in dep_graph.g.edges():
        out_node = dep_graph.get_node(node1_id)
        in_node = dep_graph.get_node(node2_id)
        rels = dep_graph.get_dependency(out_node, in_node).rels
        # have_acl = False
        # for x in rels:
        # have_acl = have_acl or ('acl' in x)
        # have_acl = have_acl or rels_contain(x, 'acl')
        # have_acl = have_acl or rels_contain(x, 'acl:relcl')
        # print(rels)
        # exit()
        # if not have_acl:
        if not rels_contain(rels, 'acl:relcl'):
            continue
        if not (out_node.UPOS == 'NOUN' and (
                in_node.UPOS == 'PRON' or in_node.UPOS == 'VERB' or in_node.UPOS == 'NOUN')):
            continue
        # print('find!', rels)
        # exit()
        for child, child_rel in dep_graph.children(in_node):
            child_rel = child_rel.rels
            # if 'nsubj' in child_rel:
            if rels_contain(child_rel, 'nsubj'):
                # print(in_node.UPOS)
                # exit()
                if in_node in nodes_has_advmod:
                    continue
                if in_node.UPOS == 'PRON':  # the relative pronoun occupies the head position within the clause
                    # dep_graph.add_dependency(out_node, child, 'nsubj')
                    # dep_graph.add_dependency(out_node, in_node, 'ref')
                    del_dep.append((in_node, child, 'nsubj'))
                    dep_add.append((out_node, child, 'nsubj'))
                    dep_add.append((out_node, in_node, 'ref'))
                else:
                    if wh_words(child.FORM):
                        # dep_graph.add_dependency(in_node, out_node, 'nsubj')
                        # dep_graph.add_dependency(out_node, child, 'ref')
                        del_dep.append((in_node, child, 'nsubj'))
                        dep_add.append((in_node, out_node, 'nsubj'))
                        dep_add.append((out_node, child, 'ref'))
                    else:
                        # dep_graph.add_dependency(in_node, out_node, 'obj')
                        dep_add.append((in_node, out_node, 'obj'))
            # elif 'advmod' in child_rel:
            elif rels_contain(child_rel, 'advmod'):
                # dep_graph.add_dependency(out_node, child, 'ref')
                # dep_graph.add_dependency(in_node, out_node, 'obl')
                dep_add.append((out_node, child, 'ref'))
                dep_add.append((in_node, out_node, 'obl'))
            # elif 'obj' in child_rel:
            elif rels_contain(child_rel, 'obj'):
                if not wh_words(child.FORM):
                    continue
                rel_name = ''
                for r in child_rel:
                    if 'obj' in r:
                        rel_name = r

                # del_dep.append((in_node, child, rel_name))
                # dep_add.append((in_node, out_node, rel_name))
                # dep_add.append((out_node, child, 'ref'))

                if in_node.UPOS == 'PRON':  # the relative pronoun occupies the head position within the clause
                    del_dep.append((in_node, child, rel_name))
                    dep_add.append((out_node, child, rel_name))
                    dep_add.append((out_node, in_node, 'ref'))
                else:
                    if wh_words(child.FORM):
                        #del_dep.append((in_node, child, rel_name))
                        #dep_add.append((in_node, out_node, rel_name))
                        dep_add.append((out_node, child, 'ref'))
                    else:
                        dep_add.append((in_node, out_node, 'obj'))

            else:
                continue
    for out_node, in_node, rel in dep_add:
        dep_graph.add_dependency(out_node, in_node, rel)
    for out_node, in_node, rel in del_dep:
        dep_graph.remove_dependency(out_node, in_node, rel)
    dep_remove = del_dep
    return dep_add, dep_remove


def add_case_information(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    def check_mod(rel):
        """TODO: add doc string
    """
        # rel_list = ['nmod', 'acl', 'obl', 'advcl', 'iobj', 'obj', 'ccomp', 'conj']
        rel_list = ['nmod', 'acl', 'obl', 'advcl', 'conj']
        if ':' in rel:
            return False
        for r in rel_list:
            if r in rel:
                if r == 'acl' and 'acl:relcl' in rel:
                    continue
                return True
        return False

    dep_add = defaultdict(list)
    dep_remove = defaultdict(list)
    for node1_id, node2_id in dep_graph.g.edges():
        out_node = dep_graph.get_node(node1_id)
        in_node = dep_graph.get_node(node2_id)
        rels = dep_graph.get_dependency(out_node, in_node).rels
        if ('case' in rels) or ('mark' in rels) or ('cc' in rels):
            trg_lemma = in_node.LEMMA.lower()
            for parent, parent_rel in dep_graph.parents(out_node):
                parent_rel = parent_rel.rels
                changed_pr = []
                for pr in parent_rel:
                    if check_mod(pr):
                        changed_pr.append(pr)
                for pr in changed_pr:
                    # dep_graph.remove_dependency(parent, out_node, pr)
                    # dep_graph.add_dependency(parent, out_node, pr + ':' + trg_lemma)
                    dep_add[(parent, out_node)].append(pr + ':' + trg_lemma)
                    dep_remove[(parent, out_node)].append(pr)

    for (source, target), rels in dep_add.items():  # conll7617
        if len(rels) > 1:
            continue
        rel = rels.pop()
        dep_graph.add_dependency(source, target, rel)
    for (source, target), rels in dep_remove.items():
        if len(rels) > 1:
            continue
        rel = rels.pop()
        dep_graph.remove_dependency(source, target, rel)
    return dep_add, dep_remove


# def subjects_of_controlled_verbs(dep_graph : DependencyGraph):
#     dep_add = []
#     dep_remove = []
#     for node1_id, node2_id in dep_graph.g.edges():
#         out_node = dep_graph.get_node(node1_id)
#         in_node = dep_graph.get_node(node2_id)
#         rels = dep_graph.get_dependency(out_node, in_node).rels
#         if not rels_contain(rels, 'nsubj'):
#             continue
#         for child, child_rel in dep_graph.children(out_node):
#             child_rel = child_rel.rels
#             if child == in_node:
#                 continue
#             if not rels_contain(child_rel, 'xcomp'):
#                 continue
#             dep_add.append((child, in_node, 'nsubj:xsubj'))

#     for source, target, rel in dep_add:
#         dep_graph.add_dependency(source, target, rel)
#     for source, target, rel in dep_remove:
#         dep_graph.remove_dependency(source, target, rel)
#     return dep_add, dep_remove


def to_enhanced_dep(dep_graph: DependencyGraph):
    """TODO: add doc string
    """
    dep_add4, dep_remove4 = add_case_information(dep_graph)
    dep_add1, dep_remove1 = conjuncts_propagation(dep_graph)
    dep_add2, dep_remove2 = raised_subjects(dep_graph)
    dep_add3, dep_remove3 = relative_clauses(dep_graph)
    # dep_add5, dep_remove5 = subjects_of_controlled_verbs(dep_graph)
    return dep_add1 + dep_add2 + dep_add3 + dep_add4, dep_remove1 + dep_remove2 + dep_remove3 + dep_remove4
