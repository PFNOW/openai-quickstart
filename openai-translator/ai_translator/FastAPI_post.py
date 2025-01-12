import requests

url = "http://127.0.0.1:8000/translate_pdf/api"

# 填写表单数据
data = {
    "openai_api_key": "sk-mNtv08y1KsyuWH6VBZjPl1gg0zgUwy6TMakoW99sJ3JbQzIv",
    "model_name": "gpt-4o-mini",
    "openai_api_url": "https://chatapi.littlewheat.com/v1",
    "language": "Chinese",
    "file_format": "pdf",
    "pages": 2,
    "output_file_name": "test_output",
}

# 上传文件
files = {
    "pdf_file": open("D:\\LLM\\openai-quickstart\\openai-translator\\ai_translator\\tests\\test.pdf", "rb"),
}

response = requests.post(url, data=data, files=files, stream=True)
# 检查响应状态
if response.status_code == 200:
    # 将返回的 PDF 文件保存到本地
    filename = "downloaded_" + response.headers.get("Content-Disposition").split("filename=")[-1].strip(' "') # 保存的本地文件名
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"翻译后的文件已保存为 {filename}")
else:
    # 输出错误信息
    print(f"请求失败，状态码：{response.status_code}")
    print("错误信息：", response.text)