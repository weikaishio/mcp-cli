# 插件开发（包含通用的方法def execute(self, **kwargs) -> Any:），用python实现 http requester的插件，入参：method、url、params、headers、鉴权、请求体（none\json\form-data\x-www-form-urlencoded）.输出：body(string)、statusCode、headers(string)。需要用到面向对象设计，代码健壮性，异常捕获，日志，执行时长等

import json
import time
import logging
from typing import Any, Dict, Optional
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from app.plugin.llm import BaseModelAPI
from app.plugin.workflow_node import WorkflowNode


class HttpRequester(WorkflowNode):
    def __init__(self, name: str, api_client: BaseModelAPI):
        super().__init__(name, api_client)
        self.logger = logging.getLogger(__name__)
        self._init_logger()

    def _init_logger(self):
        """初始化日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("http_requester.log"),
                logging.StreamHandler()
            ]
        )

    def _prepare_request(self, method: str, url: str, params: Dict, headers: Dict, cookie: Optional[Dict],
                         auth: Optional[Dict], body: Any) -> requests.Request:
        """构造请求对象"""
        req = requests.Request(
            method=method.upper(),
            url=url,
            params=params,
            headers=headers,
            cookies=cookie,
            data=self._encode_body(body, headers)
        )

        if auth:
            req.auth = HTTPBasicAuth(auth.get('username'), auth.get('password'))

        return req.prepare()

    def _encode_body(self, body: Any, headers: Dict) -> Optional[str]:
        """处理不同请求体类型"""
        content_type = headers.get('Content-Type', '')

        if body is None:
            return None
        elif 'json' in content_type:
            return json.dumps(body)
        elif 'x-www-form-urlencoded' in content_type:
            return requests.compat.urlencode(body)
        else:  # form-data需要特殊处理
            return body  # 假设已处理为multipart格式

    def _record_metrics(self, start_time: float) -> float:
        """记录执行时长"""
        return time.perf_counter() - start_time

    def parse_options(self, headers=None):
        options = Options()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        for k, v in headers.items():
            options.add_argument(f'{k}={v}')
        return options

    def get_content_headless(self, url, headers=None):
        driver = webdriver.Chrome(options=self.parse_options(headers))  # , executable_path='/usr/local/bin/chromedriver'
        driver.set_page_load_timeout(15)

        driver.get(url)
        response = driver.page_source
        driver.quit()
        return response

    def execute(self, ** kwargs) -> Dict:
        """
        执行HTTP请求
        参数：
            method: HTTP方法 (GET/POST/PUT/DELETE)
            url: 请求地址
            params: URL参数
            headers: 请求头
            auth: 鉴权信息 {username, password}
            body: 请求体（支持None/JSON/Form-data/x-www-form-urlencoded）
        返回：
            {
                "body": string,
                "statusCode": int,
                "headers": string,
                "duration": float
            }
        """
        result = {"body": "", "statusCode": 0, "headers": "", "duration": 0.0}
        start_time = time.perf_counter()

        try:
            # 构造请求对象
            # response = self.get_content_headless(kwargs['url'], kwargs.get('headers', {}))
            req = self._prepare_request(
                method=kwargs.get('method', 'GET'),
                url=kwargs['url'],
                params=kwargs.get('params', {}),
                headers=kwargs.get('headers', {}),
                cookie=kwargs.get('cookie'),
                auth=kwargs.get('auth'),
                body=kwargs.get('body'),
            )

            # 发送请求[2,4](@ref)
            with requests.Session() as session:
                response = session.send(
                    req,
                    timeout=10,
                    verify=True  # 启用SSL验证
                )

            # 记录响应信息
            result.update({
                "statusCode": response.status_code,
                "body": response.text,
                "headers": str(response.headers),
                "duration": self._record_metrics(start_time)
            })
            # print(result["body"])

            # 记录成功日志[13](@ref)
            self.logger.info(
                f"Request succeeded | URL: {kwargs['url']} | "
                f"Status: {response.status_code} | Duration: {result['duration']:.2f}s"
            )

        except RequestException as e:
            # 异常处理[9,11](@ref)
            error_msg = f"Request failed: {str(e)}"
            result.update({
                "statusCode": e.response.status_code if e.response else 500,
                "body": error_msg
            })
            self.logger.error(error_msg)

        except Exception as e:
            # 处理未知异常
            error_msg = f"Unexpected error: {str(e)}"
            result.update({"statusCode": 500, "body": error_msg})
            self.logger.exception("Critical error occurred")

        finally:
            result["duration"] = self._record_metrics(start_time)
            return result


# 使用示例
if __name__ == "__main__":
    plugin = HttpRequester()

    response = plugin.execute(
        method="GET",
        url="https://novelbin.com/search",
        params={"keyword": "An Alchemist's Path to Eternity"},
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "referer": "https://novelbin.com/search?keyword=An+Alchemist%27s+Path+to+Eternity",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-arch": '"x86"',
            "sec-ch-ua-bitness": '"64"',
            "sec-ch-ua-full-version": '"134.0.6998.166"',
            "sec-ch-ua-full-version-list": '"Chromium";v="134.0.6998.166", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.166"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": '""',
            "sec-ch-ua-platform": '"macOS"',
            "sec-ch-ua-platform-version": '"12.7.2"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        },
        cookies={
            "_ga": "GA1.1.2055941430.1743392782",
            "_gaClientId": "2055941430.1743392782",
            "_csrf": "iWHPFwkxQz0kry9ZPzWntCXm",
            "connect.sid": "s%3AzjmMb8HMXJjCOcYwMsOcXWioFqd0dSoW.P0MduauigdNiUFkXlqMMFuSMuB8Li1x6NVlbTvNs9lk",
            "cf_clearance": "gbub7ipwPaFB7WquqaAKZEtN50Tg1FrwXx8zS8qhNWM-1743422219-1.2.1.1-xzfKk_GZpswdq_azMoNlreXQc9WzU.QbLopAhX0tonpfM9unM8JxtifdG6.y__vllWHX9I4xLxXY6jHpW_4L9UEB6.o51JNbiGOJ9nXN.cPSBCLGcM4QpwXWi1UdO8dnnVFVE2ebMs1hBc6o_KKoO7XY_meuE8jyNw5cu1h0cjKik5YC3XH8oMi37Nwwa5lFOM7XqfP_jfVewfRDJiWnIQ9jQVAaEBFUmBckW237R4MgExX3rMSqUhZiEluNUnCdL91TNxX0tW.653gaLhL2w4xzaHCAUGoxd894R3kXFSSlP5BCP0bVSBg5SbVC9iS4iBRtfwdXAaR_AvRL6EedRkN4CV5HFwrTARgA4PKdtCjtEAdT68p7XZc3oYT1pZKisW2ZU6asjBxlJMZEdTsKMvBqxVVFSe4tI35J51sSs8E",
            "_ga_15YCML7VSC": "GS1.1.1743422219.4.1.1743422340.0.0.0"
        }
        # auth={"username": "admin", "password": "secret"},
        # body={"key": "value"}
    )

    print(json.dumps(response, indent=2))