import sys
import os
import gradio as gr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import ArgumentParser, LOG
from translator import PDFTranslator, TranslationConfig

global Translator

def translation(input_file, output_file_format, pages, source_language, target_language, style):
    LOG.debug(f"[翻译任务]\n源文件: {input_file}\n源语言: {source_language}\n目标语言: {target_language}\n输出文件格式: {output_file_format}\n翻译页数: {pages}\n翻译风格: {style}")
    if not os.path.exists(input_file):
        return "文件不存在", None
    if not pages or pages == 0:
        # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
        output_file_path = Translator.translate_pdf(
            input_file, source_language=source_language, target_language=target_language,
            output_file_format=output_file_format, style=style)

    if pages and pages < 0:
        return "翻译页数必须大于等于1", None
    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    else :
        output_file_path = Translator.translate_pdf(
        input_file, source_language=source_language, target_language=target_language,
            output_file_format=output_file_format, pages=pages, style=style)

    return "翻译成功", output_file_path

def openai_config(api_key, api_url, model_name):
    global Translator
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_URL"] = api_url
    Translator = PDFTranslator("openai", model_name)

def ollama_config(model_name):
    global Translator
    Translator = PDFTranslator("ollama", model_name)

def update_visibility(selected_option):
    if selected_option == "openai":
        return gr.update(visible=True), gr.update(visible=False)
    elif selected_option == "ollama":
        return gr.update(visible=False), gr.update(visible=True)

def launch_gradio():
    with gr.Blocks() as iface:
        with gr.Tab(label="翻译选项"):
            gr.Interface(
                fn=translation,
                title="OpenAI-Translator v2.0(PDF 电子书翻译工具)",
                inputs=[
                    gr.File(label="上传PDF文件"),
                    gr.Radio(label="输出文件格式", choices=["markdown", "pdf"], type="value", value="markdown"),
                    gr.Number(label="翻译页数", step=1, minimum=0),
                    gr.Textbox(label="源语言（默认：英文）", placeholder="English", value="English"),
                    gr.Textbox(label="目标语言（默认：中文）", placeholder="Chinese", value="Chinese"),
                    gr.Textbox(label="翻译风格", placeholder="Official", value="Official")
                ],
                outputs=[
                    gr.Textbox(label="翻译结果"),
                    gr.File(label="下载翻译文件")
                ],
                flagging_mode="never"
            )
        with gr.Tab(label="模型配置"):
            model_type = gr.Radio(label="选择使用的模型库", interactive=True, choices=["ollama", "openai"], type="value", value="openai")
            with gr.Group(visible=False) as openai_group:
                gr.Interface(
                    title="OpenAI 配置",
                    fn=openai_config,
                    inputs=[
                        gr.Textbox(label="API Key", placeholder="请输入API Key"),
                        gr.Textbox(label="API URL", placeholder="请输入API URL"),
                        gr.Dropdown(label="选择翻译模型", choices=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                                    type="value")
                    ],
                    outputs=[],
                    flagging_mode="never"
                )
            with gr.Group(visible=False) as ollama_group:
                gr.Interface(
                    title="Ollama 配置",
                    fn=ollama_config,
                    inputs=[ gr.Dropdown(label="选择翻译模型", choices=["glm4", "EntropyYue/chatglm3"], type="value") ],
                    outputs=[],
                    flagging_mode="never"
                )
            model_type.change(fn = update_visibility, inputs=model_type, outputs=[openai_group, ollama_group])



    iface.launch()

def initialize_translator():
    # 解析命令行
    argument_parser = ArgumentParser()
    args = argument_parser.parse_arguments()

    # 初始化配置单例
    config = TranslationConfig()
    config.initialize(args)    
    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    global Translator
    Translator = PDFTranslator(config.model_type, config.model_name)


if __name__ == "__main__":
    # 初始化 translator
    initialize_translator()
    # 启动 Gradio 服务
    launch_gradio()
