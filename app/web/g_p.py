import gradio as gr
import json

STEP_TYPES = ["HTTP请求", "HTML解析", "文本处理", "并行步骤"]
MODULE_MAP = {st: st.lower() for st in STEP_TYPES}


class WorkflowBuilder:
    def __init__(self):
        self.workflow = []
        self.parallel_steps = []

    def add_step(self, step_type, params):
        # 实现步骤添加逻辑
        pass


builder = WorkflowBuilder()


def create_all_components():
    """预定义所有界面组件"""
    components = []
    # HTTP参数
    components.extend([
        gr.Dropdown(["GET", "POST"], label="方法", visible=False),
        gr.Textbox(label="URL", visible=False),
        gr.Dropdown(["none", "json"], label="Content-Type", visible=False)
    ])
    # HTML解析参数
    components.extend([
        gr.Textbox(label="内容变量", visible=False),
        gr.Textbox(label="CSS选择器", visible=False),
        gr.Dropdown(["text", "href"], label="属性", visible=False)
    ])
    # 文本处理参数
    components.extend([
        gr.Textbox(label="输入变量（JSON）", visible=False),
        gr.Textbox(label="模板", visible=False)
    ])
    return components


with gr.Blocks(title="工作流编辑器") as demo:
    gr.Markdown("## 工作流配置工具")

    # 预加载所有组件
    all_components = create_all_components()

    # 主界面布局
    with gr.Row():
        # 配置区
        with gr.Column():
            step_type = gr.Dropdown(STEP_TYPES, label="步骤类型")
            param_area = gr.Column()
            param_area.children = all_components  # 注入预定义组件
            add_btn = gr.Button("添加步骤")

        # 预览区
        with gr.Column():
            preview = gr.JSON(label="配置预览")
            export_btn = gr.Button("导出配置")
            file_out = gr.File(label="配置文件")


    # 可见性控制
    def update_ui(step_type):
        vis_rules = {
            "HTTP请求": [True] * 3 + [False] * 5,
            "HTML解析": [False] * 3 + [True] * 3 + [False] * 2,
            "文本处理": [False] * 6 + [True] * 2,
            "并行步骤": [False] * 8
        }
        return [gr.update(visible=v) for v in vis_rules[step_type]]


    step_type.change(
        update_ui,
        inputs=step_type,
        outputs=all_components
    )


    # 步骤添加逻辑
    def collect_params(step_type):
        param_map = {
            "HTTP请求": [all_components[i].value for i in range(3)],
            "HTML解析": [all_components[i].value for i in range(3, 6)],
            "文本处理": [all_components[i].value for i in range(6, 8)]
        }
        return param_map.get(step_type, [])


    def add_step_handler(step_type):
        params = collect_params(step_type)
        # 实现具体的步骤添加逻辑
        return gr.update(value=builder.workflow)


    add_btn.click(
        add_step_handler,
        inputs=step_type,
        outputs=preview
    )

    # 文件导出
    export_btn.click(
        lambda: ("workflow.json", json.dumps(builder.workflow, indent=2)),
        outputs=file_out
    )

if __name__ == "__main__":
    demo.launch()