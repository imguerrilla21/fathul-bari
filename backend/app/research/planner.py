from app.llm.client import get_llm_client
from app.llm.prompts import RESEARCH_PLAN_PROMPT
from app.llm.structured import ResearchQuery, ResearchPlan
import json

def generate_plan(query: ResearchQuery) -> ResearchPlan:
    """
    Generates a sequence of execution steps based on the parsed intent.
    """
    client = get_llm_client()
    query_json = query.model_dump_json()
    return client.generate_structured(
        system_prompt=RESEARCH_PLAN_PROMPT,
        user_prompt=f"Generate a research plan for this query:\n{query_json}",
        response_model=ResearchPlan
    )
