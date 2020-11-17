"""
fix the issue of acl and obl cooccured in
"""
from oix.oia.graphs.dependency_graph import DependencyGraph


def acl_loop(dep_graph: DependencyGraph):
    """

    :param dep_graph:
    :param oia_graph:
    :return:
    """

    for n1, n2, deps in dep_graph.dependencies():

        if "acl:relcl" in deps:
            back_deps = dep_graph.get_dependency(n2, n1)
            if any(x in back_deps for x in {"obl", "nsubj", "obj", "mark", "advmod"}):
                dep_graph.remove_dependency(n2, n1)
