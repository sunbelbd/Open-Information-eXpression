"""
update to new standard
"""
from oix.oia.graphs.oia_graph import OIAGraph, OIAAuxNode


def upgrade_to_new_standard(oia_graph: OIAGraph):
    """
    @param oia_graph:
    @type oia_graph:
    @return:
    @rtype:
    """

    for n1, edge, n2 in oia_graph.relations():
        edge.label = edge.label.replace("pred:arg:", "pred.arg.")
        if edge.label.startswith("mod_by:"):
            edge.label = edge.label.replace("mod_by:", "as:")
        if edge.label == "func:arg":
            edge.label = "func.arg.1"
        if edge.label == "mod_by":
            edge.label = "mod"
        elif edge.label == "mod":
            edge.label = "as:mod"
        if edge.label == "ref_by":
            edge.label = "ref"
        elif edge.label == "ref":
            edge.label = "as:ref"