"""
workflow
"""

from loguru import logger


class WorkFlow(object):
    """
    DebuggableWorkFlow
    """

    def __init__(self, workflow):

        self.workflow = workflow
        self.workflow_names = set(self.processor_name(x) for x in self.workflow)

    def processor_name(self, x):
        """

        @param x:
        @return:
        """
        try:
            return x.__name__
        except:
            return type(x).__name__

    def working_stack(self):
        """

        :return:
        """
        import inspect

        info = []
        for call in inspect.stack():
            if call.function in self.workflow_names:

                info.append(call.function + ":" + str(call.lineno))

        return info  # convertion_func_name


class WorkFlowOptions(object):
    """
    WorkFlowOptions
    """

    def __init__(self):

        self.uri = None
        self.debug = False
        self.info = False


class WorkFlowContext(object):
    """
    WorkFlowContext
    """
    pass

