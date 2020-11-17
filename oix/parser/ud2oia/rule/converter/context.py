"""
context
"""
from oix.parser.support.rule.workflow import WorkFlowContext
from loguru import logger

class UD2OIAContext(WorkFlowContext):
    """
    CTB2OIAContext
    """
    def __init__(self):

        self.debugger = None

        self.processed_edges = set()

    def processed(self, start, end):
        """

        @param start:
        @type start:
        @param end:
        @type end:
        @return:
        @rtype:
        """
        logger.debug("set processed: {0} {1}".format(start.ID, end.ID))
        self.processed_edges.add((start.ID, end.ID))

    def is_processed(self, start, end):
        """

        @param start:
        @type start:
        @param end:
        @type end:
        @return:
        @rtype:
        """
        return (start.ID, end.ID) in self.processed_edges