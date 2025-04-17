# 同样用python实现文本处理器，用于处理多个字符串类型变量的格式。作为智能体工作流中的一个节点，支持多个输入变量，并支持字符串拼接模板用上输入的变量。同样需要用到面向对象设计，代码健壮性，异常捕获，日志，执行时长等
import logging
import time
from typing import List, Union, Dict
from functools import wraps

from app.plugin.llm import BaseModelAPI
from app.plugin.workflow_node import WorkflowNode


class TextProcessorError(Exception):
    """自定义文本处理异常基类"""
    pass


class TextProcessor(WorkflowNode):
    """文本处理器（支持多字符串拼接与格式处理）"""

    def __init__(self, name: str, api_client: BaseModelAPI, logger_name: str = "TextProcessor"):
        super().__init__(name, api_client)
        self._init_logger(logger_name)
        self.operations = {
            'concat': self.concatenate,
            'upper': self.to_upper,
            'strip': self.remove_whitespace
        }

    def _init_logger(self, name: str):
        """配置日志记录器（参考网页12/13/14）"""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(console_handler)

    def _validate_input(self, inputs: List[str]):
        """输入验证（参考网页9/10/11）"""
        if not isinstance(inputs, list):
            raise TextProcessorError("输入必须为字符串列表")
        if any(not isinstance(s, str) for s in inputs):
            raise TextProcessorError("列表元素必须为字符串类型")

    def _timing_decorator(func):
        """执行时长监控装饰器（参考网页15/16）"""

        @wraps(func)
        def wrapper(self, *args,  ** kwargs):
            start_time = time.perf_counter()
            result = func(self, *args,  ** kwargs)
            duration = time.perf_counter() - start_time
            self.logger.debug(
                f"{func.__name__} 执行耗时: {duration:.4f}秒")
            return result

        return wrapper

    @_timing_decorator
    def concatenate(self, inputs: List[str], delimiter: str = '') -> str:
        """
        多字符串拼接
        :param inputs: 输入字符串列表
        :param delimiter: 连接符（默认空）
        :return: 拼接结果字符串
        """
        try:
            self._validate_input(inputs)
            return delimiter.join(inputs)
        except TextProcessorError as e:
            self.logger.error(f"拼接失败: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            self.logger.critical(f"未知错误: {str(e)}", exc_info=True)
            raise TextProcessorError("系统内部错误") from e

    @_timing_decorator
    def execute(self, ** kwargs) -> str:
        """
        self, template: str, params: Dict[str, str]
        模板化字符串生成（参考网页3/5）
        :param template: 含占位符的模板字符串
        :param params: 参数字典
        :return: 格式化后的字符串
        """
        try:
            template = kwargs.get('template')
            if not isinstance(template, str):
                raise TextProcessorError("模板必须为字符串类型")

            inputs = kwargs.get('inputs', {})
            missing_keys = [k for k in inputs if f'{{{k}}}' not in template]
            if missing_keys:
                raise TextProcessorError(f"模板缺失参数: {missing_keys}")

            return template.format(**inputs)
        except KeyError as e:
            error_msg = f"参数缺失: {str(e)}"
            self.logger.error(error_msg)
            raise TextProcessorError(error_msg)
        except Exception as e:
            self.logger.error(f"模板处理错误: {str(e)}")
            raise

    @_timing_decorator
    def to_upper(self, inputs: Union[str, List[str]]) -> Union[str, List[str]]:
        """批量转大写（参考网页5）"""
        if isinstance(inputs, str):
            return inputs.upper()
        return [s.upper() for s in inputs]

    @_timing_decorator
    def remove_whitespace(self, inputs: Union[str, List[str]],
                          mode: str = 'both') -> Union[str, List[str]]:
        """
        去除空白字符（参考网页3/5）
        :param mode: both/left/right
        """
        modes = {'both': str.strip,
                 'left': str.lstrip,
                 'right': str.rstrip}

        if mode not in modes:
            raise TextProcessorError(f"无效模式: {mode}，可选: {list(modes.keys())}")

        processor = modes[mode]
        if isinstance(inputs, str):
            return processor(inputs)
        return [processor(s) for s in inputs]

    def batch_process(self, operations: List[Dict]) -> str:
        """
        批量处理管道（参考网页4/5）
        :param operations: 操作指令列表
            [{'type':'concat', 'params':{'inputs':[...], 'delimiter':','}},
             {'type':'upper'}]
        """
        result = []
        try:
            for op in operations:
                func = self.operations.get(op['type'])
                if not func:
                    raise TextProcessorError(f"无效操作类型: {op['type']}")
                result = func(**op.get('params', {}))
            return result
        except KeyError as e:
            self.logger.error(f"操作指令格式错误: {str(e)}")
            raise TextProcessorError("指令缺少必要参数")


# 使用示例
if __name__ == "__main__":
    processor = TextProcessor()

    # 字符串拼接
    # try:
    #     print(processor.concatenate(["Hello", "World"], delimiter=", "))
    #     # 输出: Hello, World
    # except TextProcessorError as e:
    #     print(f"处理失败: {str(e)}")

    # 模板格式化
    template = "用户{name}于{time}登录系统"
    params = {"name": "张三", "time": "2025-03-31 14:30"}
    print(processor.execute(template=template, inputs=params))

    # # 批量处理流水线
    # pipeline = [
    #     {'type': 'concat', 'params': {'inputs': ['  apple ', ' banana ']}},
    #     {'type': 'strip', 'params': {'mode': 'both'}},
    #     {'type': 'upper'}
    # ]
    # print(processor.batch_process(pipeline))  # 输出: ['APPLE', 'BANANA']