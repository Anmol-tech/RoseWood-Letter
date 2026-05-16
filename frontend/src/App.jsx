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
  letterParagraphs,
  memorySignals,
  pipelineStages,
  visitIntent,
} from "./data/rosewoodPipeline.js";

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

function IntentPanel() {
  const rows = [
    ["Emotional state", visitIntent.emotionalState],
    ["Engagement style", visitIntent.engagementStyle],
    ["Narrative frame", visitIntent.narrativeFrame],
    ["Scent profile", visitIntent.scentProfile],
  ];

  return (
    <article className="panel intent-panel" id="intent">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Visit Intent Object</p>
          <h3>{visitIntent.label}</h3>
        </div>
        <span className="confidence">{visitIntent.confidence}%</span>
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

function MemoryPanel() {
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
        {memorySignals.map((item) => (
          <p key={`${item.time}-${item.signal}`}>
            <strong>{item.time}</strong> {item.signal}
          </p>
        ))}
      </div>
    </article>
  );
}

function PipelinePanel() {
  const [activeStage, setActiveStage] = useState(1);
  const [isRunning, setIsRunning] = useState(false);

  const buttonText = useMemo(() => {
    if (!isRunning) return "Run simulation";
    return pipelineStages[activeStage]?.statusText ?? "Pipeline complete";
  }, [activeStage, isRunning]);

  function runPipeline() {
    setIsRunning(true);
    setActiveStage(0);

    pipelineStages.forEach((_, index) => {
      window.setTimeout(() => {
        setActiveStage(index);
      }, index * 650);
    });

    window.setTimeout(() => {
      setIsRunning(false);
      setActiveStage(pipelineStages.length);
    }, pipelineStages.length * 650);
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
        {pipelineStages.map((stage, index) => {
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

function LetterPreview() {
  return (
    <article className="letter-preview" id="letter" aria-label="Printed letter preview">
      <header className="letter-head">
        <span>ROSEWOOD</span>
        <p>Morning letter · May 17, 2030</p>
      </header>
      <div className="letter-body">
        <p className="salutation">Good morning,</p>
        {letterParagraphs.map((paragraph) => (
          <p key={paragraph}>{paragraph}</p>
        ))}
      </div>
      <footer className="letter-foot">
        <div className="qr-mark" aria-label="QR code placeholder" />
        <span>A personal note from Rosewood.</span>
      </footer>
    </article>
  );
}

function AudioPanel() {
  return (
    <article className="panel" id="audio">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Audio Agent</p>
          <h3>60 second note</h3>
        </div>
        <span className="soft-tag">soft · slow</span>
      </div>
      <p className="script">“{audioScript}”</p>
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
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="workspace">
        <Topbar />
        <HeroBand />

        <section className="grid-two">
          <IntentPanel />
          <MemoryPanel />
        </section>

        <PipelinePanel />

        <section className="grid-two letter-grid">
          <LetterPreview />
          <div className="right-stack">
            <AudioPanel />
            <CrosswordPanel />
            <article className="panel build-next">
              <Leaf size={22} />
              <div>
                <p className="eyebrow">Next build target</p>
                <h3>Swap static fixtures for real agent output.</h3>
              </div>
            </article>
          </div>
        </section>
      </main>
    </div>
  );
}
