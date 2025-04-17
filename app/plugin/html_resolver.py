# 同样用python实现一个html解析器，作为智能体工作流中的一个节点，传入html字符串 css选择器和选择器index下标 返回对应元素的属性，同样需要用到面向对象设计，代码健壮性，异常捕获，日志，执行时长等
import logging
import time
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup, FeatureNotFound
from bs4.element import Tag

from app.plugin.llm import BaseModelAPI
from app.plugin.workflow_node import WorkflowNode


class HtmlParserException(Exception):
    pass


class HtmlParser(WorkflowNode):

    def __init__(self, name: str, api_client: BaseModelAPI):
        super().__init__(name, api_client)
        self.logger = logging.getLogger("HtmlParser")
        self._init_logger()

    def _init_logger(self):
        """配置日志记录器"""
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # 文件日志
        file_handler = logging.FileHandler('html_parser.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 控制台日志
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _safe_parse(self, html: str) -> BeautifulSoup:
        try:
            self.logger.info(f"开始解析HTML文档，长度：{len(html)}字节")
            start_time = time.time()
            soup = BeautifulSoup(html, 'lxml')  # 使用性能更好的lxml解析器
            parse_time = round(time.time() - start_time, 4)
            self.logger.debug(f"HTML解析完成，耗时{parse_time}秒")
            return soup
        except FeatureNotFound as e:
            self.logger.critical("缺少lxml解析器，请执行 pip install lxml")
            raise HtmlParserException("依赖缺失：lxml解析器未安装") from e
        except Exception as e:
            self.logger.error(f"HTML解析失败：{str(e)}")
            raise HtmlParserException("文档解析异常") from e

    def execute(self, ** kwargs) -> Dict[str, Any]:
        """
        获取指定元素的属性值

        Args:
            css_selector: CSS选择器语法
            index: 元素下标（默认首个元素）
            attribute: 目标属性名，默认取文本内容

        Returns:
            {
                "value": str,     # 属性值
                "status": int,    # 状态码（200成功，404未找到等）
                "error": str,     # 错误信息
                "duration": float # 执行耗时
            }
        """
        result = {"value": None, "status": 200, "error": "", "duration": 0.0}
        start_time = time.time()

        try:
            html_content = kwargs.get("content", "")
            self.soup = self._safe_parse(html_content)
            css_selector = kwargs.get("selector", "")
            if not css_selector:
                raise ValueError("CSS选择器不能为空")
            index = kwargs.get("index", 0)
            if index < 0:
                raise ValueError("元素下标必须为非负整数")

            self.logger.debug(f"执行选择器：'{css_selector}' [index={index}]")

            # 定位元素
            elements = self.soup.select(css_selector)
            if not elements:
                result["status"] = 404
                raise ValueError(f"未找到匹配元素：{css_selector}")

            if index >= len(elements):
                result["status"] = 416
                raise IndexError(f"元素下标越界（最大{len(elements) - 1}）")

            target = elements[index]

            attribute = kwargs.get("attribute", "text")
            if attribute == "text":
                value = target.get_text(strip=True)
            elif isinstance(target, Tag):
                value = target.get(attribute, "")
            else:
                value = str(target)

            result["value"] = value

        except (ValueError, IndexError) as e:
            result["error"] = str(e)
            self.logger.warning(f"元素定位失败：{str(e)}")
        except Exception as e:
            result["status"] = 500
            result["error"] = "内部解析错误"
            self.logger.error(f"未处理异常：{str(e)}", exc_info=True)
        finally:
            result["duration"] = round(time.time() - start_time, 4)
            return result


if __name__ == "__main__":
    html = ""
    parser = HtmlParser()
    print(parser.execute(content=html, selector=".framer-styles-preset-1wh8wit span", attribute="text"))