"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_PATH = "prompts/bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt no formato "{username}/bug_to_user_story_v2"
        prompt_data: Dados do prompt (já validados)

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])

        tags = prompt_data.get("techniques_applied", []) + prompt_data.get("tags", [])

        client = Client()
        url = client.push_prompt(
            prompt_name,
            object=prompt_template,
            is_public=True,
            description=prompt_data["description"],
            tags=tags,
        )

        print(f"   ✓ Prompt publicado: {url}")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao publicar prompt no LangSmith: {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Reaproveita utils.validate_prompt_structure para não duplicar as
    regras de validação usadas também pelos testes em tests/test_prompts.py.

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS AO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    prompt_data = load_yaml(PROMPT_PATH)
    if prompt_data is None:
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print(f"❌ Prompt inválido em {PROMPT_PATH}:")
        for error in errors:
            print(f"   - {error}")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/bug_to_user_story_v2"

    print(f"Publicando prompt: {prompt_name}")

    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    print(f"\n✓ Push concluído com sucesso!")
    print(f"  Confira em: https://smith.langchain.com/prompts/{prompt_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
