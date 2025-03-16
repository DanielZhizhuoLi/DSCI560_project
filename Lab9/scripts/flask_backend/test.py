from langchain_huggingface import HuggingFaceEndpoint
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUGGINGFACE_API_TOKEN")
print("Token:", token)

# 尝试两种方式传递 token，方式一：
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingface_api_token=token,
    temperature=0.1,
    model_kwargs={"max_length": 1024}
)
try:
    result = llm("Hello, world!")
    print("结果方式一：", result)
except Exception as e:
    print("方式一错误：", e)

# 方式二，将 token 放入 model_kwargs 中，键名用 api_key：
llm2 = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0.1,
    model_kwargs={
        "api_key": token,
        "max_length": 1024
    }
)
try:
    result2 = llm2("Hello, world!")
    print("结果方式二：", result2)
except Exception as e:
    print("方式二错误：", e)
