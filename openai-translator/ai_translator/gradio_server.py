import gradio as gr
import os
import pdfplumber
from openai import OpenAI

from model import OpenAIModel
from utils import ConfigLoader
from translator import PDFTranslator

def translator(openai_api_key, model_name, openai_api_url, language, pdf_file_path, file_format, pages, output_file_path):
    if not os.path.exists(output_file_path): # 验证保存路径
        return "保存路径不存在,请检查路径"
    if not pdf_file_path and os.path.exists(os.path.dirname(pdf_file_path)): # 验证待翻译文件是否存在
        return "待翻译不存在,请检查路径"
    if file_format not in ["pdf", "markdown"]: # 验证保存文件格式
        return "文件格式错误,请选择pdf或markdown"
    if not language: # 验证目标语言是否存在
        return "请选择目标语言"
    with pdfplumber.open(pdf_file_path) as pdf: # 读取PDF文件，验证页数是否超出范围
        if pages is not None and pages > len(pdf.pages):
            return "页数超出范围,请重新输入"
    config_loader = ConfigLoader("config.yaml") # 读取配置文件，验证大模型配置是否有效
    config = config_loader.load_config()
    openai_api_key = openai_api_key if openai_api_key else config["OpenAIModel"]["api_key"] # 获取API Key
    if not openai_api_key and not os.getenv("OPENAI_API_KEY"): # 验证API Key是否存在
        return "请设置OPENAI_API_KEY"
    api_url = openai_api_url if openai_api_url else config["OpenAIModel"]["api_url"] # 获取API URL
    if not api_url:
        api_url = os.getenv("OPENAI_BASE_URL")
    try: # 连接OpenAI API，验证网络链接是否有效
        client = OpenAI(api_key=openai_api_key, base_url=api_url)
    except Exception as e:
        return e
    model_name = model_name if model_name else config["OpenAIModel"]["model"] # 获取模型名称
    model_list = client.models.list() # 获取模型列表
    if model_name not in [model.id for model in model_list.data]: # 验证模型是否存在
        return "模型不存在"
    print(openai_api_key, api_url, model_name)

    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    model = OpenAIModel(model_name, openai_api_key, api_url)
    PDF_translator = PDFTranslator(model)
    PDF_translator.translate_pdf(pdf_file_path, file_format, language, output_file_path, pages)

    return f"翻译成功,并保存在{output_file_path}"

demo = gr.Interface(
    fn=translator,
    inputs=[
        gr.Textbox(label="OPENAI API KEY"),
        gr.Dropdown(
            label="模型名称",
            choices=["gpt-3.5-turbo", "gpt-3.5", "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-o1", "gpt-o1-mini"],
            interactive=True,
            allow_custom_value=True,
        ),
        gr.Textbox(label="OPENAI API 网址", info="请输入API网址,如https://api.openai.com/v1,支持中转key"),
        gr.Textbox(label="目标语言", info="请输入要翻译为何种语言,如Chinese, English, Spanish等"),
        gr.File(label="请选择待翻译文件", file_types=["pdf"], file_count="single"),
        gr.Radio(label="输出文件格式", choices=["pdf", "markdown"]),
        gr.Textbox(label="翻译页数", info="请输入页数,默认为全部页数"),
        gr.Textbox(label="输出路径和文件名", info="请填写完整路径,如: D:/LLM/output.pdf"),
    ],
    outputs=gr.Textbox(label="result")
)


if __name__ == "__main__":
    demo.launch()

