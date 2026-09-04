from getpass import getpass
from openai import OpenAI

BASE_URL = "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1"
MODEL_NAME = "z-ai/glm-5.2-hackathon"

# Enter the API key securely at runtime.
# It is intentionally NOT stored in this source file.
API_KEY = getpass("GreenNode API Key: ")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {
            "role": "system",
            "content": "You are a Server Operations Assistant."
        },
        {
            "role": "user",
            "content": "Xin chào. Hãy trả lời bằng tiếng Việt: Kết nối GreenNode thành công."
        }
    ],
    temperature=0.2,
)

print("\nGreenNode response:")
print(response.choices[0].message.content)
