import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CalendarClock,
  FileText,
  Headphones,
  Moon,
  Play,
  Printer,
  QrCode,
  Radio,
  Sparkles,
} from "lucide-react";
import {
  audioScript,
  fallbackScenarios,
  letterParagraphs,
  memorySignals,
  pipelineStages,
  visitIntent,
} from "./data/rosewoodPipeline.js";
import { getDemoScenarios, runRosewoodPipeline } from "./services/api.js";

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

function mapMemorySignals(response, request) {
  if (response?.memory?.signals?.length) {
    return [
      ...response.memory.signals,
      {
        time: "Signal",
        signal: response.memory.inferred_pattern,
      },
    ];
  }

  if (request?.ambient_signals?.length) {
    return request.ambient_signals;
  }

  return memorySignals;
}

function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Rosewood Letter operations">
      <div className="brand-lockup">
        <span className="brand-mark">R</span>
        <div>
          <p className="eyebrow">Rosewood Letter</p>
          <h1>Night Ops</h1>
        </div>
      </div>

      <nav className="nav-stack" aria-label="Primary">
        <a className="nav-item active" href="#queue">
          <CalendarClock size={17} />
          Queue
        </a>
        <a className="nav-item" href="#pipeline">
          <Activity size={17} />
          Trace
        </a>
        <a className="nav-item" href="#letter">
          <Printer size={17} />
          Print Studio
        </a>
        <a className="nav-item" href="#audio">
          <Headphones size={17} />
          Voice Note
        </a>
      </nav>

      <div className="night-run">
        <p className="eyebrow">Dawn handoff</p>
        <strong>05:42</strong>
        <span>Letter, QR, scent, voice script</span>
      </div>
    </aside>
  );
}

function Topbar({ profile, runState }) {
  const stateLabel = runState === "running" ? "Running overnight pass" : "Ready for 03:00 run";

  return (
    <section className="topbar" aria-label="Current guest context">
      <div>
        <p className="eyebrow">Hotel staff console</p>
        <h2>Suite {profile.suite} · {profile.guest_name}</h2>
      </div>
      <div className="status-pill">
        <span className="pulse" />
        {stateLabel}
      </div>
    </section>
  );
}

function OperationsQueue({ profile, intent, printArtifact, audio }) {
  const cells = [
    ["Run window", "03:00", "Silent agent pass"],
    ["Print handoff", printArtifact?.delivery_window ?? "06:00", printArtifact?.print_status ?? "ready"],
    ["Scent", intent.scentProfile, "paper profile"],
    ["Voice", audio?.voice ?? "soft and slow", audio?.status ?? "script ready"],
  ];

  return (
    <section className="ops-board" id="queue">
      <div className="ops-copy">
        <p className="eyebrow">Night operations console</p>
        <h2>One guest, one morning artifact.</h2>
        <p>
          {profile.booking_notes}
        </p>
      </div>
      <div className="ops-grid" aria-label="Production queue">
        {cells.map(([label, value, meta]) => (
          <div className="ops-cell" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
            <small>{meta}</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function ScenarioConsole({ scenarios, selectedId, onSelect }) {
  return (
    <section className="scenario-console" aria-label="Demo guest scenarios">
      <div className="section-label">
        <Radio size={17} />
        <span>Guest Profile + Stay Context</span>
      </div>
      <div className="scenario-rail">
        {scenarios.map((scenario) => (
          <button
            className={`scenario-tab${scenario.id === selectedId ? " active" : ""}`}
            key={scenario.id}
            onClick={() => onSelect(scenario.id)}
            type="button"
          >
            <strong>{scenario.title}</strong>
            <span>{scenario.description}</span>
          </button>
        ))}
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
          <p className="eyebrow">Memory Agent</p>
          <h3>Ambient signals</h3>
        </div>
        <span className="soft-tag">zero survey</span>
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
    if (runState === "error") return "Retry overnight run";
    if (!isRunning) return "Run 03:00 pass";
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
          <p className="eyebrow">Execution trace</p>
          <h3>3AM agent run</h3>
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

function ArtifactSpec({ printArtifact, letter }) {
  const specs = [
    ["Format", letter?.pdf_status ?? "html ready"],
    ["Scent", printArtifact?.paper_scent ?? visitIntent.scentProfile],
    ["QR", printArtifact?.qr_url ?? "pending voice note"],
    ["Status", printArtifact?.print_status ?? "ready for composition"],
  ];

  return (
    <article className="panel spec-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Letter Composer</p>
          <h3>Print artifact studio</h3>
        </div>
        <FileText size={20} />
      </div>
      <dl className="spec-list">
        {specs.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

function AudioPanel({ audio, script }) {
  return (
    <article className="panel" id="audio">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Audio Script Agent</p>
          <h3>Voice note</h3>
        </div>
        <span className="soft-tag">{audio?.voice ?? "soft · slow"}</span>
      </div>
      <p className="script">"{script}"</p>
      <div className="audio-bar">
        <button type="button" aria-label="Play audio preview">
          <Play size={17} fill="currentColor" />
        </button>
        <span />
      </div>
    </article>
  );
}

function CrosswordPanel({ crossword }) {
  const cells = [
    false, false, true, false, false,
    true, false, false, false, true,
    false, false, false, true, false,
    false, true, false, false, false,
    true, false, false, false, false,
  ];
  const clues = crossword?.clues?.slice(0, 3) ?? [];

  return (
    <article className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Crossword Agent</p>
          <h3>Hidden itinerary</h3>
        </div>
        <span className="soft-tag">{clues.length || 4} clues</span>
      </div>
      <div className="crossword" aria-label="Crossword preview">
        {cells.map((filled, index) => (
          <span className={filled ? "filled" : ""} key={index} />
        ))}
      </div>
      {clues.length ? (
        <ul className="clue-list">
          {clues.map((clue) => (
            <li key={`${clue.clue}-${clue.answer}`}>
              <span>{clue.clue}</span>
              <strong>{clue.answer}</strong>
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function QRPanel({ printArtifact }) {
  return (
    <article className="panel qr-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">QR Code</p>
          <h3>Guest handoff</h3>
        </div>
        <QrCode size={20} />
      </div>
      <div className="handoff-row">
        <div className="qr-mark large" aria-label="QR code placeholder" />
        <p>{printArtifact?.qr_caption ?? "A personal note from Rosewood."}</p>
      </div>
    </article>
  );
}

export default function App() {
  const [scenarios, setScenarios] = useState(fallbackScenarios);
  const [selectedScenarioId, setSelectedScenarioId] = useState(fallbackScenarios[0].id);
  const [pipelineResponse, setPipelineResponse] = useState(null);
  const [runState, setRunState] = useState("idle");
  const [runError, setRunError] = useState("");

  useEffect(() => {
    getDemoScenarios()
      .then((items) => {
        setScenarios(items);
        setSelectedScenarioId((current) => (items.some((item) => item.id === current) ? current : items[0].id));
      })
      .catch(() => {
        setScenarios(fallbackScenarios);
      });
  }, []);

  const selectedScenario = scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0];
  const selectedRequest = selectedScenario.request;
  const profile = pipelineResponse?.profile ?? selectedRequest.profile;
  const intent = mapIntent(pipelineResponse?.visit_intent);
  const stages = mapStages(pipelineResponse?.outputs);
  const signals = mapMemorySignals(pipelineResponse, selectedRequest);
  const currentAudioScript = pipelineResponse?.audio_script ?? audioScript;

  function selectScenario(scenarioId) {
    setSelectedScenarioId(scenarioId);
    setPipelineResponse(null);
    setRunState("idle");
    setRunError("");
  }

  async function handleRunPipeline() {
    setRunState("running");
    setRunError("");

    try {
      const response = await runRosewoodPipeline(selectedRequest);
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
        <Topbar profile={profile} runState={runState} />
        <OperationsQueue
          audio={pipelineResponse?.audio}
          intent={intent}
          printArtifact={pipelineResponse?.print_artifact}
          profile={profile}
        />

        <ScenarioConsole
          onSelect={selectScenario}
          scenarios={scenarios}
          selectedId={selectedScenarioId}
        />

        <section className="grid-two">
          <IntentPanel intent={intent} />
          <MemoryPanel signals={signals} />
        </section>

        <PipelinePanel stages={stages} onRun={handleRunPipeline} runState={runState} />
        {runError ? <p className="api-error">Backend unavailable: {runError}</p> : null}

        <section className="studio-grid">
          <LetterPreview letter={pipelineResponse?.letter} />
          <div className="right-stack">
            <ArtifactSpec letter={pipelineResponse?.letter} printArtifact={pipelineResponse?.print_artifact} />
            <AudioPanel audio={pipelineResponse?.audio} script={currentAudioScript} />
            <CrosswordPanel crossword={pipelineResponse?.crossword} />
            <QRPanel printArtifact={pipelineResponse?.print_artifact} />
          </div>
        </section>
      </main>
    </div>
  );
}
