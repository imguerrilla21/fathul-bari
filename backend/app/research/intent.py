from app.llm.client import get_llm_client
from app.llm.prompts import RESEARCH_INTENT_PROMPT
from app.llm.structured import ResearchQuery

def parse_intent(query: str) -> ResearchQuery:
    """
    Parses a natural language query into a structured ResearchQuery.
    """
    client = get_llm_client()
    return client.generate_structured(
        system_prompt=RESEARCH_INTENT_PROMPT,
        user_prompt=query,
        response_model=ResearchQuery
    )
