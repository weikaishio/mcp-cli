import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from app.plugin.html_resolver import HtmlParser
from app.plugin.http_requester import HttpRequester
from app.plugin.llm import BaseModelAPI, LLM
from app.plugin.text_generation import TextGenerationNode
from app.plugin.text_process import TextProcessor
from app.workflow.variable_resolution import VariableResolutionError
from app.workflow.workflow_exception import WorkflowException


class StepType:
    SINGLE = "single"
    PARALLEL = "parallel"


class WorkflowEngine:
    def __init__(self, api_client: BaseModelAPI):
        self.http_requester = HttpRequester("HttpRequester", api_client)
        self.html_parser = HtmlParser("HtmlParser", api_client)
        self.text_processor = TextProcessor("TextProcessor", api_client)
        self.text_generation = TextGenerationNode("TextGeneration", api_client)
        self.context = {}

    def _resolve_parameters(self, params: Dict, context: Dict = None) -> Dict:
        """支持指定上下文快照的解析"""
        context = context or self.context
        return {
            k: self._deep_resolve(v, context)
            for k, v in params.items()
        }

    def _deep_resolve(self, value, context: Dict):
        """递归解析嵌套结构"""
        if isinstance(value, str) and value.startswith('${'):
            return self._resolve_variable(value, context)
        elif isinstance(value, dict):
            return {k: self._deep_resolve(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deep_resolve(v, context) for v in value]
        else:
            return value

    def _resolve_variable(self, expression: str, context: Dict):
        """解析变量表达式"""
        path = expression[2:-1].split('.')
        current = context
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                current = getattr(current, key, None)
            if current is None:
                raise VariableResolutionError(expression)
        return current

    def execute_flow(self, flow_config: List[Dict]):
        for step in flow_config:

            if step.get("type") == StepType.PARALLEL:
                self._execute_parallel_step(step)
            else:
                self._execute_single_step(step)

    def _execute_parallel_step(self, step_config: Dict):
        # 获取线程安全的当前上下文快照
        context_snapshot = self.context.copy()

        with ThreadPoolExecutor() as executor:
            # 提交所有子任务
            futures = []
            for substep in step_config["steps"]:
                # 预解析参数（基于快照上下文）
                resolved_params = self._resolve_parameters(
                    substep["params"],
                    context=context_snapshot
                )
                if substep['module'] == 'html_parser':
                    if not isinstance(substep["params"]['content'], str):
                        raise TypeError("HTML解析需要字符串类型的content参数")
                # 提交任务
                # print(f"module:{substep['module']}\n resolved_params:{resolved_params}")
                future = executor.submit(
                    self._run_isolated_substep,
                    substep["module"],
                    resolved_params
                )
                futures.append((future, substep.get("output_var")))

            # 收集结果
            aggregated_results = {}
            for future, output_var in futures:
                try:
                    f_result = future.result()
                    if output_var:
                        self.context[output_var] = f_result
                    aggregated_results[output_var] = f_result
                except Exception as e:
                    raise WorkflowException("parallel", str(e))

            # 存储聚合结果
            # print(f"aggregated_results:{aggregated_results}")
            self.context[step_config["output_var"]] = {
                "list": [r for _, r in aggregated_results.items()],
                "dict": aggregated_results
            }

    def _execute_single_step(self, step_config: Dict):
        """执行单个工作流步骤"""
        try:
            module = getattr(self, step_config["module"])

            resolved_params = self._resolve_parameters(
                step_config["params"]
            )

            if module == 'html_parser':
                if not isinstance(resolved_params['content'], str):
                    raise TypeError("HTML解析需要字符串类型的content参数")

            result = module.execute(**resolved_params)

            self._validate_status(result, step_config["module"])

            if "output_var" in step_config:
                self.context[step_config["output_var"]] = result

            return result

        except Exception as e:
            raise WorkflowException(
                step=step_config["module"],
                error=f"执行失败: {str(e)}"
            )

    def _validate_status(self, result: dict, module_name: str):
        """统一状态校验逻辑"""
        status_key = "statusCode" if module_name == "http_requester" else "status"
        if status_key in result and result[status_key] != 200:
            raise WorkflowException(
                step=module_name,
                error=f"异常状态码: {result[status_key]}"
            )

    def _run_isolated_substep(self, module_name: str, params: Dict):
        """线程隔离的执行环境"""
        module = getattr(self, module_name)
        return module.execute(**params)

    def execute_flow_x(self, flow_config: List[Dict]):
        """
        执行工作流
        :param flow_config: JSON格式流程配置
        """
        global result
        for step in flow_config:
            module = getattr(self, step['module'])
            try:
                resolved_params = self._resolve_parameters(step['params'])
                if step['module'] == 'html_parser':
                    if not isinstance(resolved_params['content'], str):
                        raise TypeError("HTML解析需要字符串类型的content参数")
                result = module.execute(**resolved_params)
            except Exception as e:
                raise WorkflowException(step['module'], str(e))
            finally:
                if "statusCode" in result:
                    if int(result["statusCode"]) != 200:
                        raise WorkflowException(step['module'], f"HTTP请求失败，状态码: {result['statusCode']}")
                if "status" in result:
                    if int(result["status"]) != 200:
                        raise WorkflowException(step['module'], f"处理失败")
                self.context.update({step['output_var']: result})


if __name__ == "__main__":
    api_key = "your_openai_api_key_here"
    gpt_client = LLM(api_key=api_key, timeout=15)
    engine = WorkflowEngine(gpt_client)
    novel_search_flow = [
        {
            "module": "http_requester",
            "params": {
                "method": "GET",
                "url": "https://novelbin.com/search",
                "params": {"keyword": "An Alchemist's Path to Eternity"},
                "content_type": "none"
            },
            "output_var": "search_result"
        },
        {
            "module": "html_parser",
            "params": {
                "content": "${search_result.body}",  # 引用上一步结果
                "selector": ".novel-title a",
                "attribute": "text"
            },
            "output_var": "result"
        },
        {
            "module": "text_processor",
            "params": {
                "inputs": {"content": "${result.value}"},
                "template": "小说条目: {content}\n"
            },
            "output_var": "final_output"
        }
    ]
    try:
        engine.execute_flow(novel_search_flow)
        print(engine.context['final_output'])
    except WorkflowException as e:
        print(f"流程中断于{e.step}，错误：{str(e)}")