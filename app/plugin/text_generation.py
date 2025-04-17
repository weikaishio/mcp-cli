import time
from typing import Dict

from app.plugin.llm import BaseModelAPI
from app.plugin.workflow_node import WorkflowNode


class TextGenerationNode(WorkflowNode):
    """文本生成工作流节点"""

    def __init__(self, name: str, api_client: BaseModelAPI, max_retries: int = 3):
        super().__init__(name, api_client)
        self.max_retries = max_retries

    def execute(self, ** kwargs) -> Dict:
        """执行文本生成任务"""
        prompt = kwargs.get("prompt", "")
        max_tokens = kwargs.get("max_tokens", 100)

        if not prompt:
            raise ValueError("Prompt cannot be empty")

        attempt = 1
        last_exception = None

        while attempt <= self.max_retries:
            try:
                self.logger.info(
                    f"[{self.name}] Attempt {attempt} of {self.max_retries}"
                )
                result = self.api_client.generate(prompt, max_tokens)
                return {
                    "status": "success",
                    "data": result,
                    "node": self.name,
                    "attempt": attempt
                }

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"[{self.name}] Execution failed (attempt {attempt}): {str(e)}"
                )
                time.sleep(2 ** attempt)  # 指数退避

                attempt += 1

        self.logger.error(f"[{self.name}] All attempts failed")
        return {
            "status": "failed",
            "error": str(last_exception),
            "node": self.name,
            "attempt": self.max_retries
        }
