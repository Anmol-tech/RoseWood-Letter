export const visitIntent = {
  label: "Quiet Restoration",
  confidence: 91,
  emotionalState: "Overextended, private, seeking relief from decisions",
  engagementStyle: "Gentle offers, no crowded recommendations, low-friction opt-in",
  narrativeFrame: "The day should feel like permission to be unreachable",
  scentProfile: "Cedar, damp earth, morning fog",
};

export const defaultPipelineRequest = {
  profile: {
    guest_name: "Guest",
    suite: "804",
    booking_notes: "quiet weekend",
    arrival_date: "2030-05-16",
    stay_nights: 2,
    occasion: null,
  },
  ambient_signals: [
    {
      time: "05:47",
      signal: "Letter QR scanned early, then no further actions.",
    },
    {
      time: "11:18",
      signal: "Spa booking made after a quiet first morning.",
    },
  ],
};

export const memorySignals = [
  {
    time: "05:47",
    signal: "Letter QR scanned early, then no further actions.",
  },
  {
    time: "11:18",
    signal: "Spa booking made after a quiet first morning.",
  },
  {
    time: "Signal",
    signal: "Guest wanted space first, care second.",
  },
];

export const pipelineStages = [
  {
    name: "Intent",
    agent: "Intent Agent",
    summary: "Infers the guest's reason for being here.",
    statusText: "Intent object formed",
  },
  {
    name: "World",
    agent: "World Agent",
    summary: "Filters weather, events, property data, and off-menu details.",
    statusText: "World details filtered",
  },
  {
    name: "Rhythm",
    agent: "Rhythm Agent",
    summary: "Designs the emotional shape of the guest's day.",
    statusText: "Rhythm arc drafted",
  },
  {
    name: "Discovery",
    agent: "Discovery Agent",
    summary: "Finds one local recommendation with quiet specificity.",
    statusText: "Discovery selected",
  },
  {
    name: "Resonance",
    agent: "Temporal Resonance Layer",
    summary: "Surfaces one true coincidence across date, land, and guest.",
    statusText: "Resonance found",
  },
  {
    name: "Voice",
    agent: "Voice Agent",
    summary: "Rewrites every output in one calibrated editorial tone.",
    statusText: "Voice calibrated",
  },
  {
    name: "Crossword",
    agent: "Crossword Agent",
    summary: "Turns recommendations into a small solvable itinerary.",
    statusText: "Crossword generated",
  },
  {
    name: "Compositor",
    agent: "Compositor Agent",
    summary: "Assembles the print-ready letter for scent and delivery.",
    statusText: "Letter composed",
  },
];

export const letterParagraphs = [
  "The fog came in overnight. It is thicker than yesterday, and quieter. The eastern trail will hold its cool until nearly eleven.",
  "We have left the first part of the day mostly untouched. Coffee can arrive without conversation. The garden path is dry enough for soft shoes.",
  "One small thing worth knowing: the fig orchard beyond the lower lawn was planted in the same year you first came to California. The fruit is just beginning this week.",
  "If the afternoon asks for a destination, Mara Kito opens her ceramics studio at two. She fires with clay from the same ridge you can see from your window.",
];

export const audioScript =
  "There is no need to make much of the morning. We noticed the fog moved in low, and thought you might like the day to begin without ceremony.";
