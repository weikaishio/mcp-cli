import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException


class BaseModelAPI(ABC):

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1/chat/completions", timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()

    def _setup_logging(self):
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        pass

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
            if data.get("error"):
                self.logger.error(f"API Error: {data['error']}")
                raise RuntimeError(data["error"])
            return data
        except requests.exceptions.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON response: {response.text}")
            raise ValueError("Invalid JSON response")


class LLM(BaseModelAPI, ABC):
    """GPT模型API实现"""
    def generate(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """调用GPT API生成内容"""
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }

        try:
            self.logger.info(f"Sending request to GPT API: {prompt[:50]}...")

            response = self.session.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = self._handle_response(response)

            self.logger.info(
                f"GPT API Response: {result['choices'][0]['message']['content'][:50]}..."
            )
            self.logger.debug(f"API Response: {result}")

            return result

        except RequestException as e:
            self.logger.error(f"Network error occurred: {str(e)}")
            raise ConnectionError(f"API request failed: {str(e)}")
        finally:
            duration = round(time.time() - start_time, 4)
            self.logger.info(f"API Call Duration: {duration}s")