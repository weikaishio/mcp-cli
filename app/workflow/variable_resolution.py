from app.workflow.workflow_exception import WorkflowException


class VariableResolutionError(WorkflowException):
    def __init__(self, expression):
        super().__init__("变量解析", f"无法解析表达式: {expression}")