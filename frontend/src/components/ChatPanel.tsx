import { useEffect, useRef, useState } from "react";
import type { ExecutionContext, Message, TutorReply } from "../types";

const API = import.meta.env.VITE_API_BASE_URL || "";
const MODES = [
  ["explain", "Explain"],
  ["hint", "Give a hint"],
  ["predict", "Quiz me"],
  ["debug", "Debug"],
] as const;
const STARTERS = [
  "Explain this step",
  "Why do we save the key?",
  "What stays true as we sort?",
];

async function readJson(response: Response) {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    throw new Error(
      response.status === 429
        ? "Too many questions at once. Wait a moment and try again."
        : typeof detail === "string"
          ? detail
          : response.status === 422
            ? "Check the supplied code, context, and question."
            : "The server could not complete this request.",
    );
  }
  return body;
}

export default function ChatPanel() {
  const [frames, setFrames] = useState<ExecutionContext[]>([]);
  const [position, setPosition] = useState(0);
  const [values, setValues] = useState("2, 7, 9, 4");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("explain");
  const [strategy, setStrategy] = useState("auto");
  const [level, setLevel] = useState("beginner");
  const [loading, setLoading] = useState(false);
  const [traceLoading, setTraceLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);
  const [provider, setProvider] = useState("Connecting");
  const [custom, setCustom] = useState("");
  const [customContext, setCustomContext] = useState<ExecutionContext | null>(
    null,
  );
  const [contextLabel, setContextLabel] = useState("Reference demo");
  const abort = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const context = customContext ?? frames[position];

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API}/api/health`, { signal: controller.signal })
      .then(readJson)
      .then((data) =>
        setProvider(
          data.provider_configured
            ? `${data.provider} · ${data.model}`
            : "Model setup needed",
        ),
      )
      .catch(() => setProvider("Backend offline"));
    fetch(`${API}/api/demo/insertion-sort?values=2,7,9,4`, {
      signal: controller.signal,
    })
      .then(readJson)
      .then((data) => setFrames(data.frames))
      .catch((e) => {
        if (e.name !== "AbortError")
          setTraceError("Start the backend to load the visualization.");
      });
    return () => {
      controller.abort();
      abort.current?.abort();
    };
  }, []);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, loading]);
  useEffect(() => {
    if (!playing || customContext || loading) return;
    const timer = window.setInterval(
      () =>
        setPosition((p) => {
          if (p >= frames.length - 1) {
            setPlaying(false);
            return p;
          }
          return p + 1;
        }),
      1400,
    );
    return () => window.clearInterval(timer);
  }, [playing, customContext, frames.length, loading]);

  async function loadDemo() {
    setTraceLoading(true);
    setPlaying(false);
    setTraceError(null);
    try {
      const data = await fetch(
        `${API}/api/demo/insertion-sort?values=${encodeURIComponent(values)}`,
      ).then(readJson);
      setFrames(data.frames);
      setPosition(0);
      setCustomContext(null);
      setContextLabel("Reference demo");
      setMessages([]);
      setError(null);
    } catch (e) {
      setTraceError(
        e instanceof Error ? e.message : "Could not load the trace.",
      );
    } finally {
      setTraceLoading(false);
    }
  }

  async function loadContext() {
    setTraceError(null);
    try {
      const parsed = JSON.parse(custom);
      // Server validates the complete schema; no provider call is made here.
      const data = await fetch(`${API}/api/context/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed),
      }).then(readJson);
      setCustomContext(data);
      setPlaying(false);
      setMessages([]);
      setContextLabel("Imported snapshot");
      setError(null);
    } catch (e) {
      setTraceError(e instanceof Error ? e.message : "Invalid snapshot JSON.");
    }
  }

  async function ask(question = input) {
    if (!question.trim() || loading) return;
    setPlaying(false);
    setError(null);
    setLoading(true);
    const submitted = question.trim();
    const step = context?.step;
    const history = messages.slice(-6).map((m) => ({
      role: m.role,
      content:
        `${m.step !== undefined ? `[At step ${m.step}] ` : ""}${m.content}`.slice(
          0,
          1800,
        ),
    }));
    const userMessage: Message = { role: "user", content: submitted, step };
    setMessages((previous) => [...previous, userMessage]);
    setInput("");
    const controller = new AbortController();
    abort.current = controller;
    const timer = window.setTimeout(() => controller.abort(), 195000);
    try {
      const response: TutorReply = await fetch(`${API}/api/tutor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          question: submitted,
          mode,
          level,
          strategy,
          context: context ?? null,
          history,
        }),
      }).then(readJson);
      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: response.answer, step, reply: response },
      ]);
    } catch (e) {
      setError(
        e instanceof Error && e.name === "AbortError"
          ? "Request stopped. You can edit the question and try again."
          : e instanceof Error
            ? e.message
            : "Could not reach the tutor.",
      );
      setMessages((previous) => previous.filter((m) => m !== userMessage));
      setInput(submitted);
    } finally {
      window.clearTimeout(timer);
      setLoading(false);
      abort.current = null;
      inputRef.current?.focus();
    }
  }

  const array =
    context?.arrays?.collection ??
    Object.values(context?.arrays ?? {})[0] ??
    [];
  const latest = context?.recent_events?.[context.recent_events.length - 1];
  const indices = latest?.indices ?? [];
  const maxValue = Math.max(
    1,
    ...array.map((v) => (typeof v === "number" ? Math.abs(v) : 1)),
  );
  const codeLines = context?.code.split("\n") ?? [];

  return (
    <div className="app-shell">
      <header className="topbar">
        <a href="./" className="brand" aria-label="AVP Tutor home">
          <span className="brand-symbol">a↗</span>
          <span>
            AVP<span className="brand-light"> / tutor</span>
          </span>
        </a>
        <span className="topbar-caption">Make the next step make sense.</span>
        <span
          className="provider"
          title="Configured provider; reachability is checked when you ask a question"
        >
          <span className="status-dot" />
          {provider}
        </span>
      </header>
      <main>
        <div className="page-heading">
          <div>
            <p className="eyebrow">TUTOR INTEGRATION TEST HARNESS</p>
            <h1>Understand every move.</h1>
            <p>Step through the algorithm. Ask about what you see.</p>
          </div>
          <span className="context-tag">{contextLabel}</span>
        </div>
        <div className="workspace">
          <section
            className="visual-column"
            aria-label="Algorithm visualization"
          >
            <div className="panel visualization">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">01 / OBSERVE</p>
                  <h2>
                    {customContext
                      ? context?.algorithm.replace(/_/g, " ") ||
                        "Your algorithm"
                      : "Insertion sort"}
                  </h2>
                </div>
                <span className="pill">
                  {customContext ? "Snapshot" : "Ascending order"}
                </span>
              </div>
              <p className="description">
                {customContext
                  ? "The tutor will use the snapshot supplied by your visualizer."
                  : "Build a sorted prefix, one element at a time."}
              </p>
              <div
                className="array-stage"
                aria-label={`Array: ${array.map(String).join(", ") || "empty"}`}
              >
                {array.length === 0 && (
                  <p className="empty-array">
                    An empty collection is already sorted.
                  </p>
                )}
                {array.map((value, index) => (
                  <div
                    className={`array-item ${indices.includes(index) ? "active" : ""}`}
                    key={index}
                  >
                    <span className="bar-value">{String(value)}</span>
                    <div
                      className="bar"
                      style={{
                        height: `${Math.max(18, ((typeof value === "number" ? Math.abs(value) : 1) / maxValue) * 108)}px`,
                      }}
                    />
                    <span className="bar-index">{index}</span>
                  </div>
                ))}
              </div>
              <div className="event-caption" aria-live="polite">
                <span className="event-dot" />
                {latest?.description ?? "Waiting for an execution snapshot."}
              </div>
              <div className="variables">
                {Object.entries(context?.variables ?? {}).map(
                  ([name, value]) => (
                    <span className="variable" key={name}>
                      <span>{name}</span>
                      <strong>{JSON.stringify(value)}</strong>
                    </span>
                  ),
                )}
              </div>
              {!customContext && (
                <div className="playback">
                  <div className="playback-buttons">
                    <button
                      aria-label="Previous step"
                      disabled={position === 0 || loading || traceLoading}
                      onClick={() => {
                        setPlaying(false);
                        setPosition((p) => p - 1);
                      }}
                    >
                      ←
                    </button>
                    <button
                      className="play"
                      disabled={!frames.length || loading || traceLoading}
                      onClick={() => {
                        if (position >= frames.length - 1) setPosition(0);
                        setPlaying((v) => !v);
                      }}
                    >
                      {playing ? "Pause" : "Play"}
                    </button>
                    <button
                      aria-label="Next step"
                      disabled={
                        position >= frames.length - 1 || loading || traceLoading
                      }
                      onClick={() => {
                        setPlaying(false);
                        setPosition((p) => p + 1);
                      }}
                    >
                      →
                    </button>
                  </div>
                  <input
                    aria-label="Execution step"
                    type="range"
                    min={0}
                    max={Math.max(0, frames.length - 1)}
                    value={position}
                    disabled={loading || traceLoading}
                    onChange={(e) => {
                      setPlaying(false);
                      setPosition(Number(e.target.value));
                    }}
                  />
                  <span className="step-count">
                    {position} / {Math.max(0, frames.length - 1)}
                  </span>
                </div>
              )}
              <details className="configure">
                <summary>Change input or connect your visualizer</summary>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    loadDemo();
                  }}
                >
                  <label htmlFor="array-values">
                    Demo input · up to 24 integers
                  </label>
                  <div className="input-row">
                    <input
                      id="array-values"
                      value={values}
                      onChange={(e) => setValues(e.target.value)}
                      placeholder="3, 1, 2"
                    />
                    <button disabled={loading || traceLoading}>
                      Load trace
                    </button>
                  </div>
                </form>
                <label htmlFor="context-json">Execution snapshot JSON</label>
                <textarea
                  id="context-json"
                  value={custom}
                  onChange={(e) => setCustom(e.target.value)}
                  placeholder='{"algorithm":"...","code":"...","phase":"after"}'
                  rows={4}
                />
                <button
                  disabled={loading || !custom.trim()}
                  onClick={loadContext}
                >
                  Use snapshot
                </button>
              </details>
              {traceError && (
                <p className="error" role="alert">
                  {traceError}
                </p>
              )}
            </div>
            <div className="panel code-panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">02 / FOLLOW THE CODE</p>
                  <h2>Behind the animation</h2>
                </div>
                <span className="pill">AVP</span>
              </div>
              <p className="code-legend">
                {context?.phase === "after"
                  ? "Highlighted line has just executed."
                  : context?.phase === "before"
                    ? "Highlighted line is next to execute."
                    : "Execution phase is unspecified."}
              </p>
              <div className="code-scroll">
                <pre aria-label="Algorithm source code">
                  {codeLines.map((line, index) => (
                    <div
                      key={index}
                      className={`code-line ${context?.current_line === index + 1 ? "highlighted" : ""}`}
                      aria-current={
                        context?.current_line === index + 1 ? "step" : undefined
                      }
                    >
                      <span className="line-number">{index + 1}</span>
                      <code>{line || " "}</code>
                    </div>
                  ))}
                </pre>
              </div>
            </div>
          </section>
          <section className="panel tutor-panel" aria-label="Algorithm tutor">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">03 / ASK WHY</p>
                <h2>Your learning companion</h2>
              </div>
              <button
                className="text-button"
                disabled={loading || messages.length === 0}
                onClick={() => {
                  setMessages([]);
                  setError(null);
                }}
              >
                Clear chat
              </button>
            </div>
            <p className="description">
              Grounded in the code and the step in front of you.
            </p>
            <div className="tutor-options">
              <div className="mode-tabs" role="group" aria-label="Tutor mode">
                {MODES.map(([value, label]) => (
                  <button
                    key={value}
                    aria-pressed={mode === value}
                    onClick={() => setMode(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <label className="level-label">
                Level
                <select
                  aria-label="Explanation level"
                  value={level}
                  onChange={(e) => setLevel(e.target.value)}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </label>
              <label className="level-label">
                Strategy
                <select
                  aria-label="Explanation strategy"
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                >
                  {[
                    "auto",
                    "trace",
                    "analogy",
                    "comparison",
                    "invariant",
                    "worked-example",
                    "guided-question",
                  ].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div
              className="conversation"
              role="log"
              aria-label="Conversation"
              aria-live="polite"
            >
              {messages.length === 0 && (
                <div className="welcome">
                  <span className="welcome-symbol">↳</span>
                  <h3>A little curiosity goes a long way.</h3>
                  <p>
                    Ask about a value, a line, or the bigger idea. I’ll use your
                    current step to help explain it.
                  </p>
                  <div className="starters">
                    {STARTERS.map((question) => (
                      <button
                        key={question}
                        disabled={loading}
                        onClick={() => ask(question)}
                      >
                        {question}
                        <span>↗</span>
                      </button>
                    ))}
                  </div>
                  <p className="welcome-note">
                    Try “Give a hint” to work it out yourself.
                  </p>
                </div>
              )}
              {messages.map((message, index) => (
                <article key={index} className={`message ${message.role}`}>
                  <div className="message-meta">
                    <strong>
                      {message.role === "user" ? "You" : "AVP tutor"}
                    </strong>
                    {message.step !== undefined && (
                      <span>Step {message.step}</span>
                    )}
                  </div>
                  <div className="message-content">{message.content}</div>
                  {message.reply?.warnings.map((warning) => (
                    <p className="answer-warning" key={warning}>
                      {warning}
                    </p>
                  ))}
                  {!!message.reply?.sources.length && (
                    <details className="sources">
                      <summary>
                        {message.reply.sources.length} teaching references
                        provided to the model
                      </summary>
                      {message.reply.sources.map((source) => (
                        <div key={source.id}>
                          <strong>
                            {source.title} / {source.section}
                          </strong>
                          <p>{source.text}</p>
                          <code>{source.id}</code>
                        </div>
                      ))}
                    </details>
                  )}
                  {message.reply?.teaching_decision && (
                    <details className="sources">
                      <summary>How this answer was prepared</summary>
                      <p>
                        {message.reply.teaching_decision.action} ·{" "}
                        {message.reply.teaching_decision.strategy}
                      </p>
                      {message.reply.teaching_decision.reasons.map((reason) => (
                        <p key={reason}>{reason}</p>
                      ))}
                      <p>
                        Supplied-field checks: {message.reply.evidence?.status}.
                        No independent execution or answer verification.
                      </p>
                      <p>
                        {message.reply.code_examples?.length ?? 0}{" "}
                        syntax-checked reference examples; implementation
                        equivalence is unverified.
                      </p>
                    </details>
                  )}
                  {message.reply && (
                    <span className="reply-meta">
                      {message.reply.model} ·{" "}
                      {(message.reply.latency_ms / 1000).toFixed(1)}s
                      {message.reply.fallback_used
                        ? " · fallback provider"
                        : ""}
                    </span>
                  )}
                </article>
              ))}
              {loading && (
                <div className="thinking" role="status">
                  <span className="thinking-dot" />
                  Working through your question…{" "}
                  <button onClick={() => abort.current?.abort()}>Stop</button>
                </div>
              )}
              <div ref={bottom} />
            </div>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <form
              className="composer"
              onSubmit={(e) => {
                e.preventDefault();
                ask();
              }}
            >
              <label className="sr-only" htmlFor="question">
                Ask the tutor
              </label>
              <textarea
                id="question"
                ref={inputRef}
                value={input}
                maxLength={4000}
                onChange={(e) => setInput(e.target.value)}
                placeholder="What would you like to understand?"
                rows={3}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey &&
                    !e.nativeEvent.isComposing
                  ) {
                    e.preventDefault();
                    ask();
                  }
                }}
              />
              <div className="composer-bottom">
                <span>
                  {context
                    ? `Context attached · step ${context.step ?? "unknown"}`
                    : "No execution context attached"}
                </span>
                <button className="send" disabled={!input.trim() || loading}>
                  Ask tutor <span>↑</span>
                </button>
              </div>
            </form>
            <p className="disclaimer">
              AI explanations can be wrong. The visualization supplies the
              execution state.
            </p>
          </section>
        </div>
        <footer>
          Temporary test harness · integrate the API into your team’s frontend.
          <a
            href="https://github.com/jhunter11/avp-tutor"
            target="_blank"
            rel="noreferrer"
          >
            Project & integration guide ↗
          </a>
        </footer>
      </main>
    </div>
  );
}
