from datetime import datetime

from pydantic import BaseModel, Field


class GuestPersona(BaseModel):
    segment: str = "Restoration Seeker"
    traits: list[str] = Field(
        default_factory=lambda: ["private", "low-friction", "quiet luxury"]
    )
    preferences: dict[str, str] = Field(
        default_factory=lambda: {
            "pace": "unhurried",
            "service_style": "present when needed, invisible otherwise",
            "tone": "quiet and precise",
        }
    )


class GuestProfile(BaseModel):
    id: int | None = None
    guest_name: str = "Guest"
    suite: str = "804"
    booking_notes: str = "quiet weekend"
    arrival_date: str = "2030-05-16"
    stay_nights: int = 2
    occasion: str | None = None
    persona: GuestPersona = Field(default_factory=GuestPersona)


class GuestProfileCreate(BaseModel):
    guest_name: str = "Guest"
    suite: str = "804"
    booking_notes: str = "quiet weekend"
    arrival_date: str = "2030-05-16"
    stay_nights: int = 2
    occasion: str | None = None
    persona: GuestPersona = Field(default_factory=GuestPersona)


class GuestProfileRecord(GuestProfile):
    created_at: datetime
    updated_at: datetime


class AmbientSignal(BaseModel):
    time: str
    signal: str


class PipelineRequest(BaseModel):
    profile_id: int | None = None
    profile: GuestProfile = Field(default_factory=GuestProfile)
    ambient_signals: list[AmbientSignal] = Field(default_factory=list)


class DemoScenario(BaseModel):
    id: str
    title: str
    description: str
    request: PipelineRequest


class VisitIntent(BaseModel):
    label: str
    confidence: int
    emotional_state: str
    engagement_style: str
    narrative_frame: str
    scent_profile: str


class AgentOutput(BaseModel):
    agent: str
    title: str
    summary: str
    data: dict = Field(default_factory=dict)


class WorldContext(BaseModel):
    weather_frame: str
    property_detail: str
    chef_note: str
    local_conditions: list[str] = Field(default_factory=list)


class RhythmArc(BaseModel):
    morning: str
    afternoon: str
    evening: str
    emotional_shape: str


class DiscoveryRecommendation(BaseModel):
    title: str
    recommendation: str
    reason: str
    guest_fit: str


class MemoryInsight(BaseModel):
    signals: list[AmbientSignal] = Field(default_factory=list)
    inferred_pattern: str
    next_letter_adjustment: str


class TemporalResonance(BaseModel):
    title: str
    detail: str
    verification_needed: bool
    source_targets: list[str] = Field(default_factory=list)


class EditorialVoice(BaseModel):
    tone: str
    rules: list[str] = Field(default_factory=list)
    forbidden_phrases: list[str] = Field(default_factory=list)


class CrosswordClue(BaseModel):
    clue: str
    answer: str


class CrosswordArtifact(BaseModel):
    title: str
    clues: list[CrosswordClue] = Field(default_factory=list)


class LetterArtifact(BaseModel):
    date_line: str
    salutation: str
    paragraphs: list[str]
    qr_caption: str
    html: str = ""
    pdf_status: str = "pending"
    markdown_path: str | None = None
    html_path: str | None = None


class AudioArtifact(BaseModel):
    script: str
    voice: str
    provider: str = "elevenlabs"
    audio_url: str | None = None
    status: str = "script_ready"


class PrintArtifact(BaseModel):
    delivery_window: str = "06:00"
    paper_scent: str
    qr_url: str
    qr_caption: str
    print_status: str


class PipelineResponse(BaseModel):
    profile: GuestProfile
    visit_intent: VisitIntent
    outputs: list[AgentOutput]
    world_context: WorldContext
    rhythm_arc: RhythmArc
    discovery: DiscoveryRecommendation
    memory: MemoryInsight
    temporal_resonance: TemporalResonance
    editorial_voice: EditorialVoice
    crossword: CrosswordArtifact
    letter: LetterArtifact
    audio: AudioArtifact
    print_artifact: PrintArtifact
    audio_script: str
    print_status: str
