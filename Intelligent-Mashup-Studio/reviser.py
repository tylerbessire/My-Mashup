import os
import json
from openai import OpenAI
from anthropic import Anthropic

class RevisionEngine:
    """
    Handles revising a mashup recipe by leveraging a Large Language Model (LLM)
    to understand natural language commands and rewrite the JSON recipe.
    """

    def __init__(self, current_recipe: dict, user_command: str):
        self.recipe = current_recipe
        self.command = user_command
        openai_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        self.openai_client = OpenAI(api_key=openai_key) if openai_key else None
        self.anthropic_client = Anthropic(api_key=anthropic_key) if anthropic_key else None

        if not self.openai_client and not self.anthropic_client:
            raise EnvironmentError(
                "At least one of OPENAI_API_KEY or ANTHROPIC_API_KEY must be set."
            )

    def _construct_prompt(self):
        system_prompt = """
        You are a music production assistant AI. Your task is to modify a JSON "mashup recipe" based on a user's natural language command.
        Your ONLY output must be the complete, modified JSON recipe. Do not add any conversational text, explanations, or code formatting like ```json.
        Rules:
        1. Analyze the user's command to understand their intent.
        2. Identify the target timeline item(s) to modify.
        3. Modify the JSON structure directly to apply the change.
        4. If changing timing, you must update the "time_ms" fields for the target item and all subsequent items.
        5. Increment the "version" number by 1.
        6. Ensure the final output is a single, valid JSON object.
        """
        user_prompt = f"""
        Current mashup recipe:
        {json.dumps(self.recipe, indent=2)}

        User's command:
        "{self.command}"

        Provide the complete, updated JSON recipe.
        """
        return system_prompt, user_prompt

    def revise(self):
        print(f"Contacting AI Creative Assistant with command: '{self.command}'")
        system_prompt, user_prompt = self._construct_prompt()
        # First attempt using OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                response_content = response.choices[0].message.content
                new_recipe = json.loads(response_content)
                print("Successfully received recipe from OpenAI.")
                return new_recipe
            except Exception as e:
                print(f"OpenAI failed: {e}")

        # Fallback to Anthropic if OpenAI fails or wasn't configured
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-4-opus-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                response_content = response.content[0].text
                new_recipe = json.loads(response_content)
                print("Successfully received recipe from Anthropic.")
                return new_recipe
            except Exception as e:
                print(f"Anthropic failed: {e}")

        print("Both language models failed. Returning original recipe.")
        return self.recipe
