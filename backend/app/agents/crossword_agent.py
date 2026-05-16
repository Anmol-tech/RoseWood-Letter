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
