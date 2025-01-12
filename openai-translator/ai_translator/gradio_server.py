from typing import Optional
import gradio as gr
import os
import pdfplumber
import uvicorn
from openai import OpenAI
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from model import OpenAIModel
from utils import ConfigLoader
from translator import PDFTranslator

# FastAPI 应用实例
app = FastAPI()


# 请求体模型
class TranslatorRequest(BaseModel):
    openai_api_key: Optional[str] = None
    model_name: Optional[str] = "gpt-4o-mini"
    openai_api_url: Optional[str] = None
    language: str
    file_format: str
    pages: Optional[int] = None
    output_file_name: str


def translator(openai_api_key, model_name, openai_api_url, language, pdf_file_path, file_format, pages,
               output_file_path, output_file_name):
    if output_file_path and not os.path.exists(output_file_path):  # 验证保存路径
        return "保存路径不存在,请检查路径"
    if not pdf_file_path and os.path.exists(os.path.dirname(pdf_file_path)):  # 验证待翻译文件是否存在
        return "待翻译不存在,请检查路径"
    if file_format not in ["pdf", "markdown"]:  # 验证保存文件格式
        return "文件格式错误,请选择pdf或markdown"
    if not language:  # 验证目标语言是否存在
        return "请选择目标语言"
    if pages and pages < 1:  # 验证页数是否小于1
        return "页数不能小于1"
    with pdfplumber.open(pdf_file_path) as pdf:  # 读取PDF文件，验证页数是否超出范围
        if pages and pages > len(pdf.pages):
            return "页数超出范围,请重新输入"
    config_loader = ConfigLoader("config.yaml")  # 读取配置文件，验证大模型配置是否有效
    config = config_loader.load_config()
    openai_api_key = openai_api_key if openai_api_key else config["OpenAIModel"]["api_key"]  # 获取API Key
    if not openai_api_key and not os.getenv("OPENAI_API_KEY"):  # 验证API Key是否存在
        return "请设置OPENAI_API_KEY"
    api_url = openai_api_url if openai_api_url else config["OpenAIModel"]["api_url"]  # 获取API URL
    if not api_url:
        api_url = os.getenv("OPENAI_BASE_URL")
    try:  # 连接OpenAI API，验证网络链接是否有效
        client = OpenAI(api_key=openai_api_key, base_url=api_url)
    except Exception as e:
        return e
    model_name = model_name if model_name else config["OpenAIModel"]["model"]  # 获取模型名称
    model_list = client.models.list()  # 获取模型列表
    if model_name not in [model.id for model in model_list.data]:  # 验证模型是否存在
        return "模型不存在"

    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    model = OpenAIModel(model_name, openai_api_key, api_url)
    PDF_translator = PDFTranslator(model)
    output_file_path = output_file_path + "\\" + output_file_name + "." + "pdf" if file_format =="pdf" else "md"
    if not pages:
        pages = None
    PDF_translator.translate_pdf(pdf_file_path, file_format, language, output_file_path, pages)

    return f"翻译成功,并保存在{output_file_path}", output_file_path


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
        gr.Number(label="翻译页数", info="请输入页数,默认为全部页数", step=1),
        gr.Textbox(label="输出路径", info="请填写完整路径,如: D:/LLM/"),
        gr.Textbox(label="输出文件名", info="请填写输出文件名,不需加文件扩展名"),
    ],
    outputs=[gr.Textbox(label="result"), gr.File(label="翻译文件", file_types=["pdf", "markdown"])],
)

# gradio图形界面
app = gr.mount_gradio_app(app, demo, path="/translate_pdf/gradio_server")

# FastAPI 路由，处理翻译请求
@app.post("/translate_pdf/api")
async def translate_pdf(
        openai_api_key: Optional[str] = Form(None),
        model_name: Optional[str] = Form("gpt-3.5-turbo"),
        openai_api_url: Optional[str] = Form(None),
        language: str = Form(...),
        file_format: str = Form(...),
        pages: Optional[int] = Form(None),
        output_file_name: str = Form(...),
        pdf_file: UploadFile = File(...)
):
    # 保存上传的PDF文件到临时目录
    temp_pdf_path = f"temp_{pdf_file.filename}"
    with open(temp_pdf_path, "wb") as buffer:
        buffer.write(await pdf_file.read())
    output_file_path = os.getcwd()
    # 调用翻译函数
    result, result_file_path = translator(openai_api_key, model_name, openai_api_url, language, temp_pdf_path, file_format, pages,
                        output_file_path, output_file_name)

    # 删除临时PDF文件
    os.remove(temp_pdf_path)
    # 如果翻译成功，返回翻译后的 PDF 文件
    if file_format == "pdf" and result_file_path and os.path.exists(result_file_path):
        return FileResponse(result_file_path, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename={os.path.basename(result_file_path)}"})

    # 如果翻译成功，返回翻译后的 Markdown 文件
    if file_format == "markdown" and result_file_path and os.path.exists(result_file_path):
        return FileResponse(result_file_path, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={os.path.basename(result_file_path)}"})

    return {"message": result}

# FastAPI 主页
@app.get("/")
def read_root():
    return {"message": "Welcome to the PDF Translation API"}


if __name__ == "__main__":
    # gradio 启动方式
    # demo.launch()

    # uvicorn 启动方式
    uvicorn.run(app, host="127.0.0.1", port=8000)
