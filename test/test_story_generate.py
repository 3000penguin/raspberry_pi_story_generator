from google import genai
from pydantic import BaseModel
from config import GEMINI_TEXT_MODEL
from config import GOOGLE_GENAI_API_KEY


class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]


class Recipe_Response:
    def __init__(self, api_key: str = GOOGLE_GENAI_API_KEY):
        if not api_key:
            raise ValueError("API key cannot be empty. Please configure GOOGLE_GENAI_API_KEY in config.py.")
        self.client = genai.Client(api_key=api_key)
        print("Recipe_Response initialized using genai.Client().")

    def test_story_generate(self,prompt_text: str):
        # noinspection PyTypeChecker
        response = self.client.models.generate_content(
            model=GEMINI_TEXT_MODEL,
            contents=prompt_text,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[Recipe],
            },
        )

        if not response.candidates or response.candidates[0].finish_reason.name != 'STOP':
            reason = response.candidates[0].finish_reason.name if response.candidates else "Unknown"
            print(f"Gemini API 文本生成未正常完成。终止原因: {reason}。")
            return None
        if hasattr(response, 'text') and response.text:
            return response
        else:
            print("Gemini API 返回了空文本，但未报告具体错误原因。")
            return None


def main():
    prompt_text = "列出一些流行的饼干食谱，并包括所需的原料和数量。用中文回答。"
    print("--- 测试食谱生成 ---")
    response = Recipe_Response().test_story_generate(prompt_text)
    # Use the response as a JSON string.
    print(response.text)

    # Use instantiated objects.
    my_recipes: list[Recipe] = response.parsed

    print("\n--- 解析后的食谱对象 ---")
    for recipe in my_recipes:
        print(f"食谱名称: {recipe.recipe_name}")
        print(f"所需原料: {recipe.ingredients}")
        print("-" * 20)  # 打印一个分隔线

main()