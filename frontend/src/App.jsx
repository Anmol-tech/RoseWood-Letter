import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  FileText,
  Headphones,
  Loader2,
  Moon,
  Play,
  Printer,
  QrCode,
  Users,
} from "lucide-react";
import {
  fallbackScenarios,
  letterParagraphs,
  pipelineStages,
  visitIntent,
} from "./data/rosewoodPipeline.js";
import {
  getDemoScenarios,
  getRosewoodPipelineJobs,
  listRosewoodPipelineJobs,
  startRosewoodPipelineJobs,
} from "./services/api.js";

function cleanText(text = "") {
  return text.replace(/\u2014/g, ", ").replace(/\u2013/g, "-");
}

function getMoodClass(label = "") {
  const normalized = label.toLowerCase();
  if (normalized.includes("milestone")) return "mood-milestone";
  if (normalized.includes("celebration")) return "mood-celebration";
  return "mood-restoration";
}

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

function Sidebar({ screen, onHome, onJobs }) {
  return (
    <aside className="sidebar" aria-label="Rosewood Letter">
      <div className="brand-lockup">
        <span className="brand-mark">R</span>
        <div>
          <p className="eyebrow">Rosewood Letter</p>
          <h1>Night Ops</h1>
        </div>
      </div>
      <nav className="nav-stack" aria-label="Primary">
        <button className={`nav-item ${screen === "home" ? "active" : ""}`} onClick={onHome} type="button">
          <Users size={17} />
          Guests
        </button>
        <button className={`nav-item ${screen !== "home" ? "active" : ""}`} onClick={onJobs} type="button">
          <Moon size={17} />
          Runs
        </button>
      </nav>
      <div className="night-run">
        <p className="eyebrow">Generation window</p>
        <strong>03:00</strong>
        <span>Parallel artifacts before dawn</span>
      </div>
    </aside>
  );
}

function GuestHome({ scenarios, selectedIds, onToggle, onGenerateOne, onGenerateSelected }) {
  const selectedCount = selectedIds.length;

  return (
    <main className="workspace">
      <section className="page-hero">
        <div>
          <p className="eyebrow">Check-in guests</p>
          <h2>Tonight's arrival list</h2>
          <p>
            Review the guests currently checked in or arriving tonight. Generate the
            Rosewood Letter for one guest, or run the full overnight artifact pass.
          </p>
        </div>
        <button className="primary-action large" disabled={!selectedCount} onClick={onGenerateSelected} type="button">
          <Moon size={18} />
          Generate {selectedCount || "selected"}
        </button>
      </section>

      <section className="guest-grid" aria-label="Guest list">
        {scenarios.map((scenario) => {
          const profile = scenario.request.profile;
          const selected = selectedIds.includes(scenario.id);

          return (
            <article className={`guest-card ${selected ? "selected" : ""}`} key={scenario.id}>
              <header>
                <label className="guest-check">
                  <input
                    checked={selected}
                    onChange={() => onToggle(scenario.id)}
                    type="checkbox"
                  />
                  <span />
                </label>
                <div>
                  <p className="eyebrow">Suite {profile.suite}</p>
                  <h3>{profile.guest_name}</h3>
                </div>
              </header>
              <p>{scenario.description}</p>
              <dl className="guest-meta">
                <div>
                  <dt>Occasion</dt>
                  <dd>{profile.occasion ?? "private stay"}</dd>
                </div>
                <div>
                  <dt>Nights</dt>
                  <dd>{profile.stay_nights}</dd>
                </div>
                <div>
                  <dt>Persona</dt>
                  <dd>{profile.persona?.segment ?? "Restoration Seeker"}</dd>
                </div>
              </dl>
              <button className="secondary-action" onClick={() => onGenerateOne(scenario.id)} type="button">
                Generate this guest
              </button>
            </article>
          );
        })}
      </section>
    </main>
  );
}

function JobList({ batch, selectedJobId, onSelect }) {
  if (!batch) {
    return (
      <section className="empty-state">
        <Moon size={28} />
        <h2>No generation run yet</h2>
        <p>Choose guests from the home screen and start artifact generation.</p>
      </section>
    );
  }

  return (
    <section className="job-list-panel">
      <div className="job-list-head">
        <div>
          <p className="eyebrow">Generation jobs</p>
          <h2>{batch.completed}/{batch.total} completed</h2>
        </div>
        <span>{batch.running} running · {batch.queued} queued · {batch.failed} failed</span>
      </div>
      <div className="job-list">
        {batch.jobs.map((job) => (
          <button
            className={`job-row ${job.status} ${job.job_id === selectedJobId ? "active" : ""}`}
            key={job.job_id}
            onClick={() => onSelect(job.job_id)}
            type="button"
          >
            <StatusIcon status={job.status} />
            <span className="job-main">
              <strong>{job.guest_name}</strong>
              <small>Suite {job.suite} · {job.current_agents[0] ?? job.completed_agents.at(-1) ?? "Waiting"}</small>
            </span>
            <span className="job-progress">
              <i style={{ width: `${job.progress}%` }} />
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}

function StatusIcon({ status }) {
  if (status === "completed") return <CheckCircle2 className="status-icon ok" size={18} />;
  if (status === "failed") return <AlertTriangle className="status-icon bad" size={18} />;
  if (status === "running") return <Loader2 className="status-icon spin" size={18} />;
  return <Moon className="status-icon" size={18} />;
}

function JobsScreen({ batch, onSelect, onBack }) {
  return (
    <main className="workspace jobs-layout">
      <section className="jobs-topbar">
        <button className="secondary-action" onClick={onBack} type="button">
          <ChevronLeft size={17} />
          Guests
        </button>
        <div>
          <p className="eyebrow">Overnight production</p>
          <h2>Artifact generation queue</h2>
        </div>
      </section>
      <JobList batch={batch} selectedJobId="" onSelect={onSelect} />
    </main>
  );
}

function DetailScreen({ batch, selectedJobId, onBackToRuns, onBackToGuests }) {
  const selectedJob = batch?.jobs.find((job) => job.job_id === selectedJobId) ?? batch?.jobs[0];

  return (
    <main className="workspace detail-layout">
      <section className="jobs-topbar">
        <button className="secondary-action" onClick={onBackToRuns} type="button">
          <ChevronLeft size={17} />
          Runs
        </button>
        <div>
          <p className="eyebrow">Job detail</p>
          <h2>{selectedJob?.guest_name ?? "Generation output"}</h2>
        </div>
        <button className="secondary-action" onClick={onBackToGuests} type="button">
          Guests
        </button>
      </section>
      <JobDetail job={selectedJob} />
    </main>
  );
}

function JobDetail({ job }) {
  if (!job) {
    return (
      <section className="empty-state">
        <FileText size={28} />
        <h2>Select a job</h2>
        <p>The generated letter and production artifacts will appear here.</p>
      </section>
    );
  }

  if (job.status === "failed") {
    return (
      <section className="detail-panel failed-run">
        <p className="eyebrow">Job failed</p>
        <h2>{job.guest_name}</h2>
        <p>{job.error ?? "The backend returned an error for this guest."}</p>
      </section>
    );
  }

  if (job.status !== "completed") {
    return <RunningJobDetail job={job} />;
  }

  return <CompletedJobDetail job={job} />;
}

function RunningJobDetail({ job }) {
  const completed = new Set(job.completed_agents);

  return (
    <section className="detail-panel running-job">
      <div className="running-stage">
        <div className="running-orbit" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="eyebrow">Live pipeline</p>
          <h2>{job.guest_name}</h2>
          <p>
            {job.current_agents.length
              ? `${job.current_agents.join(", ")} working now.`
              : "Waiting for the next agent group."}
          </p>
        </div>
      </div>
      <div className="large-progress">
        <i style={{ width: `${job.progress}%` }} />
      </div>
      <div className="agent-timeline">
        {pipelineStages.map((stage) => (
          <div className={completed.has(stage.agent) ? "done" : ""} key={stage.agent}>
            <span>{stage.name}</span>
            <small>{completed.has(stage.agent) ? "complete" : "pending"}</small>
          </div>
        ))}
        <div className={completed.has("Audio Agent") ? "done" : ""}>
          <span>Audio</span>
          <small>{completed.has("Audio Agent") ? "complete" : "pending"}</small>
        </div>
      </div>
    </section>
  );
}

function CompletedJobDetail({ job }) {
  const response = job.response;
  const intent = mapIntent(response?.visit_intent);
  const moodClass = getMoodClass(intent.label);
  const letter = response?.letter;
  const crossword = response?.crossword;
  const paragraphs = (letter?.paragraphs ?? letterParagraphs).map(cleanText);

  return (
    <section className={`detail-panel result-detail ${moodClass}`}>
      <div className="result-header">
        <div>
          <p className="eyebrow">Generated artifact</p>
          <h2>{job.guest_name}</h2>
          <span>Suite {job.suite} · {intent.label} · {intent.confidence}%</span>
        </div>
        <span className="status-pill">
          <CheckCircle2 size={16} />
          Complete
        </span>
      </div>

      <div className="result-grid">
        <article className="letter-preview compact">
          <header className="letter-head">
            <div className="letter-brand">
              <span>ROSEWOOD</span>
              <small>{letter?.date_line ?? "Morning letter · May 17, 2030"}</small>
            </div>
          </header>
          <div className="letter-body">
            <p className="salutation">{cleanText(letter?.salutation ?? "Good morning,")}</p>
            {paragraphs.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
          <LetterCrossword crossword={crossword} />
          <footer className="letter-foot">
            <div className="qr-mark" aria-label="QR code placeholder" />
            <span>{letter?.qr_caption ?? "A personal note from Rosewood."}</span>
          </footer>
        </article>

        <aside className="artifact-stack">
          <ArtifactCard icon={<Printer size={18} />} label="Print" value={response?.print_artifact.print_status} />
          <ArtifactCard icon={<Headphones size={18} />} label="Voice" value={response?.audio.voice} />
          <ArtifactCard icon={<QrCode size={18} />} label="QR" value={response?.print_artifact.qr_url} />
          <CrosswordAnswerKey crossword={crossword} />
          <article className="artifact-card audio-card">
            <div>
              <p className="eyebrow">Audio script</p>
              <p>"{cleanText(response?.audio_script ?? "")}"</p>
            </div>
            <button type="button" aria-label="Play audio preview">
              <Play size={16} fill="currentColor" />
            </button>
          </article>
        </aside>
      </div>
    </section>
  );
}

function CrosswordAnswerKey({ crossword }) {
  if (!crossword?.entries?.length) return null;

  return (
    <article className="artifact-card crossword-answer-card">
      <FileText size={18} />
      <div>
        <p className="eyebrow">Crossword answer key</p>
        <ul>
          {crossword.entries.map((entry) => (
            <li key={`${entry.number}-${entry.answer}`}>
              <span>{entry.number} {entry.direction}</span>
              <strong>{entry.answer}</strong>
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

function LetterCrossword({ crossword }) {
  if (!crossword?.grid?.length || !crossword?.entries?.length) return null;

  const starts = new Map(
    crossword.entries.map((entry) => [`${entry.row}:${entry.col}`, entry.number]),
  );

  return (
    <section className="letter-crossword" aria-label="Morning crossword">
      <div className="letter-crossword-head">
        <p className="eyebrow">Morning Crossword</p>
        <h3>{crossword.title ?? "Hidden itinerary"}</h3>
      </div>
      <div
        className="letter-crossword-grid"
        style={{ gridTemplateColumns: `repeat(${crossword.grid[0]?.length ?? 1}, minmax(0, 1fr))` }}
      >
        {crossword.grid.flatMap((row, rowIndex) => (
          row.map((cell, colIndex) => {
            const key = `${rowIndex}:${colIndex}`;
            const number = starts.get(key);

            return (
              <span
                className={cell ? "letter-crossword-cell" : "letter-crossword-cell empty"}
                data-answer={cell ?? ""}
                key={key}
              >
                {number ? <small>{number}</small> : null}
              </span>
            );
          })
        ))}
      </div>
      <ol className="letter-crossword-clues">
        {crossword.entries.map((entry) => (
          <li key={`${entry.number}-${entry.answer}`}>
            <strong>{entry.number} {entry.direction}</strong>
            <span>{cleanText(entry.clue)}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function ArtifactCard({ icon, label, value }) {
  return (
    <article className="artifact-card">
      {icon}
      <div>
        <p className="eyebrow">{label}</p>
        <strong>{value ?? "ready"}</strong>
      </div>
    </article>
  );
}

export default function App() {
  const [scenarios, setScenarios] = useState(fallbackScenarios);
  const [selectedIds, setSelectedIds] = useState(fallbackScenarios.map((scenario) => scenario.id));
  const [screen, setScreen] = useState("home");
  const [batch, setBatch] = useState(null);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getDemoScenarios()
      .then((items) => {
        setScenarios(items);
        setSelectedIds(items.map((scenario) => scenario.id));
      })
      .catch(() => {
        setScenarios(fallbackScenarios);
      });

    listRosewoodPipelineJobs()
      .then((batches) => {
        if (batches.length) {
          setBatch(batches[0]);
          setSelectedJobId(batches[0].jobs[0]?.job_id ?? "");
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!batch?.batch_id) return undefined;
    const done = batch.total > 0 && batch.completed + batch.failed === batch.total;
    if (done) return undefined;

    const interval = window.setInterval(async () => {
      try {
        const nextBatch = await getRosewoodPipelineJobs(batch.batch_id);
        setBatch(nextBatch);
        setSelectedJobId((current) => current || nextBatch.jobs[0]?.job_id || "");
      } catch (pollError) {
        setError(pollError.message);
      }
    }, 1200);

    return () => window.clearInterval(interval);
  }, [batch]);

  const moodClass = useMemo(() => {
    const selectedJob = batch?.jobs.find((job) => job.job_id === selectedJobId);
    return getMoodClass(selectedJob?.response?.visit_intent?.label);
  }, [batch, selectedJobId]);

  function toggleGuest(id) {
    setSelectedIds((current) => (
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    ));
  }

  async function startGeneration(ids) {
    const requests = scenarios
      .filter((scenario) => ids.includes(scenario.id))
      .map((scenario) => scenario.request);

    if (!requests.length) return;

    setError("");
    setScreen("jobs");

    try {
      const started = await startRosewoodPipelineJobs({
        max_concurrency: Math.min(3, requests.length),
        requests,
      });
      setBatch(started);
      setSelectedJobId(started.jobs[0]?.job_id ?? "");
    } catch (startError) {
      setError(startError.message);
    }
  }

  return (
    <div className={`app-shell ${moodClass}`}>
      <Sidebar
        onHome={() => setScreen("home")}
        onJobs={() => setScreen("jobs")}
        screen={screen}
      />
      {screen === "home" ? (
        <GuestHome
          onGenerateOne={(id) => startGeneration([id])}
          onGenerateSelected={() => startGeneration(selectedIds)}
          onToggle={toggleGuest}
          scenarios={scenarios}
          selectedIds={selectedIds}
        />
      ) : (
        screen === "jobs" ? (
          <JobsScreen
            batch={batch}
            onBack={() => setScreen("home")}
            onSelect={(jobId) => {
              setSelectedJobId(jobId);
              setScreen("detail");
            }}
          />
        ) : (
          <DetailScreen
            batch={batch}
            onBackToGuests={() => setScreen("home")}
            onBackToRuns={() => setScreen("jobs")}
            selectedJobId={selectedJobId}
          />
        )
      )}
      {error ? <p className="toast-error">{error}</p> : null}
    </div>
  );
}
