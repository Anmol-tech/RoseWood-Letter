from app.schemas import AmbientSignal, DemoScenario, GuestPersona, GuestProfile, PipelineRequest


DEMO_SCENARIOS = [
    DemoScenario(
        id="quiet-restoration",
        title="Quiet Restoration",
        description="A solo guest booked late and asked for a quiet weekend with very little friction.",
        request=PipelineRequest(
            profile=GuestProfile(
                guest_name="Avery Stone",
                suite="804",
                booking_notes="quiet weekend, solo arrival, no calls if possible",
                arrival_date="2030-05-16",
                stay_nights=2,
                persona=GuestPersona(
                    segment="Restoration Seeker",
                    traits=["private", "overextended", "decision-light"],
                    preferences={
                        "pace": "unhurried",
                        "service_style": "quiet and opt-in",
                        "tone": "soft, precise, spacious",
                    },
                ),
            ),
            ambient_signals=[
                AmbientSignal(
                    time="05:47",
                    signal="Letter QR scanned early, then no further actions.",
                ),
                AmbientSignal(
                    time="11:18",
                    signal="Spa booking made after a quiet first morning.",
                ),
            ],
        ),
    ),
    DemoScenario(
        id="milestone-couple",
        title="Milestone Couple",
        description="A couple planned months ahead for their first trip together in two years.",
        request=PipelineRequest(
            profile=GuestProfile(
                guest_name="Mara and Julian Chen",
                suite="1203",
                booking_notes="first trip together in two years, private dinner preferred",
                arrival_date="2030-05-16",
                stay_nights=3,
                occasion="milestone",
                persona=GuestPersona(
                    segment="Milestone Couple",
                    traits=["ceremonial", "connected", "meaning-seeking"],
                    preferences={
                        "pace": "gentle build",
                        "service_style": "warm, prepared, quietly celebratory",
                        "tone": "ceremonial without sentimentality",
                    },
                ),
            ),
            ambient_signals=[
                AmbientSignal(
                    time="20:12",
                    signal="Private dining inquiry added before arrival.",
                ),
                AmbientSignal(
                    time="21:04",
                    signal="Guest asked concierge for a quiet place to mark the evening.",
                ),
            ],
        ),
    ),
    DemoScenario(
        id="celebration-discovery",
        title="Celebration / Discovery Guest",
        description="A bright, curious guest came to celebrate and wants the place to open up.",
        request=PipelineRequest(
            profile=GuestProfile(
                guest_name="Leila Hart",
                suite="617",
                booking_notes="birthday weekend, loves food, design, hidden local places",
                arrival_date="2030-05-16",
                stay_nights=2,
                occasion="celebration",
                persona=GuestPersona(
                    segment="Celebration Explorer",
                    traits=["curious", "social", "taste-led"],
                    preferences={
                        "pace": "lively but edited",
                        "service_style": "confident, surprising, locally connected",
                        "tone": "bright, elegant, conspiratorial",
                    },
                ),
            ),
            ambient_signals=[
                AmbientSignal(
                    time="07:32",
                    signal="QR scanned after breakfast and chef note opened.",
                ),
                AmbientSignal(
                    time="09:15",
                    signal="Guest saved the gallery recommendation.",
                ),
            ],
        ),
    ),
]
