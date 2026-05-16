import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

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
    CrosswordEntry,
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

logger = logging.getLogger("rosewood.pipeline")


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

    async def arun(
        self,
        request: PipelineRequest,
        progress_callback: Callable[[dict[str, Any]], Awaitable[None] | None] | None = None,
    ) -> PipelineResponse:
        async def emit(event: str, agent: str, progress: int) -> None:
            logger.info(
                "pipeline agent %s: guest=%s suite=%s agent=%s progress=%s",
                event,
                request.profile.guest_name,
                request.profile.suite,
                agent,
                progress,
            )
            if progress_callback is None:
                return

            result = progress_callback(
                {
                    "event": event,
                    "agent": agent,
                    "progress": progress,
                }
            )
            if result is not None:
                await result

        await emit("started", "Intent Agent", 5)
        intent_output = await self.intent_agent.arun(request)
        await emit("completed", "Intent Agent", 12)
        visit_intent = VisitIntent(**intent_output.data)

        outputs: list[AgentOutput] = [intent_output]
        context = {"intent": visit_intent.model_dump()}

        async def run_agent(agent, progress_start: int, progress_end: int) -> AgentOutput:
            await emit("started", agent.name, progress_start)
            output = await agent.arun(request=request, intent=visit_intent, context=context.copy())
            await emit("completed", agent.name, progress_end)
            return output

        parallel_outputs = await asyncio.gather(
            *[
                run_agent(agent, 18, 52)
                for agent in self.parallel_agents
            ]
        )
        for output in parallel_outputs:
            outputs.append(output)
            context[output.agent] = output.model_dump()

        await emit("started", self.voice_agent.name, 60)
        voice_output_agent = await self.voice_agent.arun(
            request=request,
            intent=visit_intent,
            context=context,
        )
        await emit("completed", self.voice_agent.name, 68)
        outputs.append(voice_output_agent)
        context[self.voice_agent.name] = voice_output_agent.model_dump()

        artifact_outputs = await asyncio.gather(
            *[
                run_agent(agent, 74, 88)
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
        await emit("started", "Letter Composer", 92)
        crossword = self._build_crossword(
            title=context["Crossword Agent"]["title"],
            clues=crossword_output.get("clues", []),
        )
        qr_url = self._guest_letter_url(request)

        letter = LetterArtifact(
            date_line="Morning letter · May 17, 2030",
            salutation=f"Good morning, {request.profile.guest_name}.",
            paragraphs=letter_paragraphs,
            qr_caption="A personal note from Rosewood.",
            qr_url=qr_url,
            html=self._compose_letter_html(
                guest_name=request.profile.guest_name,
                paragraphs=letter_paragraphs,
                crossword=crossword,
                qr_url=qr_url,
            ),
            pdf_status="html_ready",
        )
        saved_paths = self._save_letter(
            request=request,
            intent=visit_intent,
            letter=letter,
            crossword=crossword,
        )
        letter.markdown_path = saved_paths["markdown_path"]
        letter.html_path = saved_paths["html_path"]
        await emit("completed", "Letter Composer", 96)

        audio = AudioArtifact(
            script=self._clean_prose(audio_output.get("script", "")),
            voice=audio_output.get("voice", "soft and slow"),
            audio_url=audio_output.get("audio_url"),
            status=audio_output.get("status", "script_ready"),
        )

        print_artifact = PrintArtifact(
            paper_scent=compositor_output.get("paper_scent", visit_intent.scent_profile),
            qr_url=qr_url,
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
            crossword=crossword,
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
        elif label == "Conference Event":
            paragraphs = [
                (
                    f"The day has a public shape. {world_output['weather_frame']}"
                ),
                (
                    "We have kept the useful parts close: breakfast, a quiet margin, and a clean return."
                ),
                (
                    f"After the formal part of the day, {self._lowercase_first(discovery_output['recommendation'])} "
                    f"{discovery_output['reason']}"
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

    def _lowercase_first(self, text: str) -> str:
        text = str(text).strip()
        if not text:
            return text
        return text[0].lower() + text[1:]

    def _guest_letter_url(self, request: PipelineRequest) -> str:
        base_url = (request.frontend_base_url or request.public_base_url or "").rstrip("/")
        artifact_id = request.artifact_id or self._slugify(f"{request.profile.suite}-{request.profile.guest_name}")
        path = f"/letter/{artifact_id}"
        return f"{base_url}{path}" if base_url else path

    def _qr_image_url(self, qr_url: str, *, size: int = 220) -> str:
        encoded_url = quote(qr_url, safe="")
        return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&margin=10&data={encoded_url}"

    def _build_crossword(self, *, title: str, clues: list[dict]) -> CrosswordArtifact:
        normalized_clues = self._normalize_crossword_clues(clues)
        if not normalized_clues:
            normalized_clues = [
                {"clue": "Morning cover over the hills", "answer": "FOG"},
                {"clue": "Quiet breakfast note", "answer": "COFFEE"},
                {"clue": "Ceramicist in the letter", "answer": "KITO"},
            ]

        size = 15
        board: list[list[str | None]] = [[None for _ in range(size)] for _ in range(size)]
        placements: list[dict] = []

        first = normalized_clues[0]
        first_col = max(0, (size - len(first["answer"])) // 2)
        first_row = size // 2
        if self._can_place(board, first["answer"], first_row, first_col, "across", require_crossing=False):
            self._place_word(board, first["answer"], first_row, first_col, "across")
            placements.append({**first, "row": first_row, "col": first_col, "direction": "across"})

        for clue in normalized_clues[1:]:
            placement = self._find_crossword_placement(board, placements, clue["answer"])
            if placement is None:
                continue

            row, col, direction = placement
            self._place_word(board, clue["answer"], row, col, direction)
            placements.append({**clue, "row": row, "col": col, "direction": direction})

        grid, row_offset, col_offset = self._trim_crossword_board(board)
        entries = [
            CrosswordEntry(
                number=index + 1,
                clue=item["clue"],
                answer=item["answer"],
                direction=item["direction"],
                row=item["row"] - row_offset,
                col=item["col"] - col_offset,
            )
            for index, item in enumerate(placements)
        ]

        return CrosswordArtifact(
            title=title,
            clues=[CrosswordClue(clue=entry.clue, answer=entry.answer) for entry in entries],
            grid=grid,
            entries=entries,
        )

    def _normalize_crossword_clues(self, clues: list[dict]) -> list[dict]:
        normalized = []
        seen_answers = set()

        for raw in clues:
            clue = self._clean_prose(str(raw.get("clue", ""))).strip()
            answer = re.sub(r"[^A-Za-z]", "", str(raw.get("answer", ""))).upper()

            if not clue or len(answer) < 2 or len(answer) > 12 or answer in seen_answers:
                continue

            seen_answers.add(answer)
            normalized.append({"clue": clue, "answer": answer})

            if len(normalized) == 5:
                break

        return normalized

    def _find_crossword_placement(
        self,
        board: list[list[str | None]],
        placements: list[dict],
        answer: str,
    ) -> tuple[int, int, str] | None:
        for placed in placements:
            existing = placed["answer"]
            direction = "down" if placed["direction"] == "across" else "across"

            for answer_index, letter in enumerate(answer):
                for existing_index, existing_letter in enumerate(existing):
                    if letter != existing_letter:
                        continue

                    if placed["direction"] == "across":
                        row = placed["row"] - answer_index
                        col = placed["col"] + existing_index
                    else:
                        row = placed["row"] + existing_index
                        col = placed["col"] - answer_index

                    if self._can_place(board, answer, row, col, direction, require_crossing=True):
                        return row, col, direction

        return None

    def _can_place(
        self,
        board: list[list[str | None]],
        answer: str,
        row: int,
        col: int,
        direction: str,
        *,
        require_crossing: bool,
    ) -> bool:
        size = len(board)
        delta_row = 1 if direction == "down" else 0
        delta_col = 1 if direction == "across" else 0
        end_row = row + delta_row * (len(answer) - 1)
        end_col = col + delta_col * (len(answer) - 1)

        if row < 0 or col < 0 or end_row >= size or end_col >= size:
            return False

        before_row = row - delta_row
        before_col = col - delta_col
        after_row = end_row + delta_row
        after_col = end_col + delta_col

        if self._cell_has_letter(board, before_row, before_col):
            return False
        if self._cell_has_letter(board, after_row, after_col):
            return False

        crossing = False
        for index, letter in enumerate(answer):
            current_row = row + delta_row * index
            current_col = col + delta_col * index
            existing = board[current_row][current_col]

            if existing is not None and existing != letter:
                return False

            if existing == letter:
                crossing = True
                continue

        return crossing or not require_crossing

    def _cell_has_letter(self, board: list[list[str | None]], row: int, col: int) -> bool:
        return 0 <= row < len(board) and 0 <= col < len(board[row]) and board[row][col] is not None

    def _place_word(
        self,
        board: list[list[str | None]],
        answer: str,
        row: int,
        col: int,
        direction: str,
    ) -> None:
        for index, letter in enumerate(answer):
            board[row + (index if direction == "down" else 0)][col + (index if direction == "across" else 0)] = letter

    def _trim_crossword_board(
        self,
        board: list[list[str | None]],
    ) -> tuple[list[list[str | None]], int, int]:
        filled = [
            (row_index, col_index)
            for row_index, row in enumerate(board)
            for col_index, cell in enumerate(row)
            if cell is not None
        ]

        if not filled:
            return [], 0, 0

        min_row = max(0, min(row for row, _ in filled) - 1)
        max_row = min(len(board) - 1, max(row for row, _ in filled) + 1)
        min_col = max(0, min(col for _, col in filled) - 1)
        max_col = min(len(board[0]) - 1, max(col for _, col in filled) + 1)

        return (
            [row[min_col:max_col + 1] for row in board[min_row:max_row + 1]],
            min_row,
            min_col,
        )

    def _save_letter(
        self,
        *,
        request: PipelineRequest,
        intent: VisitIntent,
        letter: LetterArtifact,
        crossword: CrosswordArtifact,
    ) -> dict[str, str]:
        output_dir = Path(__file__).resolve().parents[2] / "generated_letters"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        guest_slug = self._slugify(request.profile.guest_name)
        suite_slug = self._slugify(request.profile.suite)
        stem = f"{timestamp}-suite-{suite_slug}-{guest_slug}"

        markdown_path = output_dir / f"{stem}.md"
        html_path = output_dir / f"{stem}.html"

        markdown_path.write_text(
            self._compose_letter_markdown(intent=intent, letter=letter, crossword=crossword),
            encoding="utf-8",
        )
        html_path.write_text(letter.html, encoding="utf-8")

        return {
            "markdown_path": str(markdown_path.relative_to(Path(__file__).resolve().parents[2])),
            "html_path": str(html_path.relative_to(Path(__file__).resolve().parents[2])),
        }

    def _compose_letter_markdown(
        self,
        *,
        intent: VisitIntent,
        letter: LetterArtifact,
        crossword: CrosswordArtifact,
    ) -> str:
        paragraphs = "\n\n".join(letter.paragraphs)
        crossword_markdown = self._compose_crossword_markdown(crossword)
        return (
            "# ROSEWOOD\n\n"
            f"{letter.date_line}\n\n"
            f"Intent: {intent.label}\n\n"
            f"{letter.salutation}\n\n"
            f"{paragraphs}\n\n"
            f"{crossword_markdown}\n\n"
            f"{letter.qr_caption}: {letter.qr_url}\n"
        )

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "guest"

    def _compose_crossword_markdown(self, crossword: CrosswordArtifact) -> str:
        if not crossword.entries or not crossword.grid:
            return ""

        grid_lines = [
            " ".join("[]" if cell is not None else "  " for cell in row)
            for row in crossword.grid
        ]
        clue_lines = [
            f"{entry.number}. {entry.direction.title()}: {entry.clue}"
            for entry in crossword.entries
        ]

        return (
            "## Morning Crossword\n\n"
            "```text\n"
            f"{chr(10).join(grid_lines)}\n"
            "```\n\n"
            f"{chr(10).join(clue_lines)}"
        )

    def _compose_crossword_html(self, crossword: CrosswordArtifact) -> str:
        if not crossword.entries or not crossword.grid:
            return ""

        numbered_starts = {
            (entry.row, entry.col): entry.number
            for entry in crossword.entries
        }
        rows = []
        for row_index, row in enumerate(crossword.grid):
            cells = []
            for col_index, cell in enumerate(row):
                if cell is None:
                    cells.append("<td class=\"empty\"></td>")
                    continue

                number = numbered_starts.get((row_index, col_index))
                number_html = f"<small>{number}</small>" if number is not None else ""
                cells.append(f"<td data-letter=\"{escape(cell)}\">{number_html}<span></span></td>")
            rows.append(f"<tr>{''.join(cells)}</tr>")

        clues = "".join(
            "<li>"
            f"<strong>{entry.number} {escape(entry.direction)}</strong>"
            f"<span>{escape(entry.clue)}</span>"
            "</li>"
            for entry in crossword.entries
        )

        return (
            "<section class=\"letter-crossword\">"
            "<h2>Morning Crossword</h2>"
            f"<table>{''.join(rows)}</table>"
            f"<ol>{clues}</ol>"
            "</section>"
        )

    def _compose_letter_html(
        self,
        guest_name: str,
        paragraphs: list[str],
        crossword: CrosswordArtifact,
        qr_url: str,
    ) -> str:
        body = "".join(f"<p>{escape(self._clean_prose(paragraph))}</p>" for paragraph in paragraphs)
        crossword_html = self._compose_crossword_html(crossword)
        qr_image_url = self._qr_image_url(qr_url)
        return (
            "<article class=\"rosewood-letter\">"
            "<header><strong>ROSEWOOD</strong><span>Morning letter</span></header>"
            f"<main><p><strong>Good morning, {escape(guest_name)}.</strong></p>{body}{crossword_html}</main>"
            "<footer>"
            f"<a href=\"{escape(qr_url)}\">"
            f"<img alt=\"QR code for the personal Rosewood note\" src=\"{escape(qr_image_url)}\" width=\"96\" height=\"96\" />"
            "</a>"
            "<span>A personal note from Rosewood.</span>"
            "</footer>"
            "</article>"
        )


pipeline = RosewoodPipeline()
