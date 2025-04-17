import json
from typing import Dict, Any

from app.plugin.llm import LLM
from app.workflow.workflow_engine import WorkflowEngine, StepType

def test_single_execution():
    xiaochuan_slogn_flow =  [
    {
      "module": "http_requester",
      "params": {
        "method": "GET",
        "url": "https://www.quetta.net/",
        "content_type": "none"
      },
      "output_var": "result"
    },
    {
      "module": "html_parser",
      "params": {
        "content": "${result.body}",
        "selector": ".framer-styles-preset-1wh8wit span",
        "attribute": "text"
      },
      "output_var": "result"
    },
    {
      "module": "text_processor",
      "params": {
        "inputs": {"content": "${result.value}"},
        "template": "quetta's slogon: {content}"
      },
      "output_var": "result"
    }
  ]
    with open("/Users/timwang/xiaochuan/workspace/browser/ai_workflow/workflow.json", "r") as f:
        json_content = f.read()
        xiaochuan_slogn_flow = json.loads(json_content)["workflow"]

    print(f"xiaochuan_slogn_flow:{xiaochuan_slogn_flow}")
    api_key = "your_openai_api_key_here"
    gpt_client = LLM(api_key=api_key, base_url="https://api.openai.com/v1/chat/completions", timeout=15)
    engine = WorkflowEngine(gpt_client)
    engine.execute_flow(xiaochuan_slogn_flow)
    assert "result" in engine.context
    print(engine.context['result'])

def test_parallel_execution():
    engine = WorkflowEngine()

    class MockParser:
        def execute(self, ** kwargs) -> Dict[str, Any]:
            return {"value": "mock value", "status": 200, "error": "", "duration": 0.0}

    # engine.html_parser = MockParser()

    flow = [
        {
            "module": "http_requester",
            "params": {
                "method": "GET",
                "url": "https://www.quetta.net/",
                "content_type": "none"
            },
            "output_var": "response"
        },
        {
            "type": StepType.PARALLEL,
            "steps": [
                {
                    "module": "html_parser",
                    "params": {
                        "content": "${response.body}",
                        "selector": ".framer-styles-preset-1wh8wit span",
                        "attribute": "text"
                    },
                    "output_var": "slogon"
                },
                {
                    "module": "html_parser",
                    "params": {
                        "content": "${response.body}",
                        "selector": ".framer-1m5dm46 p",
                        "attribute": "text"
                    },
                    "output_var": "private"
                }
            ],
            "output_var": "parsed_data"
        },
        {
            "module": "text_processor",
            "params": {
                "inputs": {"slogon": "${slogon.value}", "private": "${private.value}"},
                "template": "quetta's slogon: {slogon}\nquetta's private: {private}\n"
            },
            "output_var": "final_output"
        }
    ]

    engine.execute_flow(flow)
    assert "parsed_data" in engine.context
    assert len(engine.context["parsed_data"]) == 2
    assert "slogon" in engine.context
    assert "private" in engine.context
    print(engine.context['final_output'])


if __name__ == "__main__":
    test_single_execution()