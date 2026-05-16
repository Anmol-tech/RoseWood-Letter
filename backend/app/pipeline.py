from app.agents import (
    AudioAgent,
    CompositorAgent,
    CrosswordAgent,
    DiscoveryAgent,
    IntentAgent,
    ResonanceAgent,
    RhythmAgent,
    VoiceAgent,
    WorldAgent,
)
from app.schemas import AgentOutput, LetterArtifact, PipelineRequest, PipelineResponse


class RosewoodPipeline:
    def __init__(self) -> None:
        self.intent_agent = IntentAgent()
        self.agents = [
            WorldAgent(),
            RhythmAgent(),
            DiscoveryAgent(),
            ResonanceAgent(),
            VoiceAgent(),
            CrosswordAgent(),
            CompositorAgent(),
            AudioAgent(),
        ]

    def run(self, request: PipelineRequest) -> PipelineResponse:
        intent_output = self.intent_agent.run(request)
        visit_intent = self.intent_agent.infer(request)

        outputs: list[AgentOutput] = [intent_output]
        context = {"intent": visit_intent.model_dump()}

        for agent in self.agents:
            output = agent.run(request=request, intent=visit_intent, context=context)
            outputs.append(output)
            context[agent.name] = output.model_dump()

        audio_script = outputs[-1].data.get("script", "")

        return PipelineResponse(
            visit_intent=visit_intent,
            outputs=outputs,
            letter=LetterArtifact(
                date_line="Morning letter · May 17, 2030",
                salutation="Good morning,",
                paragraphs=[
                    "The fog came in overnight. It is thicker than yesterday, and quieter.",
                    "We have left the first part of the day mostly untouched.",
                    "The fig orchard beyond the lower lawn is just beginning this week.",
                    "If the afternoon asks for a destination, Mara Kito opens her ceramics studio at two.",
                ],
                qr_caption="A personal note from Rosewood.",
            ),
            audio_script=audio_script,
            print_status="ready_for_composition",
        )


pipeline = RosewoodPipeline()
