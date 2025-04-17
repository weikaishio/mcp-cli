import gradio as gr
import json
from typing import List, Dict

# 步骤类型定义
STEP_TYPES = ["", "HTTP请求", "HTML解析", "文本处理"]
MODULE_MAP = {
    "":"",
    "HTTP请求": "http_requester",
    "HTML解析": "html_parser",
    "文本处理": "text_processor"
}

current_workflow = []

# 预定义所有参数组件
with gr.Blocks() as demo:
    gr.Markdown("## 工作流配置工具")

    # 状态存储
    current_step_type = gr.State("HTTP请求")
    param_values = gr.State({})

    # 步骤类型选择
    with gr.Row():
        step_type = gr.Dropdown(
            label="步骤类型",
            choices=STEP_TYPES,
            value=""
        )

    # 预定义所有参数面板
    with gr.Row(visible=False) as http_panel:
        http_method = gr.Dropdown(
            label="方法",
            choices=["GET", "POST"],
            value="GET"
        )
        http_url = gr.Textbox(label="URL")
        http_content_type = gr.Dropdown(
            label="Content-Type",
            choices=["none", "json"],
            value="none"
        )

    with gr.Row(visible=False) as html_panel:
        html_content = gr.Textbox(label="内容变量")
        html_selector = gr.Textbox(label="CSS选择器")
        html_attribute = gr.Dropdown(
            label="属性",
            choices=["text", "href", "src"],
            value="text"
        )

    with gr.Row(visible=False) as text_panel:
        text_inputs = gr.Textbox(
            label="输入变量（JSON格式）",
            placeholder='{"content": "${var}"}',
            lines=2
        )
        text_template = gr.Textbox(label="模板")

    # 控制面板
    with gr.Row():
        add_btn = gr.Button("添加步骤")
        export_btn = gr.Button("生成配置文件")

    # 输出显示
    workflow_display = gr.Textbox(
        label="当前工作流",
        lines=10,
        interactive=False
    )
    file_output = gr.File(label="配置文件下载")


    # 更新参数面板可见性
    def update_panels(step_type: str):
        visibility = {
            "HTTP请求": [True, False, False],
            "HTML解析": [False, True, False],
            "文本处理": [False, False, True]
        }
        vis = visibility.get(step_type, [False] * 3)
        return [
            gr.Row.update(visible=vis[0]),  # HTTP面板
            gr.Row.update(visible=vis[1]),  # HTML面板
            gr.Row.update(visible=vis[2])  # 文本面板
        ]


    step_type.change(
        fn=update_panels,
        inputs=step_type,
        outputs=[http_panel, html_panel, text_panel]
    )


    # 收集参数值
    def collect_params(step_type: str, *args):
        params = {}
        if step_type == "HTTP请求":
            params = {
                "method": args[0],
                "url": args[1],
                "content_type": args[2]
            }
        elif step_type == "HTML解析":
            params = {
                "content": args[3],
                "selector": args[4],
                "attribute": args[5]
            }
        elif step_type == "文本处理":
            try:
                inputs = json.loads(args[6])
            except json.JSONDecodeError as e:
                raise gr.Error(f"JSON解析错误: {str(e)}")
            params = {
                "inputs": inputs,
                "template": args[7]
            }
        return params


    # 添加步骤到工作流
    def add_step(step_type: str, *args):
        params = collect_params(step_type, *args)
        module = MODULE_MAP[step_type]

        step_config = {
            "module": module,
            "params": params,
            "output_var": "result"
        }

        current_workflow.append(step_config)
        display = "\n".join([
            f"步骤{i + 1}: {s['module']}\n参数: {json.dumps(s['params'], indent=2)}"
            for i, s in enumerate(current_workflow)
        ])
        return display


    # 绑定添加按钮
    add_btn.click(
        fn=add_step,
        inputs=[
            step_type,
            http_method, http_url, http_content_type,
            html_content, html_selector, html_attribute,
            text_inputs, text_template
        ],
        outputs=workflow_display
    )


    # 生成配置文件
    def export_config():
        config = {"workflow": current_workflow}
        with open("workflow.json", "w") as f:
            json.dump(config, f, indent=2)
        return "workflow.json"


    export_btn.click(
        fn=export_config,
        outputs=file_output
    )

if __name__ == "__main__":
    demo.launch()