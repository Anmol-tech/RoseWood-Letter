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
  getDemoScenarios,
  getRosewoodJobHistoryItem,
  getRosewoodPipelineJobs,
  listRosewoodJobHistory,
  startRosewoodPipelineJobs,
} from "./services/api.js";

const PIPELINE_STAGES = [
  { name: "Intent", agent: "Intent Agent" },
  { name: "World", agent: "World Agent" },
  { name: "Rhythm", agent: "Rhythm Agent" },
  { name: "Discovery", agent: "Discovery Agent" },
  { name: "Memory", agent: "Memory Agent" },
  { name: "Resonance", agent: "Temporal Resonance Layer" },
  { name: "Voice", agent: "Voice Agent" },
  { name: "Crossword", agent: "Crossword Agent" },
  { name: "Compositor", agent: "Compositor Agent" },
  { name: "Audio", agent: "Audio Agent" },
];

function cleanText(text = "") {
  return text.replace(/\u2014/g, ", ").replace(/\u2013/g, "-");
}

function getQrImageUrl(qrUrl = "", size = 180) {
  if (!qrUrl) return "";
  return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&margin=10&data=${encodeURIComponent(qrUrl)}`;
}

function getGuestLetterJobId() {
  const match = window.location.pathname.match(/^\/letter\/([^/]+)$/);
  return match ? decodeURIComponent(match[1]) : "";
}

function getMoodClass(label = "") {
  const normalized = label.toLowerCase();
  if (normalized.includes("milestone")) return "mood-milestone";
  if (normalized.includes("celebration")) return "mood-celebration";
  if (normalized.includes("conference") || normalized.includes("event")) return "mood-event";
  return "mood-restoration";
}

function getScenarioLocation(scenario) {
  return scenario?.request?.profile?.property_location ?? "Rosewood Property";
}

function mapIntent(intent) {
  if (!intent) {
    return {
      label: "Pending",
      confidence: 0,
      emotionalState: "Waiting for generated output",
      engagementStyle: "Pending",
      narrativeFrame: "Pending",
      scentProfile: "Pending",
    };
  }

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

function GuestHome({
  locationFilter,
  onGenerateOne,
  onGenerateSelected,
  onLocationFilterChange,
  onToggle,
  scenarios,
  selectedIds,
}) {
  const locations = Array.from(
    new Set(scenarios.map(getScenarioLocation)),
  ).sort((a, b) => a.localeCompare(b));
  const filteredScenarios = locationFilter === "all"
    ? scenarios
    : scenarios.filter((scenario) => getScenarioLocation(scenario) === locationFilter);
  const visibleSelectedIds = filteredScenarios
    .filter((scenario) => selectedIds.includes(scenario.id))
    .map((scenario) => scenario.id);
  const selectedCount = visibleSelectedIds.length;
  const selectedLabel = locationFilter === "all"
    ? `${selectedCount || "selected"}`
    : `${selectedCount || "selected"} at ${locationFilter}`;

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
        <button
          className="primary-action large"
          disabled={!selectedCount}
          onClick={() => onGenerateSelected(visibleSelectedIds)}
          type="button"
        >
          <Moon size={18} />
          Generate {selectedLabel}
        </button>
      </section>

      <section className="filter-bar" aria-label="Guest filters">
        <label>
          <span>Location</span>
          <select value={locationFilter} onChange={(event) => onLocationFilterChange(event.target.value)}>
            <option value="all">All Rosewood locations</option>
            {locations.map((location) => (
              <option key={location} value={location}>{location}</option>
            ))}
          </select>
        </label>
        <p>{filteredScenarios.length} guests shown · {selectedCount} selected in view</p>
      </section>

      {filteredScenarios.length ? (
        <section className="guest-grid" aria-label="Guest list">
          {filteredScenarios.map((scenario) => {
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
                  <p className="eyebrow">{profile.property_location} · Suite {profile.suite}</p>
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
      ) : (
        <section className="empty-state">
          <Users size={28} />
          <h2>No backend guests loaded</h2>
          <p>Start the backend and ensure `GET /scenarios` is available.</p>
        </section>
      )}
    </main>
  );
}

function formatRunTimestamp(value) {
  if (!value) return "No timestamp";
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getJobLocation(job) {
  if (job.location) return job.location;
  if (job.response?.profile?.property_location) return job.response.profile.property_location;

  const notes = job.response?.profile?.booking_notes ?? "";
  if (notes.includes(":")) return notes.split(":")[0].trim();
  return "Rosewood Property";
}

function groupJobsByLocation(jobs) {
  return jobs.reduce((groups, job) => {
    const location = getJobLocation(job);
    return {
      ...groups,
      [location]: [...(groups[location] ?? []), job],
    };
  }, {});
}

function mergeJobs(incoming, existing) {
  const byId = new Map();
  [...incoming, ...existing].forEach((job) => {
    if (!byId.has(job.job_id)) {
      byId.set(job.job_id, job);
    }
  });

  return Array.from(byId.values()).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );
}

function JobList({ jobs, selectedJobId, onSelect }) {
  if (!jobs.length) {
    return (
      <section className="empty-state">
        <Moon size={28} />
        <h2>No generation run yet</h2>
        <p>Choose guests from the home screen and start artifact generation.</p>
      </section>
    );
  }

  const groupedJobs = groupJobsByLocation(jobs);
  const locations = Object.keys(groupedJobs).sort((a, b) => a.localeCompare(b));

  return (
    <section className="job-list-panel">
      <div className="job-list-head">
        <div>
          <p className="eyebrow">Generation history</p>
          <h2>{jobs.length} saved jobs</h2>
        </div>
        <span>{jobs.filter((job) => job.status === "running").length} running · {jobs.filter((job) => job.status === "completed").length} complete</span>
      </div>
      {locations.map((location) => (
        <section className="hotel-job-group" key={location}>
          <div className="hotel-job-head">
            <div>
              <p className="eyebrow">Rosewood location</p>
              <h3>{location}</h3>
            </div>
            <span>{groupedJobs[location].length} jobs</span>
          </div>
          <div className="job-list">
            {groupedJobs[location].map((job) => (
              <button
                className={`job-row ${job.status} ${job.job_id === selectedJobId ? "active" : ""}`}
                key={job.job_id}
                onClick={() => onSelect(job.job_id)}
                type="button"
              >
                <StatusIcon status={job.status} />
                <span className="job-main">
                  <strong>{job.guest_name}</strong>
                  <small>
                    {job.location} · Suite {job.suite} · {formatRunTimestamp(job.created_at)} · {job.current_agents[0] ?? job.completed_agents.at(-1) ?? "Waiting"}
                  </small>
                </span>
                <span className="job-progress">
                  <i style={{ width: `${job.progress}%` }} />
                </span>
              </button>
            ))}
          </div>
        </section>
      ))}
    </section>
  );
}

function StatusIcon({ status }) {
  if (status === "completed") return <CheckCircle2 className="status-icon ok" size={18} />;
  if (status === "failed") return <AlertTriangle className="status-icon bad" size={18} />;
  if (status === "running") return <Loader2 className="status-icon spin" size={18} />;
  return <Moon className="status-icon" size={18} />;
}

function JobsScreen({ jobs, onSelect, onBack }) {
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
      <JobList jobs={jobs} selectedJobId="" onSelect={onSelect} />
    </main>
  );
}

function DetailScreen({ jobs, selectedJobId, onBackToRuns, onBackToGuests }) {
  const selectedJob = jobs.find((job) => job.job_id === selectedJobId) ?? jobs[0];

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
        {PIPELINE_STAGES.map((stage) => (
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
  const paragraphs = (letter?.paragraphs ?? []).map(cleanText);
  const qrUrl = response?.print_artifact?.qr_url || letter?.qr_url || "";
  const qrImageUrl = getQrImageUrl(qrUrl);

  return (
    <section className={`detail-panel result-detail ${moodClass}`}>
      <div className="result-header">
        <div>
          <p className="eyebrow">Generated artifact</p>
          <h2>{job.guest_name}</h2>
          <span>{job.location} · Suite {job.suite} · {intent.label} · {intent.confidence}%</span>
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
            {qrImageUrl ? (
              <a className="qr-mark real" href={qrUrl} rel="noreferrer" target="_blank">
                <img alt="QR code for the personal Rosewood note" src={qrImageUrl} />
              </a>
            ) : (
              <div className="qr-mark" aria-label="QR code placeholder" />
            )}
            <span>{letter?.qr_caption ?? "A personal note from Rosewood."}</span>
          </footer>
        </article>

        <aside className="artifact-stack">
          <ArtifactCard icon={<Printer size={18} />} label="Print" value={response?.print_artifact?.print_status} />
          <ArtifactCard icon={<Headphones size={18} />} label="Voice" value={response?.audio?.voice} />
          <ArtifactCard icon={<QrCode size={18} />} label="QR" value={response?.print_artifact?.qr_url} />
          <CrosswordAnswerKey crossword={crossword} />
          <article className="artifact-card audio-card">
            <div>
              <p className="eyebrow">ElevenLabs voice note</p>
              <strong>{response?.audio?.status ?? "script_ready"}</strong>
              <p>"{cleanText(response?.audio_script ?? "")}"</p>
              {response?.audio?.audio_url ? (
                <audio controls src={response.audio.audio_url}>
                  <track kind="captions" />
                </audio>
              ) : (
                <small>No audio file generated yet. Check ElevenLabs key and voice id.</small>
              )}
            </div>
            <a
              aria-label="Open audio file"
              className={response?.audio?.audio_url ? "" : "disabled"}
              href={response?.audio?.audio_url ?? "#"}
              rel="noreferrer"
              target="_blank"
            >
              <Play size={16} fill="currentColor" />
            </a>
          </article>
        </aside>
      </div>
    </section>
  );
}

function CrosswordAnswerKey({ crossword }) {
  if (!crossword?.entries?.length) return null;

  return (
    <details className="artifact-card crossword-answer-card">
      <summary>
        <FileText size={18} />
        <span>
          <p className="eyebrow">Crossword answer key</p>
          <strong>{crossword.entries.length} answers</strong>
        </span>
      </summary>
      <div className="answer-list-wrap">
        <ul>
          {crossword.entries.map((entry) => (
            <li key={`${entry.number}-${entry.answer}`}>
              <span>{entry.number} {entry.direction}</span>
              <strong>{entry.answer}</strong>
            </li>
          ))}
        </ul>
      </div>
    </details>
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

function GuestLetterPage({ error, job }) {
  if (error) {
    return (
      <main className="guest-letter-shell">
        <section className="guest-letter-status">
          <AlertTriangle size={24} />
          <h1>We could not open this note.</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  if (!job || job.status !== "completed") {
    return (
      <main className="guest-letter-shell">
        <section className="guest-letter-status">
          <Loader2 className="spin" size={24} />
          <h1>Your Rosewood note is being prepared.</h1>
          <p>{job?.current_agents?.[0] ?? "The final artifact is still settling into place."}</p>
        </section>
      </main>
    );
  }

  const response = job.response;
  const letter = response?.letter;
  const crossword = response?.crossword;
  const paragraphs = (letter?.paragraphs ?? []).map(cleanText);

  return (
    <main className={`guest-letter-shell ${getMoodClass(response?.visit_intent?.label)}`}>
      <section className="guest-letter-layout">
        <article className="letter-preview guest-facing">
          <header className="letter-head">
            <div className="letter-brand">
              <span>ROSEWOOD</span>
              <small>{letter?.date_line ?? "Morning letter"}</small>
            </div>
          </header>
          <div className="letter-body">
            <p className="salutation">{cleanText(letter?.salutation ?? `Good morning, ${job.guest_name}.`)}</p>
            {paragraphs.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
          <LetterCrossword crossword={crossword} />
        </article>

        <aside className="guest-note-panel">
          <p className="eyebrow">A personal note from Rosewood</p>
          <h1>{job.guest_name}</h1>
          <p>{job.location} · Suite {job.suite}</p>
          {response?.audio?.audio_url ? (
            <audio controls src={response.audio.audio_url}>
              <track kind="captions" />
            </audio>
          ) : (
            <p className="audio-missing">The written note is ready. The voice note has not been generated yet.</p>
          )}
          <p className="guest-script">"{cleanText(response?.audio_script ?? "")}"</p>
          <CrosswordAnswerKey crossword={crossword} />
        </aside>
      </section>
    </main>
  );
}

export default function App() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [locationFilter, setLocationFilter] = useState("all");
  const [screen, setScreen] = useState("home");
  const [batch, setBatch] = useState(null);
  const [jobHistory, setJobHistory] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [guestLetterJobId, setGuestLetterJobId] = useState(getGuestLetterJobId);
  const [guestLetterJob, setGuestLetterJob] = useState(null);
  const [guestLetterError, setGuestLetterError] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    function handleRouteChange() {
      setGuestLetterJobId(getGuestLetterJobId());
    }

    window.addEventListener("popstate", handleRouteChange);
    return () => window.removeEventListener("popstate", handleRouteChange);
  }, []);

  useEffect(() => {
    if (!guestLetterJobId) return undefined;

    let cancelled = false;
    let interval = null;

    async function loadGuestLetter() {
      try {
        const job = await getRosewoodJobHistoryItem(guestLetterJobId);
        if (cancelled) return;
        setGuestLetterJob(job);
        setGuestLetterError("");
        if (job.status === "completed" || job.status === "failed") {
          if (interval) window.clearInterval(interval);
        }
      } catch (loadError) {
        if (cancelled) return;
        setGuestLetterError(loadError.message);
      }
    }

    loadGuestLetter();
    interval = window.setInterval(loadGuestLetter, 1400);

    return () => {
      cancelled = true;
      if (interval) window.clearInterval(interval);
    };
  }, [guestLetterJobId]);

  useEffect(() => {
    if (guestLetterJobId) return;

    getDemoScenarios()
      .then((items) => {
        setScenarios(items);
        setSelectedIds(items.map((scenario) => scenario.id));
      })
      .catch(() => {
        setError("Failed to load guests from backend.");
      });

    listRosewoodJobHistory()
      .then((jobs) => {
        setJobHistory(jobs);
        setSelectedJobId((current) => current || jobs[0]?.job_id || "");
      })
      .catch(() => {});
  }, [guestLetterJobId]);

  useEffect(() => {
    if (!batch?.batch_id) return undefined;
    const done = batch.total > 0 && batch.completed + batch.failed === batch.total;
    if (done) return undefined;

    const interval = window.setInterval(async () => {
      try {
        const nextBatch = await getRosewoodPipelineJobs(batch.batch_id);
        setBatch(nextBatch);
        setJobHistory((current) => mergeJobs(nextBatch.jobs, current));
        setSelectedJobId((current) => current || nextBatch.jobs[0]?.job_id || "");
      } catch (pollError) {
        setError(pollError.message);
      }
    }, 1200);

    return () => window.clearInterval(interval);
  }, [batch]);

  const moodClass = useMemo(() => {
    const selectedJob = jobHistory.find((job) => job.job_id === selectedJobId);
    return getMoodClass(selectedJob?.response?.visit_intent?.label);
  }, [jobHistory, selectedJobId]);

  function toggleGuest(id) {
    setSelectedIds((current) => (
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id]
    ));
  }

  async function startGeneration(ids, location = "all") {
    const requests = scenarios
      .filter((scenario) => ids.includes(scenario.id))
      .filter((scenario) => location === "all" || getScenarioLocation(scenario) === location)
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
      setJobHistory((current) => mergeJobs(started.jobs, current));
      setSelectedJobId(started.jobs[0]?.job_id ?? "");
    } catch (startError) {
      setError(startError.message);
    }
  }

  if (guestLetterJobId) {
    return <GuestLetterPage error={guestLetterError} job={guestLetterJob} />;
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
          onGenerateSelected={(ids) => startGeneration(ids, locationFilter)}
          onLocationFilterChange={setLocationFilter}
          onToggle={toggleGuest}
          locationFilter={locationFilter}
          scenarios={scenarios}
          selectedIds={selectedIds}
        />
      ) : (
        screen === "jobs" ? (
          <JobsScreen
            jobs={jobHistory}
            onBack={() => setScreen("home")}
            onSelect={(jobId) => {
              setSelectedJobId(jobId);
              setScreen("detail");
            }}
          />
        ) : (
          <DetailScreen
            jobs={jobHistory}
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
