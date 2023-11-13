import os
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_type: str = "azure"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = os.getenv("OPENAI_API_VERSION")

def prompt(prompt: str, model: str = os.getenv("OPENAI_CHAT_MODEL")) -> str:
    """
    Generate a response from a prompt using the OpenAI API.
    """

    response = openai.ChatCompletion.create(
        model=model,
        temperature=0,
        deployment_id=os.getenv("OPENAI_CHAT_MODEL"),
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    return response["choices"][0]["message"]["content"]


def  add_cap_ref(
    prompt: str, prompt_suffix: str, cap_ref: str, cap_ref_content: str
) -> str:
    """
    Attaches a capitalized reference to the prompt.
    Example
        prompt = 'Refactor this code.'
        prompt_suffix = 'Make it more readable using this EXAMPLE.'
        cap_ref = 'EXAMPLE'
        cap_ref_content = 'def foo():\n    return True'
        returns 'Refactor this code. Make it more readable using this EXAMPLE.\n\nEXAMPLE\n\ndef foo():\n    return True'
    """

    new_prompt = f"""{prompt} {prompt_suffix}\n\n{cap_ref}\n\n{cap_ref_content}"""

    return new_prompt

