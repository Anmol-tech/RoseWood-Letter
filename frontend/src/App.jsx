import { useMemo, useState } from "react";
import {
  Activity,
  Headphones,
  Leaf,
  Moon,
  Play,
  Printer,
  Sparkles,
} from "lucide-react";
import {
  audioScript,
  defaultPipelineRequest,
  letterParagraphs,
  memorySignals,
  pipelineStages,
  visitIntent,
} from "./data/rosewoodPipeline.js";
import { runRosewoodPipeline } from "./services/api.js";

function mapIntent(intent) {
  if (!intent) return visitIntent;

  return {
    label: intent.label,
    confidence: intent.confidence,
    emotionalState: intent.emotional_state,
    engagementStyle: intent.engagement_style,
    narrativeFrame: intent.narrative_frame,
    scentProfile: intent.scent_profile,
  };
}

function mapStages(outputs) {
  if (!outputs?.length) return pipelineStages;

  return outputs.map((output) => ({
    name: output.agent.replace(" Agent", "").replace("Temporal Resonance Layer", "Resonance"),
    agent: output.agent,
    summary: output.summary,
    statusText: `${output.title} complete`,
  }));
}

function mapMemorySignals(signals) {
  if (!signals?.length) return memorySignals;

  return [
    ...signals,
    {
      time: "Signal",
      signal: "Guest wanted space first, care second.",
    },
  ];
}

function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Rosewood Letter workspace">
      <div className="brand-lockup">
        <span className="brand-mark">R</span>
        <div>
          <p className="eyebrow">Rosewood 2030</p>
          <h1>The Letter</h1>
        </div>
      </div>

      <nav className="nav-stack" aria-label="Primary">
        <a className="nav-item active" href="#pipeline">
          <Activity size={17} />
          Pipeline
        </a>
        <a className="nav-item" href="#intent">
          <Sparkles size={17} />
          Intent
        </a>
        <a className="nav-item" href="#letter">
          <Printer size={17} />
          Morning Letter
        </a>
        <a className="nav-item" href="#audio">
          <Headphones size={17} />
          Audio Note
        </a>
      </nav>

      <div className="night-run">
        <p className="eyebrow">Next overnight run</p>
        <strong>03:00</strong>
        <span>Print handoff by 05:42</span>
      </div>
    </aside>
  );
}

function Topbar() {
  return (
    <section className="topbar" aria-label="Current guest context">
      <div>
        <p className="eyebrow">Guest stay</p>
        <h2>Suite 804 · Arrival tonight</h2>
      </div>
      <div className="status-pill">
        <span className="pulse" />
        Pipeline ready
      </div>
    </section>
  );
}

function HeroBand() {
  return (
    <section className="hero-band">
      <div className="hero-copy">
        <p className="eyebrow">Invisible AI dashboard</p>
        <h2>A silent overnight system that leaves one physical trace.</h2>
        <p>
          Agents infer why the guest is here, shape the emotional rhythm of the day,
          discover one precise local secret, and compose a scented print artifact before
          breakfast.
        </p>
      </div>
      <div className="artifact-signal" aria-label="Letter artifact signal">
        <span>cedar</span>
        <span>fog</span>
        <span>linen</span>
      </div>
    </section>
  );
}

function IntentPanel({ intent }) {
  const rows = [
    ["Emotional state", intent.emotionalState],
    ["Engagement style", intent.engagementStyle],
    ["Narrative frame", intent.narrativeFrame],
    ["Scent profile", intent.scentProfile],
  ];

  return (
    <article className="panel intent-panel" id="intent">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Visit Intent Object</p>
          <h3>{intent.label}</h3>
        </div>
        <span className="confidence">{intent.confidence}%</span>
      </div>
      <dl className="intent-list">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

function MemoryPanel({ signals }) {
  return (
    <article className="panel memory-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Ambient memory</p>
          <h3>Learns without asking</h3>
        </div>
        <span className="soft-tag">Day 2 seed</span>
      </div>
      <div className="memory-stream">
        {signals.map((item) => (
          <p key={`${item.time}-${item.signal}`}>
            <strong>{item.time}</strong> {item.signal}
          </p>
        ))}
      </div>
    </article>
  );
}

function PipelinePanel({ stages, onRun, runState }) {
  const [activeStage, setActiveStage] = useState(1);
  const isRunning = runState === "running";

  const buttonText = useMemo(() => {
    if (runState === "error") return "Retry pipeline";
    if (!isRunning) return "Run simulation";
    return stages[activeStage]?.statusText ?? "Pipeline complete";
  }, [activeStage, isRunning, runState, stages]);

  async function runPipeline() {
    setActiveStage(0);

    stages.forEach((_, index) => {
      window.setTimeout(() => {
        setActiveStage(index);
      }, index * 650);
    });

    await onRun();
    setActiveStage(stages.length);
  }

  return (
    <section className="panel pipeline-panel" id="pipeline">
      <div className="panel-header">
        <div>
          <p className="eyebrow">3AM orchestration</p>
          <h3>Agent pipeline</h3>
        </div>
        <button className="primary-action" type="button" onClick={runPipeline} disabled={isRunning}>
          <Moon size={17} />
          {buttonText}
        </button>
      </div>

      <div className="pipeline" aria-label="Agent pipeline stages">
        {stages.map((stage, index) => {
          const complete = activeStage > index;
          const active = activeStage === index;

          return (
            <div
              className={`agent-node${complete ? " complete" : ""}${active ? " active" : ""}`}
              data-agent={stage.agent}
              key={stage.agent}
            >
              <span className="node-index">{String(index + 1).padStart(2, "0")}</span>
              <h4>{stage.name}</h4>
              <p>{stage.summary}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function LetterPreview({ letter }) {
  const paragraphs = letter?.paragraphs ?? letterParagraphs;

  return (
    <article className="letter-preview" id="letter" aria-label="Printed letter preview">
      <header className="letter-head">
        <span>ROSEWOOD</span>
        <p>{letter?.date_line ?? "Morning letter · May 17, 2030"}</p>
      </header>
      <div className="letter-body">
        <p className="salutation">{letter?.salutation ?? "Good morning,"}</p>
        {paragraphs.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}
      </div>
      <footer className="letter-foot">
        <div className="qr-mark" aria-label="QR code placeholder" />
        <span>{letter?.qr_caption ?? "A personal note from Rosewood."}</span>
      </footer>
    </article>
  );
}

function AudioPanel({ script }) {
  return (
    <article className="panel" id="audio">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Audio Agent</p>
          <h3>60 second note</h3>
        </div>
        <span className="soft-tag">soft · slow</span>
      </div>
      <p className="script">“{script}”</p>
      <div className="audio-bar">
        <button type="button" aria-label="Play audio preview">
          <Play size={17} fill="currentColor" />
        </button>
        <span />
      </div>
    </article>
  );
}

function CrosswordPanel() {
  const cells = [
    false,
    false,
    true,
    false,
    false,
    true,
    false,
    false,
    false,
    true,
    false,
    false,
    false,
    true,
    false,
    false,
    true,
    false,
    false,
    false,
    true,
    false,
    false,
    false,
    false,
  ];

  return (
    <article className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Crossword Agent</p>
          <h3>Hidden itinerary</h3>
        </div>
        <span className="soft-tag">4 clues</span>
      </div>
      <div className="crossword" aria-label="Crossword preview">
        {cells.map((filled, index) => (
          <span className={filled ? "filled" : ""} key={index} />
        ))}
      </div>
    </article>
  );
}

export default function App() {
  const [pipelineResponse, setPipelineResponse] = useState(null);
  const [runState, setRunState] = useState("idle");
  const [runError, setRunError] = useState("");

  const intent = mapIntent(pipelineResponse?.visit_intent);
  const stages = mapStages(pipelineResponse?.outputs);
  const signals = mapMemorySignals(defaultPipelineRequest.ambient_signals);
  const currentAudioScript = pipelineResponse?.audio_script ?? audioScript;

  async function handleRunPipeline() {
    setRunState("running");
    setRunError("");

    try {
      const response = await runRosewoodPipeline(defaultPipelineRequest);
      setPipelineResponse(response);
      setRunState("complete");
    } catch (error) {
      setRunError(error.message);
      setRunState("error");
    }
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="workspace">
        <Topbar />
        <HeroBand />

        <section className="grid-two">
          <IntentPanel intent={intent} />
          <MemoryPanel signals={signals} />
        </section>

        <PipelinePanel stages={stages} onRun={handleRunPipeline} runState={runState} />
        {runError ? <p className="api-error">Backend unavailable: {runError}</p> : null}

        <section className="grid-two letter-grid">
          <LetterPreview letter={pipelineResponse?.letter} />
          <div className="right-stack">
            <AudioPanel script={currentAudioScript} />
            <CrosswordPanel />
            <article className="panel build-next">
              <Leaf size={22} />
              <div>
                <p className="eyebrow">Next build target</p>
                <h3>Add the staff input panel and Memory Agent.</h3>
              </div>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
