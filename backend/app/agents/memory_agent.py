from app.agents.base import BaseAgent
from app.schemas import AgentOutput, PipelineRequest, VisitIntent


class MemoryAgent(BaseAgent):
    name = "Memory Agent"

    def run(
        self,
        request: PipelineRequest,
        intent: VisitIntent | None = None,
        context: dict | None = None,
    ) -> AgentOutput:
        has_early_scan = any("05:" in signal.time for signal in request.ambient_signals)
        has_spa_booking = any(
            "spa" in signal.signal.lower() for signal in request.ambient_signals
        )

        inferred_pattern = "Guest wanted space first, care second."
        adjustment = "Open tomorrow's letter with less ceremony and one quiet weather cue."

        if has_early_scan and not has_spa_booking:
            inferred_pattern = "Guest was awake early and preferred the letter as the primary interface."
            adjustment = "Honor the silence with a shorter opening and no new decisions before noon."
        elif has_spa_booking:
            inferred_pattern = "Guest needed the first hours alone before accepting care."
            adjustment = "Offer care as something already prepared, not something to arrange."

        return AgentOutput(
            agent=self.name,
            title="Ambient stay memory",
            summary=inferred_pattern,
            data={
                "signals": [signal.model_dump() for signal in request.ambient_signals],
                "inferred_pattern": inferred_pattern,
                "next_letter_adjustment": adjustment,
            },
        )
