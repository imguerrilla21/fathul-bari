from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel
from .structured import ResearchQuery, ResearchPlan, ResearchAnswerPayload
import json
import re

T = TypeVar('T', bound=BaseModel)

class BaseLLMClient:
    def generate_structured(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        raise NotImplementedError
        
class MockLLMClient(BaseLLMClient):
    """
    A mock LLM client that returns hardcoded responses for testing purposes,
    allowing the research engine to be run without requiring real API keys.
    """
    def generate_structured(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        
        # Mocking Intent parsing
        if response_model == ResearchQuery:
            return ResearchQuery(
                original_query=user_prompt,
                language="id",
                intent="SHARH_LOOKUP",
                entities=[{"type": "SCHOLAR", "value": "Ibn Hajar"}],
                concepts=["niat"],
                arabic_terms=["النية", "النيات"],
                source_constraints=["Fathul Bari"]
            )
            
        # Mocking Planning
        elif response_model == ResearchPlan:
            return ResearchPlan(
                steps=["IDENTIFY_HADITH", "SEARCH_ARABIC_TERMS", "RETRIEVE_FATHUL_BARI", "BUILD_EVIDENCE", "GENERATE_ANSWER"]
            )
            
        # Mocking Answer Generation
        elif response_model == ResearchAnswerPayload:
            # Extract evidence IDs from system_prompt
            ev_ids = re.findall(r'\[(ev_mock_[a-zA-Z0-9_-]+)\]', system_prompt)
            ev1 = ev_ids[0] if len(ev_ids) > 0 else "ev_mock_1"
            ev2 = ev_ids[1] if len(ev_ids) > 1 else "ev_mock_2"
            
            return ResearchAnswerPayload(
                title="Penjelasan Hadis Niat",
                summary="Ibn Hajar menjelaskan bahwa niat adalah syarat mutlak dalam sahnya suatu amalan menurut mayoritas ulama.",
                sections=[
                    {
                        "title": "Ringkasan",
                        "content": f"Hadis ini merupakan salah satu pilar Islam. Ibn Hajar mengutip para ulama yang mengatakan hadis ini mencakup sepertiga ilmu [{ev1}].",
                        "claims": [{"claim": "Hadis niat mencakup sepertiga ilmu", "evidence_ids": [ev1]}]
                    },
                    {
                        "title": "Penjelasan Ibn Hajar",
                        "content": f"Kata 'النيات' adalah bentuk jamak dari 'نية'. Ibn Hajar merinci perdebatan ulama terkait apakah niat adalah rukun atau syarat [{ev2}].",
                        "claims": [{"claim": "Perdebatan ulama tentang rukun atau syarat", "evidence_ids": [ev2]}]
                    }
                ],
                uncertainties=[]
            )
            
        # Fallback
        raise ValueError(f"Mock not implemented for {response_model}")

def get_llm_client() -> BaseLLMClient:
    return MockLLMClient()
