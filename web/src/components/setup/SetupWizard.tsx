"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { buildConfig, parseSetupJson, resolveSetup } from "../../game/config";
import {
  BOOLEAN_RULE_KEYS,
  PLAYER_SPECS,
  PRESETS,
  PROFILE_RULES,
  SPEED_DELAYS,
  isBlockades,
} from "../../game/presets";
import type {
  Blockades,
  CommentaryMode,
  MatchConfig,
  PlayerKind,
  ResolvedSetup,
  SetupInput,
  Speed,
} from "../../game/types";
import type { LoadMatchResult } from "../../match/persistence";
import { JsonConfigPanel } from "./JsonConfigPanel";
import { setupFromUrl } from "./url-setup";
import styles from "./SetupWizard.module.css";

type RuleKey = (typeof BOOLEAN_RULE_KEYS)[number];
type WizardRules = Record<RuleKey, boolean>;

interface WizardState {
  mode: MatchConfig["mode"];
  profile: MatchConfig["profile"];
  playerCount: number;
  tokens: number;
  maxTurns: number;
  seed: string;
  blockades: Blockades;
  commentary: CommentaryMode;
  speed: Speed;
  autoplay: boolean;
  reducedMotion: boolean;
  names: string[];
  kinds: PlayerKind[];
  rules: WizardRules;
}

const DEFAULT_CONFIG = buildConfig("quick", "showcase", 2, {
  tokens_per_player: 2,
  max_turns: 100,
  seed: null,
  commentary: "gameplay",
  ui: "gui",
});

const RULE_LABELS: Record<RuleKey, { title: string; description: string }> = {
  kill_to_enter: {
    title: "Kill-to-Enter",
    description: "Landing on a rival token returns it to its yard.",
  },
  podium_mode: {
    title: "Podium finish",
    description: "Finished players stay on the podium while others continue.",
  },
  exact_home_roll: {
    title: "Exact home roll",
    description: "The final step into Home requires the exact number.",
  },
  triple_six_forfeit: {
    title: "Triple-six forfeit",
    description: "A third consecutive six forfeits the turn.",
  },
  safe_tiles_enabled: {
    title: "Safe tiles",
    description: "Marked route tiles prevent captures.",
  },
  bonus_on_capture: {
    title: "Capture bonus",
    description: "A capture earns another roll.",
  },
  bonus_on_home: {
    title: "Home bonus",
    description: "Bringing a token Home earns another roll.",
  },
};

function defaultWizard(): WizardState {
  return {
    mode: DEFAULT_CONFIG.mode,
    profile: DEFAULT_CONFIG.profile,
    playerCount: DEFAULT_CONFIG.player_count,
    tokens: DEFAULT_CONFIG.tokens_per_player,
    maxTurns: DEFAULT_CONFIG.max_turns,
    seed: "",
    blockades: DEFAULT_CONFIG.blockades,
    commentary: DEFAULT_CONFIG.commentary,
    speed: "normal",
    autoplay: false,
    reducedMotion: false,
    names: ["Ada", "Grace", "Linus", "Margaret"],
    kinds: ["human", "human", "human", "human"],
    rules: {
      kill_to_enter: DEFAULT_CONFIG.kill_to_enter,
      podium_mode: DEFAULT_CONFIG.podium_mode,
      exact_home_roll: DEFAULT_CONFIG.exact_home_roll,
      triple_six_forfeit: DEFAULT_CONFIG.triple_six_forfeit,
      safe_tiles_enabled: DEFAULT_CONFIG.safe_tiles_enabled,
      bonus_on_capture: DEFAULT_CONFIG.bonus_on_capture,
      bonus_on_home: DEFAULT_CONFIG.bonus_on_home,
    },
  };
}

function mergeSource(current: WizardState, source: SetupInput): WizardState {
  const next: WizardState = {
    ...current,
    names: [...current.names],
    kinds: [...current.kinds],
    rules: { ...current.rules },
  };
  if (source.mode === "quick" || source.mode === "classic") {
    next.mode = source.mode;
    next.tokens = PRESETS[source.mode].tokens_per_player;
    next.maxTurns = PRESETS[source.mode].default_max_turns;
  }
  if (source.profile === "showcase" || source.profile === "classic") {
    next.profile = source.profile;
    next.rules = { ...PROFILE_RULES[source.profile] };
    next.blockades = PROFILE_RULES[source.profile].blockades;
  }
  if (typeof source.player_count === "number" && [2, 3, 4].includes(source.player_count)) {
    next.playerCount = source.player_count;
  }
  if (
    typeof source.tokens_per_player === "number" &&
    Number.isInteger(source.tokens_per_player) &&
    source.tokens_per_player >= 1 &&
    source.tokens_per_player <= 4
  ) {
    next.tokens = source.tokens_per_player;
  }
  if (
    typeof source.max_turns === "number" &&
    Number.isSafeInteger(source.max_turns) &&
    source.max_turns > 0
  ) {
    next.maxTurns = source.max_turns;
  }
  if (typeof source.seed === "number" || source.seed === null)
    next.seed = source.seed === null ? "" : String(source.seed);
  if (isBlockades(source.blockades)) next.blockades = source.blockades;
  if (
    source.commentary === "gameplay" ||
    source.commentary === "code" ||
    source.commentary === "both" ||
    source.commentary === "off"
  ) {
    next.commentary = source.commentary;
  }
  if (source.speed === "slow" || source.speed === "normal" || source.speed === "fast")
    next.speed = source.speed;
  if (typeof source.autoplay === "boolean") next.autoplay = source.autoplay;
  if (Array.isArray(source.names)) {
    source.names.forEach((name, index) => {
      if (index < 4 && typeof name === "string") next.names[index] = name;
    });
  }
  const kinds = source.kinds ?? source.seat;
  if (Array.isArray(kinds)) {
    kinds.forEach((kind, index) => {
      if (index < 4 && (kind === "human" || kind === "bot")) next.kinds[index] = kind;
    });
  }
  for (const key of BOOLEAN_RULE_KEYS) {
    if (typeof source[key] === "boolean") next.rules[key] = source[key];
  }
  return next;
}

function wizardSource(state: WizardState): SetupInput {
  return {
    mode: state.mode,
    profile: state.profile,
    player_count: state.playerCount,
    tokens_per_player: state.tokens,
    max_turns: state.maxTurns,
    seed: state.seed.trim() === "" ? null : Number(state.seed),
    blockades: state.blockades,
    commentary: state.commentary,
    ui: "gui",
    names: state.names.slice(0, state.playerCount),
    kinds: state.kinds.slice(0, state.playerCount),
    autoplay: state.autoplay,
    speed: state.speed,
    ...state.rules,
  };
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function SetupWizard({
  savedMatch,
  onStart,
  onResume,
  onResetSaved,
}: {
  savedMatch: LoadMatchResult | null;
  onStart: (setup: ResolvedSetup, reducedMotion: boolean) => void;
  onResume: (match: Extract<LoadMatchResult, { status: "valid" }>["match"]) => void;
  onResetSaved: () => void;
}) {
  const [state, setState] = useState<WizardState>(defaultWizard);
  const [urlSource, setUrlSource] = useState<SetupInput>({});
  const [importedSource, setImportedSource] = useState<SetupInput | null>(null);
  const [jsonText, setJsonText] = useState("");
  const [jsonError, setJsonError] = useState("");
  const [urlError, setUrlError] = useState("");
  const [urlReady, setUrlReady] = useState(false);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (!active) return;
      try {
        const parsed = setupFromUrl(window.location.search);
        setUrlSource(parsed.source);
        setState((current) => ({
          ...mergeSource(current, parsed.source),
          reducedMotion: parsed.reducedMotion,
        }));
      } catch (error) {
        setUrlError(error instanceof Error ? error.message : "URL settings could not be read.");
      } finally {
        if (active) setUrlReady(true);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const resolution = useMemo(() => {
    try {
      const setup = resolveSetup({
        wizard: wizardSource(state),
        ...(importedSource ? { json: importedSource } : {}),
        ...(Object.keys(urlSource).length > 0 ? { url: urlSource } : {}),
      });
      return { setup, error: "" };
    } catch (error) {
      try {
        return {
          setup: resolveSetup({ wizard: wizardSource(state) }),
          error: error instanceof Error ? error.message : "Configuration could not be resolved.",
        };
      } catch {
        return { setup: resolveSetup({}), error: "Check the seed, turn cap, and rule values." };
      }
    }
  }, [state, importedSource, urlSource]);

  function changeMode(mode: MatchConfig["mode"]): void {
    setState((current) => ({
      ...current,
      mode,
      tokens: PRESETS[mode].tokens_per_player,
      maxTurns: PRESETS[mode].default_max_turns,
    }));
  }

  function changeProfile(profile: MatchConfig["profile"]): void {
    setState((current) => ({
      ...current,
      profile,
      blockades: PROFILE_RULES[profile].blockades,
      rules: { ...PROFILE_RULES[profile] },
    }));
  }

  function loadConfiguration(text: string): void {
    try {
      const source = parseSetupJson(text);
      resolveSetup({ json: source });
      setImportedSource(source);
      setState((current) => mergeSource(current, source));
      setJsonText(text);
      setJsonError("");
    } catch (error) {
      setImportedSource(null);
      setJsonError(error instanceof Error ? error.message : "Configuration JSON is invalid.");
    }
  }

  const setupError = urlError || resolution.error;

  return (
    <main className={styles.page}>
      <header className={styles.masthead}>
        <Link className={styles.brand} href="/" aria-label="Ludo Showcase home">
          <span className={styles.brandMark} aria-hidden="true">
            {PLAYER_SPECS.map((spec) => (
              <i key={spec.color} style={{ background: spec.hex }} />
            ))}
          </span>
          <span>Ludo Showcase</span>
        </Link>
        <span className={styles.edition}>Local table · v3</span>
      </header>

      <section className={styles.hero} aria-labelledby="setup-title">
        <div>
          <p className="eyebrow">Four seats. One browser. No account.</p>
          <h1 id="setup-title">
            Your table.
            <br />
            Your rules.
          </h1>
          <p className={styles.lede}>
            Play locally with friends, hand a seat to a deterministic bot, or watch the whole table
            unfold. Every roll follows the same verified rules as the Python showcase.
          </p>
        </div>
        <aside className={styles.ticket} aria-label="Local-first match details">
          <span className={styles.ticketStub}>Table 01</span>
          <div>
            <p className="eyebrow">Admit everyone</p>
            <h2>Hot-seat multiplayer</h2>
            <p>2–4 players · Quick or Classic board</p>
          </div>
          <dl>
            <div>
              <dt>Storage</dt>
              <dd>This browser only</dd>
            </div>
            <div>
              <dt>Online rooms</dt>
              <dd>Planned, not active</dd>
            </div>
            <div>
              <dt>Engine</dt>
              <dd>Python-parity TypeScript</dd>
            </div>
          </dl>
        </aside>
      </section>

      {savedMatch?.status === "valid" ? (
        <section className={styles.resumeCard} aria-label="Saved match">
          <div>
            <p className="eyebrow">Saved in this browser</p>
            <h2>
              {titleCase(savedMatch.match.config.mode)} match ·{" "}
              {savedMatch.match.config.player_count} players
            </h2>
            <p>
              {titleCase(savedMatch.match.snapshot.status)} · Turn{" "}
              {savedMatch.match.snapshot.turn_count}
            </p>
          </div>
          <div className={styles.resumeActions}>
            <button
              className="button buttonPrimary"
              type="button"
              onClick={() => onResume(savedMatch.match)}
            >
              Resume match
            </button>
            <button className="button" type="button" onClick={onResetSaved}>
              Start new match
            </button>
          </div>
        </section>
      ) : null}

      {savedMatch?.status === "invalid" ? (
        <div className={styles.savedAlert}>
          <p className="alert" role="alert">
            Saved match could not be restored: {savedMatch.reason}
          </p>
          <button className="button buttonDanger buttonSmall" type="button" onClick={onResetSaved}>
            Reset saved data
          </button>
        </div>
      ) : null}

      {savedMatch === null ? (
        <p className={styles.checking}>Checking this browser for a saved match…</p>
      ) : null}

      <div className={styles.setupGrid}>
        <form
          className={styles.form}
          onSubmit={(event) => {
            event.preventDefault();
            if (!setupError) onStart(resolution.setup, state.reducedMotion);
          }}
        >
          <section aria-labelledby="board-heading">
            <div className={styles.sectionHeading}>
              <span>01</span>
              <div>
                <p className="eyebrow">Choose the board</p>
                <h2 id="board-heading">Mode and profile</h2>
              </div>
            </div>
            <fieldset className={styles.cardGrid}>
              <legend className="srOnly">Board mode</legend>
              {(["quick", "classic"] as const).map((mode) => (
                <label className={styles.choiceCard} key={mode}>
                  <input
                    type="radio"
                    name="mode"
                    value={mode}
                    checked={state.mode === mode}
                    onChange={() => changeMode(mode)}
                  />
                  <span>
                    <strong>{titleCase(mode)}</strong>
                    <small>
                      {mode === "quick"
                        ? "28 route tiles · 4 Home steps"
                        : "52 route tiles · 5 Home steps"}
                    </small>
                  </span>
                </label>
              ))}
            </fieldset>
            <fieldset className={styles.cardGrid}>
              <legend className="srOnly">Rule profile</legend>
              {(["showcase", "classic"] as const).map((profile) => (
                <label className={styles.choiceCard} key={profile}>
                  <input
                    type="radio"
                    name="profile"
                    value={profile}
                    checked={state.profile === profile}
                    onChange={() => changeProfile(profile)}
                  />
                  <span>
                    <strong>{titleCase(profile)}</strong>
                    <small>
                      {profile === "showcase"
                        ? "Kill-to-Enter, safe pairs, podium"
                        : "Familiar Ludo, no blockades"}
                    </small>
                  </span>
                </label>
              ))}
            </fieldset>
          </section>

          <section aria-labelledby="seats-heading">
            <div className={styles.sectionHeading}>
              <span>02</span>
              <div>
                <p className="eyebrow">Set the table</p>
                <h2 id="seats-heading">Players and seats</h2>
              </div>
            </div>
            <div className={styles.numberGrid}>
              <label className="field">
                <span>Players</span>
                <select
                  className="select"
                  value={state.playerCount}
                  onChange={(event) =>
                    setState((current) => ({ ...current, playerCount: Number(event.target.value) }))
                  }
                >
                  <option value={2}>2 players</option>
                  <option value={3}>3 players</option>
                  <option value={4}>4 players</option>
                </select>
              </label>
              <label className="field">
                <span>Tokens each</span>
                <select
                  className="select"
                  value={state.tokens}
                  onChange={(event) =>
                    setState((current) => ({ ...current, tokens: Number(event.target.value) }))
                  }
                >
                  <option value={1}>1 token</option>
                  <option value={2}>2 tokens</option>
                  <option value={3}>3 tokens</option>
                  <option value={4}>4 tokens</option>
                </select>
              </label>
              <label className="field">
                <span>Turn cap</span>
                <input
                  className="input"
                  type="number"
                  min={1}
                  max={100000}
                  value={state.maxTurns}
                  onChange={(event) =>
                    setState((current) => ({ ...current, maxTurns: Number(event.target.value) }))
                  }
                />
              </label>
              <label className="field">
                <span>Seed (optional)</span>
                <input
                  className="input"
                  type="number"
                  step={1}
                  value={state.seed}
                  placeholder="Random"
                  onChange={(event) =>
                    setState((current) => ({ ...current, seed: event.target.value }))
                  }
                />
              </label>
            </div>
            <div className={styles.seatList}>
              {Array.from({ length: state.playerCount }, (_, index) => (
                <div className={styles.seatRow} key={index}>
                  <span
                    className={styles.seatColor}
                    style={{ background: PLAYER_SPECS[index]!.hex }}
                    aria-hidden="true"
                  />
                  <label className="field">
                    <span>Seat {index + 1} name</span>
                    <input
                      className="input"
                      value={state.names[index]}
                      maxLength={40}
                      onChange={(event) =>
                        setState((current) => {
                          const names = [...current.names];
                          names[index] = event.target.value;
                          return { ...current, names };
                        })
                      }
                    />
                  </label>
                  <label className="field">
                    <span>Seat {index + 1} type</span>
                    <select
                      className="select"
                      value={state.kinds[index]}
                      onChange={(event) =>
                        setState((current) => {
                          const kinds = [...current.kinds];
                          kinds[index] = event.target.value as PlayerKind;
                          return { ...current, kinds };
                        })
                      }
                    >
                      <option value="human">Human</option>
                      <option value="bot">Bot</option>
                    </select>
                  </label>
                </div>
              ))}
            </div>
          </section>

          <details className={styles.rules}>
            <summary>Fine-tune the rules</summary>
            <p className={styles.rulesIntro}>
              Board geometry stays locked to the selected mode. These options change play, not the
              shape of the board.
            </p>
            <label className="field">
              <span>Blockades</span>
              <select
                className="select"
                value={state.blockades}
                onChange={(event) =>
                  setState((current) => ({
                    ...current,
                    blockades: event.target.value as Blockades,
                  }))
                }
              >
                <option value="none">None</option>
                <option value="strict">Strict</option>
                <option value="safe_pair">Safe pair</option>
              </select>
            </label>
            <div className={styles.ruleGrid}>
              {BOOLEAN_RULE_KEYS.map((key) => (
                <label className="checkbox" key={key}>
                  <input
                    type="checkbox"
                    checked={state.rules[key]}
                    onChange={(event) =>
                      setState((current) => ({
                        ...current,
                        rules: { ...current.rules, [key]: event.target.checked },
                      }))
                    }
                  />
                  <span>
                    <strong>{RULE_LABELS[key].title}</strong>
                    <small>{RULE_LABELS[key].description}</small>
                  </span>
                </label>
              ))}
            </div>
          </details>

          <section aria-labelledby="playback-heading">
            <div className={styles.sectionHeading}>
              <span>03</span>
              <div>
                <p className="eyebrow">Choose the pace</p>
                <h2 id="playback-heading">Playback</h2>
              </div>
            </div>
            <div className={styles.playbackGrid}>
              <label className="field">
                <span>Speed</span>
                <select
                  className="select"
                  value={state.speed}
                  onChange={(event) =>
                    setState((current) => ({ ...current, speed: event.target.value as Speed }))
                  }
                >
                  {Object.keys(SPEED_DELAYS).map((speed) => (
                    <option key={speed} value={speed}>
                      {titleCase(speed)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Commentary</span>
                <select
                  className="select"
                  value={state.commentary}
                  onChange={(event) =>
                    setState((current) => ({
                      ...current,
                      commentary: event.target.value as CommentaryMode,
                    }))
                  }
                >
                  <option value="gameplay">Gameplay</option>
                  <option value="code">Code</option>
                  <option value="both">Both</option>
                  <option value="off">Off</option>
                </select>
              </label>
            </div>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={resolution.setup.autoplay}
                onChange={(event) =>
                  setState((current) => ({ ...current, autoplay: event.target.checked }))
                }
              />
              <span>Autoplay every seat, including human seats</span>
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={state.reducedMotion}
                onChange={(event) =>
                  setState((current) => ({ ...current, reducedMotion: event.target.checked }))
                }
              />
              <span>Reduce motion</span>
            </label>
          </section>

          {setupError ? (
            <p className="alert" role="alert">
              {setupError}
            </p>
          ) : null}
          <button
            className={`button buttonPrimary ${styles.start}`}
            type="submit"
            disabled={!urlReady || Boolean(setupError)}
          >
            Start match
          </button>
        </form>

        <aside className={styles.sidebar}>
          <section className={styles.summary} aria-labelledby="resolved-heading">
            <p className="eyebrow">Resolved setup</p>
            <h2 id="resolved-heading">
              <span data-testid="resolved-mode">{titleCase(resolution.setup.config.mode)}</span>{" "}
              table
            </h2>
            <dl>
              <div>
                <dt>Players</dt>
                <dd>{resolution.setup.config.player_count}</dd>
              </div>
              <div>
                <dt>Tokens each</dt>
                <dd>{resolution.setup.config.tokens_per_player}</dd>
              </div>
              <div>
                <dt>Route</dt>
                <dd>{resolution.setup.config.track_len} tiles</dd>
              </div>
              <div>
                <dt>Turn cap</dt>
                <dd>{resolution.setup.config.max_turns}</dd>
              </div>
              <div>
                <dt>Rule profile</dt>
                <dd>{titleCase(resolution.setup.config.profile)}</dd>
              </div>
              <div>
                <dt>Seed</dt>
                <dd>{resolution.setup.config.seed ?? "Random"}</dd>
              </div>
            </dl>
            <p className={styles.precedence}>Precedence: URL → imported JSON → wizard.</p>
          </section>
          <JsonConfigPanel
            value={jsonText}
            error={jsonError}
            onChange={setJsonText}
            onLoad={loadConfiguration}
          />
          <section className={styles.note}>
            <p className="eyebrow">What stays here</p>
            <h2>Private by default.</h2>
            <p>
              Your match and preferences stay in localStorage. There is no sign-in, analytics
              payload, database, or game server in v3.
            </p>
          </section>
        </aside>
      </div>

      <footer className={styles.footer}>
        <span>Python-verified rules · Browser-local play · Optional 3D view</span>
        <span>Online rooms are a documented future phase.</span>
      </footer>
    </main>
  );
}
