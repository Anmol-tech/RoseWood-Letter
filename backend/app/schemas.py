from pydantic import BaseModel, Field


class GuestProfile(BaseModel):
    guest_name: str = "Guest"
    suite: str = "804"
    booking_notes: str = "quiet weekend"
    arrival_date: str = "2030-05-16"
    stay_nights: int = 2
    occasion: str | None = None


class AmbientSignal(BaseModel):
    time: str
    signal: str


class PipelineRequest(BaseModel):
    profile: GuestProfile = Field(default_factory=GuestProfile)
    ambient_signals: list[AmbientSignal] = Field(default_factory=list)


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


class LetterArtifact(BaseModel):
    date_line: str
    salutation: str
    paragraphs: list[str]
    qr_caption: str


class PipelineResponse(BaseModel):
    visit_intent: VisitIntent
    outputs: list[AgentOutput]
    letter: LetterArtifact
    audio_script: str
    print_status: str
