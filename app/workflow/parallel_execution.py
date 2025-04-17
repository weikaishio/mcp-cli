from typing import List

from app.workflow.workflow_exception import WorkflowException


class ParallelExecutionError(WorkflowException):
    def __init__(self, errors: List[Exception]):
        error_msgs = ", ".join([str(e) for e in errors])
        super().__init__("parallel", f"部分子步骤失败: {error_msgs}")
        self.errors = errors