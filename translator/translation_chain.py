import os

from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

from utils import LOG
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

class TranslationChain:
    def __init__(self, model_name: str = "gpt-3.5-turbo", verbose: bool = True):
        
        # 翻译任务指令始终由 System 角色承担
        template = (
            """You are a translation expert, proficient in various languages. You only need to provide the translation.\n
            Translates {source_language} to {target_language}.\n
            The style of translation is {style}.\n"""
        )
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)

        # 待翻译文本由 Human 角色输入
        human_template = "{text}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        # 使用 System 和 Human 角色的提示模板构造 ChatPromptTemplate
        chat_prompt_template = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )
        # 为了翻译结果的稳定性，将 temperature 设置为 0
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        chat = ChatOpenAI(model_name=model_name, api_key=api_key, base_url=base_url, temperature=0, verbose=verbose)

        self.chain =  chat_prompt_template| chat

    def run(self, text, source_language: str, target_language: str, style: str) -> (str, bool):
        result = ""
        print(f"original text: {text}")
        try:
            result = self.chain.invoke(input={
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
                "style": style
            })
            translation = result.content
            print(f"Translation result: {translation}")
        except Exception as e:
            LOG.error(f"An error occurred during translation: {e}")
            return translation, False

        return translation, True