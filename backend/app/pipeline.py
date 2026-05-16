import asyncio
import re
from datetime import datetime
from pathlib import Path

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
    VisitIntent,
    WorldContext,
)


class RosewoodPipeline:
    def __init__(self) -> None:
        self.intent_agent = IntentAgent()
        self.parallel_agents = [
            WorldAgent(),
            RhythmAgent(),
            DiscoveryAgent(),
            MemoryAgent(),
            ResonanceAgent(),
        ]
        self.voice_agent = VoiceAgent()
        self.artifact_agents = [
            CrosswordAgent(),
            CompositorAgent(),
            AudioAgent(),
        ]
        self.agents = [
            *self.parallel_agents,
            VoiceAgent(),
            *self.artifact_agents,
        ]

    def run(self, request: PipelineRequest) -> PipelineResponse:
        return asyncio.run(self.arun(request))

    async def arun(self, request: PipelineRequest) -> PipelineResponse:
        intent_output = await self.intent_agent.arun(request)
        visit_intent = VisitIntent(**intent_output.data)

        outputs: list[AgentOutput] = [intent_output]
        context = {"intent": visit_intent.model_dump()}

        parallel_outputs = await asyncio.gather(
            *[
                agent.arun(request=request, intent=visit_intent, context=context.copy())
                for agent in self.parallel_agents
            ]
        )
        for output in parallel_outputs:
            outputs.append(output)
            context[output.agent] = output.model_dump()

        voice_output_agent = await self.voice_agent.arun(
            request=request,
            intent=visit_intent,
            context=context,
        )
        outputs.append(voice_output_agent)
        context[self.voice_agent.name] = voice_output_agent.model_dump()

        artifact_outputs = await asyncio.gather(
            *[
                agent.arun(request=request, intent=visit_intent, context=context.copy())
                for agent in self.artifact_agents
            ]
        )
        for output in artifact_outputs:
            outputs.append(output)
            context[output.agent] = output.model_dump()

        world_output = context["World Agent"]["data"]
        rhythm_output = context["Rhythm Agent"]["data"]
        discovery_output = context["Discovery Agent"]["data"]
        memory_output = context["Memory Agent"]["data"]
        resonance_output = context["Temporal Resonance Layer"]["data"]
        voice_output = context["Voice Agent"]["data"]
        crossword_output = context["Crossword Agent"]["data"]
        compositor_output = context["Compositor Agent"]["data"]
        audio_output = context["Audio Agent"]["data"]

        letter_paragraphs = self._compose_letter_paragraphs(
            request=request,
            intent=visit_intent,
            world_output=world_output,
            rhythm_output=rhythm_output,
            discovery_output=discovery_output,
            memory_output=memory_output,
            resonance_output=resonance_output,
        )

        letter = LetterArtifact(
            date_line="Morning letter · May 17, 2030",
            salutation=f"Good morning, {request.profile.guest_name}.",
            paragraphs=letter_paragraphs,
            qr_caption="A personal note from Rosewood.",
            html=self._compose_letter_html(
                guest_name=request.profile.guest_name,
                paragraphs=letter_paragraphs,
            ),
            pdf_status="html_ready",
        )
        saved_paths = self._save_letter(request=request, intent=visit_intent, letter=letter)
        letter.markdown_path = saved_paths["markdown_path"]
        letter.html_path = saved_paths["html_path"]

        audio = AudioArtifact(
            script=self._clean_prose(audio_output.get("script", "")),
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

    def _compose_letter_paragraphs(
        self,
        *,
        request: PipelineRequest,
        intent: VisitIntent,
        world_output: dict,
        rhythm_output: dict,
        discovery_output: dict,
        memory_output: dict,
        resonance_output: dict,
    ) -> list[str]:
        label = intent.label

        if label == "Milestone":
            paragraphs = [
                (
                    f"Good light is waiting. {world_output['weather_frame']}"
                ),
                (
                    "Let the day stay unannounced until evening. "
                    f"{resonance_output['detail']}"
                ),
                (
                    f"{discovery_output['recommendation']} "
                    "It is held quietly, only if the day wants a secret."
                ),
            ]
        elif label == "Celebration Discovery":
            paragraphs = [
                (
                    f"The town is brightening early. {world_output['weather_frame']}"
                ),
                (
                    f"{resonance_output['detail']} "
                    "We liked the precision of that."
                ),
                (
                    f"{discovery_output['recommendation']} "
                    "The door looks ordinary until it opens."
                ),
            ]
        else:
            paragraphs = [
                (
                    "The fog came in while the hotel was quiet. The hills are still half withheld."
                ),
                (
                    "We have left the first hours open. "
                    "Coffee can arrive without conversation."
                ),
                (
                    f"{resonance_output['detail']} "
                    f"{discovery_output['recommendation']} No need to decide now."
                ),
            ]

        return [self._clean_prose(paragraph) for paragraph in paragraphs]

    def _clean_prose(self, text: str) -> str:
        return text.replace("\u2014", ", ").replace("\u2013", "-")

    def _save_letter(
        self,
        *,
        request: PipelineRequest,
        intent: VisitIntent,
        letter: LetterArtifact,
    ) -> dict[str, str]:
        output_dir = Path(__file__).resolve().parents[2] / "generated_letters"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        guest_slug = self._slugify(request.profile.guest_name)
        suite_slug = self._slugify(request.profile.suite)
        stem = f"{timestamp}-suite-{suite_slug}-{guest_slug}"

        markdown_path = output_dir / f"{stem}.md"
        html_path = output_dir / f"{stem}.html"

        markdown_path.write_text(
            self._compose_letter_markdown(intent=intent, letter=letter),
            encoding="utf-8",
        )
        html_path.write_text(letter.html, encoding="utf-8")

        return {
            "markdown_path": str(markdown_path.relative_to(Path(__file__).resolve().parents[2])),
            "html_path": str(html_path.relative_to(Path(__file__).resolve().parents[2])),
        }

    def _compose_letter_markdown(self, *, intent: VisitIntent, letter: LetterArtifact) -> str:
        paragraphs = "\n\n".join(letter.paragraphs)
        return (
            "# ROSEWOOD\n\n"
            f"{letter.date_line}\n\n"
            f"Intent: {intent.label}\n\n"
            f"{letter.salutation}\n\n"
            f"{paragraphs}\n\n"
            f"{letter.qr_caption}\n"
        )

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "guest"

    def _compose_letter_html(self, guest_name: str, paragraphs: list[str]) -> str:
        body = "".join(f"<p>{self._clean_prose(paragraph)}</p>" for paragraph in paragraphs)
        return (
            "<article class=\"rosewood-letter\">"
            "<header><strong>ROSEWOOD</strong><span>Morning letter</span></header>"
            f"<main><p><strong>Good morning, {guest_name}.</strong></p>{body}</main>"
            "<footer>A personal note from Rosewood.</footer>"
            "</article>"
        )


pipeline = RosewoodPipeline()
