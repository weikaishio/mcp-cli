class WorkflowException(Exception):
    def __init__(self, step: str, error: str):
        super().__init__(f"步骤{step}, 执行失败: {error}")
        self.step = step