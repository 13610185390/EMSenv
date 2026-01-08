# -*- coding: utf-8 -*-
"""储能EMS教学仿真平台 - 主入口文件

对应设计文档：开发规划文档 3.2节
"""

import gradio as gr
from config import APP_NAME, APP_VERSION


def create_app() -> gr.Blocks:
    """创建Gradio应用"""

    with gr.Blocks(
        title=APP_NAME,
        theme=gr.themes.Soft()
    ) as app:

        # 标题
        gr.Markdown(f"# {APP_NAME}")
        gr.Markdown(f"版本: {APP_VERSION}")

        # 标签页占位
        with gr.Tabs():
            with gr.Tab("基础参数"):
                gr.Markdown("*基础参数模块待实现*")

            with gr.Tab("经济参数"):
                gr.Markdown("*经济参数模块待实现*")

            with gr.Tab("控制策略"):
                gr.Markdown("*控制策略模块待实现*")

            with gr.Tab("仿真结果"):
                gr.Markdown("*仿真计算模块待实现*")

            with gr.Tab("教学引导"):
                gr.Markdown("*教学引导模块待实现*")

            with gr.Tab("EMS架构"):
                gr.Markdown("*EMS架构展示模块待实现*")

            with gr.Tab("故障诊断"):
                gr.Markdown("*故障诊断模块待实现*")

    return app


def main():
    """主函数"""
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
