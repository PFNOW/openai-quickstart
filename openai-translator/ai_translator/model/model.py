from langchain_experimental.graph_transformers.llm import system_prompt

from book import ContentType

class Model:
    def make_text_prompt(self, text: str, target_language: str) -> str:
        system_prompt = "你是一个翻译家，可以识别文本的语言，并且翻译为其他语言。"
        user_prompt = f"请把以下的一段话翻译为{target_language}：{text}"
        return system_prompt, user_prompt

    def make_table_prompt(self, table: str, target_language: str) -> str:
        # return f"翻译为{target_language}，保持间距（空格，分隔符），以表格形式返回：\n{table}"
        system_prompt = """
# 角色:
你是一个翻译家，可以识别表格文本的语言，并且翻译为其他语言。对于“Pirce (Dollars)”使用括号补充解释的词语，请去掉括号前的空格，然后再翻译。
# 任务:
翻译表格，以空格和换行符表示表格。
# 样例:
## 输入:
fruit color price (USD)  
apple red 1.20  
banana yellow 0.50  
## 输出:
水果 颜色 价格(美元)  
苹果 红色 1.20  
香蕉 黄色 0.50 
"""
        user_prompt = f"请把以下的一个表格翻译为{target_language}，以空格和换行符表示表格：\n{table}"
        return system_prompt, user_prompt

    def translate_prompt(self, content, target_language: str) -> str:
        if content.content_type == ContentType.TEXT:
            return self.make_text_prompt(content.original, target_language)
        elif content.content_type == ContentType.TABLE:
            return self.make_table_prompt(content.get_original_as_str(), target_language)

    def make_request(self, system_prompt, user_prompt):
        raise NotImplementedError("子类必须实现 make_request 方法")
