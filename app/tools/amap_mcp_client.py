import json
import asyncio
from contextlib import AsyncExitStack
from typing import List

from mcp.client.sse import sse_client
from mcp import ClientSession


class AmapMCPClient:
    def __init__(self):
        self.api_key = "2f9f24d6a844c27f5d1d93188f04566c"
        self.session = None
        self._exit_stack = AsyncExitStack()

    async def close(self):
        if hasattr(self, '_closed') and self._closed:
            return

        try:
            if self._exit_stack:
                await self._exit_stack.aclose()

            if self.session and hasattr(self.session, 'close'):
                await self.session.close()

        except Exception as e:
            print(f"关闭连接时异常: {str(e)}\n")
            raise
        finally:
            self._closed = True
            self.session = None
            self._exit_stack = None

    async def connect(self):
        server_config = {
            "mcpServers": {
                "amap-sse": {
                    "url": f"https://mcp.amap.com/sse?key={self.api_key}"
                }
            }
        }

        sse_cm = sse_client(server_config["mcpServers"]["amap-sse"]["url"])
        streams = await self._exit_stack.enter_async_context(sse_cm)

        session_cm = ClientSession(streams[0], streams[1])
        self.session = await self._exit_stack.enter_async_context(session_cm)
        await self.session.initialize()

    def _validate_args(self, tool_name: str, args: dict) -> dict:
        validated = args.copy()

        if "key" not in validated:
            validated["key"] = self.api_key

        if tool_name == "maps_around_search":
            if "location" not in validated:
                raise ValueError("周边搜索必须包含location参数")
            if "keywords" not in validated and "types" not in validated:
                raise ValueError("需指定keywords或types参数")
            validated["radius"] = int(validated.get("radius", 3000))

        elif tool_name == "maps_geo":
            if "address" not in validated:
                raise ValueError("地理编码必须包含address参数")

        return validated

    async def call_tool(self, tool_name, args):
        try:
            validated_args = self._validate_args(tool_name, args)
            result = await self.session.call_tool(tool_name, validated_args)
            try:
                if not result.content or not isinstance(result.content, List):
                    raise ValueError("Invalid content structure")

                text_content = result.content[0].text

                json_str = text_content.split('text=')[-1].strip()

                return self._format_result(tool_name, json.loads(json_str))

            except (AttributeError, IndexError, json.JSONDecodeError) as e:
                raise RuntimeError(f"数据解析失败: {str(e)}") from e

            # print(f"{tool_name}返回数据: {dir(result)}\n\n")
            # return_result = result.get("result") if isinstance(result, dict) else str(result)
            #
            # return self._format_result(tool_name,return_result)

        except asyncio.CancelledError:
            await self.close()
            raise
        except json.JSONDecodeError:
            return "高德返回数据格式异常"
        except KeyError as e:
            return f"高德返回数据结构异常: {str(e)}"
        except Exception as e:
            return f"网络请求失败: {str(e)}"

    def _format_result(self, tool_name, data):
        print(f"{tool_name}\n\n")
        if tool_name == "maps_around_search":
            print(f"{tool_name}返回数据: {data['pois']}\n\n")
            return "\n".join([f"{i + 1}. {poi['name']} - 距离:米"
                              for i, poi in enumerate(data['pois'])])
        elif tool_name == "maps_direction_walking":
            return f"步行路线: {data['route']['paths'][0]['instructions']}"
        return json.dumps(data, ensure_ascii=False)
