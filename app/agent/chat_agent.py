import asyncio

import time

class ChatAgent:
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
        self.tools = [
            {"name": "maps_geo", "desc": "地理编码服务"},
            {"name": "maps_around_search", "desc": "周边搜索服务"},
            {"name": "maps_direction_walking", "desc": "步行导航服务"}
        ]

    async def process_query(self, query):
        tool_chain = await self._generate_tool_chain(query)

        results = []
        for tool_call in tool_chain:
            result = await self.mcp_client.call_tool(
                tool_call['tool'],
                tool_call['args']
            )
            results.append(result)

        return "\n\n".join(results)

    async def _generate_tool_chain(self, query):
        if "附近" in query:
            return [
                {"tool": "maps_geo", "args": {"address": query.split("附近")[0]}},
                {"tool": "maps_around_search", "args": {"keywords": "连锁酒店", "radius": 3000, "location": "120.754559,37.824651"}}
            ]
        return []


async def main():
    from app.tools.amap_mcp_client import AmapMCPClient
    client = AmapMCPClient()
    await client.connect()

    agent = ChatAgent(client)

    response = await agent.process_query("济南奥体中心附近3km的经济型酒店")
    print(response)
    await client.close()
    print("Session closed.")
    time.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())