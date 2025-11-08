"""Scenario architect for creating micro-scenarios."""

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SCENARIO_PROMPT_SIMPLE = """You are creating a minimal scenario setup for a simple Python concept.

COMPLEXITY: SIMPLE
Keep it brief - 1-2 sentences maximum, or skip scenario entirely.

Technical Answer:
{technical_answer}

If a scenario helps, create a very short one. Otherwise, return "SKIP" to proceed without scenario.

Example output:
"Priya needs to display a message to users in her script."

OR

"SKIP"
"""

SCENARIO_PROMPT_STANDARD = """You are creating a focused micro-scenario for a Python learning concept.

AETHELGARD BRAND:
- Micro fixes, macro impact (small changes, big clarity)
- Honest, reflective, clear (no hype, just truth)
- One character, one problem, one solution

COMPLEXITY: STANDARD
Create a focused scenario with:
- ONE character (with a relatable name: Priya, Maya, Alex, Sam, etc.)
- ONE specific problem they hit (a "stuck" moment)
- Setup for the micro-fix discovery

EXAMPLE DOMAINS (generic, beginner-friendly):
- Data analysis (cleaning datasets, exploring data)
- ML/AI projects (training models, handling data)
- Automation scripts (file processing, API calls)
- Web projects (building apps, handling requests)

Keep it under 100 words. Focus on the problem, not the solution (solution comes in the narrative).

Technical Answer:
{technical_answer}

Create the micro-scenario:
"""

SCENARIO_PROMPT_CRITICAL = """You are creating a layered micro-scenario for a complex Python concept.

AETHELGARD BRAND:
- Micro fixes, macro impact (small changes, big clarity)
- Honest, reflective, clear (no hype, just truth)
- One character, one problem, one solution

COMPLEXITY: CRITICAL
Create a scenario with:
- ONE character (with a relatable name: Priya, Maya, Alex, Sam, etc.)
- ONE multi-layered problem (reveals sub-concepts naturally)
- Progressive discovery setup (character will have multiple "aha" moments)

EXAMPLE DOMAINS (generic, beginner-friendly):
- Data analysis (cleaning datasets, exploring data)
- ML/AI projects (training models, handling data)
- Automation scripts (file processing, API calls)
- Web projects (building apps, handling requests)

Keep it under 150 words. Set up the problem complexity without solving it.

Technical Answer:
{technical_answer}

Create the layered micro-scenario:
"""


class ScenarioArchitect:
    """
    Creates micro-scenarios for Python learning content.
    
    Adapts scenario complexity based on topic complexity:
    - Simple: Minimal or no scenario
    - Standard: Focused one-problem scenario
    - Critical: Layered multi-part scenario
    """
    
    def __init__(self) -> None:
        settings = get_settings()
        self.model = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.4,  # Some creativity, but controlled
        )
        self.logger = get_logger(__name__)
    
    async def create_scenario(
        self,
        technical_answer: str,
        complexity: str,
    ) -> str:
        """
        Create a micro-scenario appropriate for the complexity level.
        
        Args:
            technical_answer: The technical content to create scenario for
            complexity: simple | standard | critical
            
        Returns:
            Scenario text, or "SKIP" for simple topics
        """
        try:
            # Select prompt based on complexity
            if complexity == "simple":
                prompt_template = SCENARIO_PROMPT_SIMPLE
            elif complexity == "standard":
                prompt_template = SCENARIO_PROMPT_STANDARD
            else:  # critical
                prompt_template = SCENARIO_PROMPT_CRITICAL
            
            prompt = ChatPromptTemplate.from_template(prompt_template)
            messages = prompt.format_messages(technical_answer=technical_answer)
            
            response = await self.model.ainvoke(messages)
            scenario = response.content.strip()
            
            self.logger.info(
                "scenario.architect.complete",
                complexity=complexity,
                scenario_length=len(scenario),
                skipped=(scenario == "SKIP"),
            )
            
            return scenario
            
        except Exception as e:
            self.logger.error(
                "scenario.architect.error",
                complexity=complexity,
                error=str(e),
                exc_info=True,
            )
            # Return skip on error to allow pipeline to continue
            return "SKIP"



