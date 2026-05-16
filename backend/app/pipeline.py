from app.agents import (
    AudioAgent,
    CompositorAgent,
    CrosswordAgent,
    DiscoveryAgent,
    IntentAgent,
    MemoryAgent,
    ResonanceAgent,
    RhythmAgent,
    VoiceAgent,
    WorldAgent,
)
from app.schemas import (
    AgentOutput,
    AudioArtifact,
    CrosswordArtifact,
    CrosswordClue,
    DiscoveryRecommendation,
    EditorialVoice,
    LetterArtifact,
    MemoryInsight,
    PipelineRequest,
    PipelineResponse,
    PrintArtifact,
    RhythmArc,
    TemporalResonance,
    WorldContext,
)


class RosewoodPipeline:
    def __init__(self) -> None:
        self.intent_agent = IntentAgent()
        self.agents = [
            WorldAgent(),
            RhythmAgent(),
            DiscoveryAgent(),
            MemoryAgent(),
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

        world_output = context["World Agent"]["data"]
        rhythm_output = context["Rhythm Agent"]["data"]
        discovery_output = context["Discovery Agent"]["data"]
        memory_output = context["Memory Agent"]["data"]
        resonance_output = context["Temporal Resonance Layer"]["data"]
        voice_output = context["Voice Agent"]["data"]
        crossword_output = context["Crossword Agent"]["data"]
        compositor_output = context["Compositor Agent"]["data"]
        audio_output = context["Audio Agent"]["data"]

        letter = LetterArtifact(
            date_line="Morning letter · May 17, 2030",
            salutation=f"Good morning, {request.profile.guest_name}.",
            paragraphs=[
                world_output["weather_frame"],
                rhythm_output["morning"],
                resonance_output["detail"],
                discovery_output["recommendation"],
            ],
            qr_caption="A personal note from Rosewood.",
            html=self._compose_letter_html(
                guest_name=request.profile.guest_name,
                paragraphs=[
                    world_output["weather_frame"],
                    rhythm_output["morning"],
                    resonance_output["detail"],
                    discovery_output["recommendation"],
                ],
            ),
            pdf_status="html_ready",
        )

        audio = AudioArtifact(
            script=audio_output.get("script", ""),
            voice=audio_output.get("voice", "soft and slow"),
            audio_url=audio_output.get("audio_url"),
            status=audio_output.get("status", "script_ready"),
        )

        print_artifact = PrintArtifact(
            paper_scent=compositor_output.get("paper_scent", visit_intent.scent_profile),
            qr_url=f"https://rosewood.local/letters/{request.profile.suite}/audio",
            qr_caption=letter.qr_caption,
            print_status="ready_for_composition",
            delivery_window=compositor_output.get("delivery_window", "06:00"),
        )

        return PipelineResponse(
            profile=request.profile,
            visit_intent=visit_intent,
            outputs=outputs,
            world_context=WorldContext(
                weather_frame=world_output["weather_frame"],
                property_detail=world_output["property_detail"],
                chef_note=world_output["chef_note"],
                local_conditions=world_output.get("local_conditions", []),
            ),
            rhythm_arc=RhythmArc(
                morning=rhythm_output["morning"],
                afternoon=rhythm_output["afternoon"],
                evening=rhythm_output["evening"],
                emotional_shape=rhythm_output.get("emotional_shape", "A day with room in it"),
            ),
            discovery=DiscoveryRecommendation(
                title=context["Discovery Agent"]["title"],
                recommendation=discovery_output["recommendation"],
                reason=discovery_output["reason"],
                guest_fit=discovery_output["guest_fit"],
            ),
            memory=MemoryInsight(
                signals=request.ambient_signals,
                inferred_pattern=memory_output["inferred_pattern"],
                next_letter_adjustment=memory_output["next_letter_adjustment"],
            ),
            temporal_resonance=TemporalResonance(
                title=context["Temporal Resonance Layer"]["title"],
                detail=resonance_output["detail"],
                verification_needed=resonance_output["verification_needed"],
                source_targets=resonance_output["source_targets"],
            ),
            editorial_voice=EditorialVoice(
                tone=voice_output["tone"],
                rules=voice_output["rules"],
                forbidden_phrases=voice_output.get("forbidden_phrases", []),
            ),
            crossword=CrosswordArtifact(
                title=context["Crossword Agent"]["title"],
                clues=[
                    CrosswordClue(**clue)
                    for clue in crossword_output.get("clues", [])
                ],
            ),
            letter=letter,
            audio=audio,
            print_artifact=print_artifact,
            audio_script=audio.script,
            print_status=print_artifact.print_status,
        )

    def _compose_letter_html(self, guest_name: str, paragraphs: list[str]) -> str:
        body = "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
        return (
            "<article class=\"rosewood-letter\">"
            "<header><strong>ROSEWOOD</strong><span>Morning letter</span></header>"
            f"<main><p><strong>Good morning, {guest_name}.</strong></p>{body}</main>"
            "<footer>A personal note from Rosewood.</footer>"
            "</article>"
        )


pipeline = RosewoodPipeline()
