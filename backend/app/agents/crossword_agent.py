from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class CrosswordAgent(BaseAgent):
    name = "Crossword Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent=self.name,
            title="Hidden itinerary puzzle",
            summary="A small crossword whose answers reveal the day's recommendations.",
            data={
                "clues": [
                    {"clue": "Clay from the ridge", "answer": "KITO"},
                    {"clue": "Morning cover over the eastern trail", "answer": "FOG"},
                    {"clue": "Quiet breakfast note", "answer": "COFFEE"},
                ]
            },
        )

    async def arun(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        fallback = self.run(request, intent, context)
        data = await self.complete_data(
            system=(
                "You are the Rosewood Letter Crossword Agent. Create a small elegant "
                "crossword clue set where answers hide the day's recommendations. "
                "Prefer short answer words that share letters with each other. "
                "Return only JSON with clues, where clues is a list of clue/answer objects."
            ),
            prompt=f"Intent: {intent.model_dump() if intent else {}}\nContext: {context or {}}",
            fallback=fallback.data,
        )
        return AgentOutput(
            agent=self.name,
            title=fallback.title,
            summary=fallback.summary,
            data=data,
        )
