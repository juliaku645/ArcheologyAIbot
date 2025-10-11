
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOpenAI  # <-- Исправленный импорт
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_core.runnables import chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
#from langchain.llms import OpenAI
from langchain_community.llms import OpenAI

# 1. Загрузка API ключа
load_dotenv()
openai_api_key = ""
if not openai_api_key:
  raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in environment variables or .env file.")

# 2. Инициализация языковой модели OpenAI
llm = OpenAI(openai_api_key=openai_api_key)
#aaaa = "В чем смысл жизни?"
# 3. Формирование запроса (prompt)
prompt = "В чем смысл жизни?"

# 4. Отправка запроса и получение ответа
response = llm(prompt)

# 5. Вывод ответа
print(response)