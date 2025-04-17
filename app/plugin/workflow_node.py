import logging
from typing import Dict

from app.plugin.llm import BaseModelAPI


class WorkflowNode:
    """工作流节点基类"""

    def __init__(self, name: str, api_client: BaseModelAPI):
        self.name = name
        self.api_client = api_client
        self.logger = logging.getLogger(name)

    def execute(self, ** kwargs) -> Dict:
        """执行节点逻辑"""
        raise NotImplementedError