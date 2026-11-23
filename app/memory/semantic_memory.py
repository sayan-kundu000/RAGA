"""Long-Term Semantic Memory implementation based on Mem0 / Zep patterns.

Extracts facts, preferred coding languages, and style choices from interactions,
and dynamically adapts the agent's persona across multi-session dialogues.
"""

import re
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """Represents an extracted semantic memory fact."""
    fact: str
    category: str = "general"


class SemanticMemoryStore:
    """Persistent storage for extracted user semantic memories."""

    def __init__(self) -> None:
        # In-memory dictionary mapped by user_id -> List of facts
        self._user_memories: Dict[str, List[str]] = {}

    def add_memory(self, user_id: str, fact: str) -> bool:
        """Add a new semantic fact for a user if not already present."""
        if not user_id or not fact:
            return False
        cleaned_fact = fact.strip()
        if not cleaned_fact:
            return False

        if user_id not in self._user_memories:
            self._user_memories[user_id] = []

        # Avoid redundant duplicate facts
        if cleaned_fact not in self._user_memories[user_id]:
            self._user_memories[user_id].append(cleaned_fact)
            return True
        return False

    def get_memories(self, user_id: str) -> List[str]:
        """Retrieve all semantic facts recorded for a given user."""
        return list(self._user_memories.get(user_id, []))

    def clear(self, user_id: Optional[str] = None) -> None:
        """Clear memories for a single user or all users."""
        if user_id:
            self._user_memories.pop(user_id, None)
        else:
            self._user_memories.clear()


class FactExtractor:
    """Extracts user preferences, preferred programming languages, and response styles."""

    LANGUAGE_PATTERNS = [
        (r"\b(?:i work in|i code in|i write|i prefer|i use)\s+(python|typescript|javascript|rust|golang|go|c\+\+|java)\b", "language"),
        (r"\b(python|typescript|rust|golang|c\+\+|java)\s+developer\b", "language"),
    ]

    STYLE_PATTERNS = [
        (r"\bprefer\s+(brief|concise|code-only|code only|short|detailed|verbose)\s+responses?\b", "style"),
        (r"\b(code-only|code only|only code|brief|concise)\b", "style"),
        (r"\bno\s+explanations?\b", "style"),
    ]

    def extract_facts(self, text: str) -> List[str]:
        """Inspect input text and extract declarative preferences and facts."""
        facts: List[str] = []
        lower_text = text.lower()

        # Check programming language preferences
        for pattern, cat in self.LANGUAGE_PATTERNS:
            match = re.search(pattern, lower_text)
            if match:
                lang = match.group(1).capitalize()
                if lang.lower() == "go":
                    lang = "Go"
                fact = f"User works in {lang} and prefers {lang} code examples."
                if fact not in facts:
                    facts.append(fact)

        # Check response style preferences
        if "code-only" in lower_text or "code only" in lower_text or "brief, code-only" in lower_text:
            fact = "User prefers brief, code-only responses without long conversational explanations."
            if fact not in facts:
                facts.append(fact)
        elif "brief" in lower_text or "concise" in lower_text:
            fact = "User prefers brief, concise responses."
            if fact not in facts:
                facts.append(fact)

        # Fallback / General declarative fact heuristics (e.g. "I am an engineer at Acme")
        role_match = re.search(r"\bi am (?:a|an)\s+([\w\s]+?)(?:\.|$|,)", lower_text)
        if role_match:
            role = role_match.group(1).strip()
            if len(role) < 40 and not any(k in role for k in ["working", "saying", "asking"]):
                fact = f"User is {role}."
                if fact not in facts:
                    facts.append(fact)

        return facts


class PersonaAdapter:
    """Injects user semantic memories into the LLM system prompt to customize responses."""

    BASE_SYSTEM_PROMPT = (
        "You are RAGA, an Advanced Retrieval-Augmented Generation Agent. "
        "Your task is to provide accurate, grounded answers based strictly on retrieved context "
        "while tailoring your style to the user's historical preferences."
    )

    def build_system_prompt(self, user_memories: List[str]) -> str:
        """Construct the customized system prompt incorporating user profile facts."""
        if not user_memories:
            return self.BASE_SYSTEM_PROMPT

        memory_bullets = "\n".join(f"- {fact}" for fact in user_memories)

        adapter_block = (
            f"\n\n### USER PERSONALIZATION PROFILE (Semantic Memory):\n"
            f"{memory_bullets}\n\n"
            f"INSTRUCTION: You MUST adapt your response structure to respect the user's profile. "
            f"If the user prefers code-only or brief answers, omit conversational filler, greetings, "
            f"and explanations, and output ONLY the requested code block."
        )

        return self.BASE_SYSTEM_PROMPT + adapter_block

