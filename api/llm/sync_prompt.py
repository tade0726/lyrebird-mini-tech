"""
Initialize and Manage prompts with different iterations

"""

import os
from typing import List

from langchain import hub as prompts
from langchain_core.prompts import ChatPromptTemplate
from langsmith.utils import LangSmithConflictError

from api.core.config import settings


PROMPT_PATH = "api/llm/prompts/"


def update_prompt(prompt_name: str, prompt_template: str):

    # init env variables from st.secrets, put them in os.environ
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT

    prompt = ChatPromptTemplate.from_template(prompt_template)

    try:
        url = prompts.push(prompt_name, prompt)
    except LangSmithConflictError:
        return {"url": None, "prompt": prompt_name, "prompt_template": prompt_template}

    return {"url": url, "prompt": prompt_name, "prompt_template": prompt_template}


def main(templates: List[dict]):

    for template in templates:
        update_prompt(template["prompt_name"], template["prompt_template"])

    return templates


def local_prompt_reader(prompt_name: str):
    with open(f"{PROMPT_PATH}/{prompt_name}.md", "r") as f:
        return f.read()


TEMPLATES = [
    {
        "prompt_name": "format-transcript",
        "prompt_template": local_prompt_reader("format-transcript"),
    },
    {
        "prompt_name": "create-memory",
        "prompt_template": local_prompt_reader("create-memory"),
    },
]


if __name__ == "__main__":
    main(TEMPLATES)
