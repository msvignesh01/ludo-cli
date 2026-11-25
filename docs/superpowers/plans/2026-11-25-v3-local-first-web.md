# v3 Local-First Web Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a thoroughly tested, responsive, Python-parity Ludo web showcase in `web/`, deploy it to Vercel, and push reviewed source to `msvignesh01/ludo-cli`.

**Architecture:** A pure TypeScript rules core mirrors the verified Python engines. A React controller owns turns, timers, commentary, and versioned localStorage persistence. Three.js is presentation-only and a semantic DOM board provides complete fallback play. Vercel hosts the frontend now; Render is documented for a later server-authoritative online-room phase.

**Tech Stack:** Next.js App Router, React, TypeScript, Three.js, CSS Modules, Fontsource, Vitest, Playwright, axe-core, Python 3.11 oracle, Vercel.

**Spec:** `docs/superpowers/specs/2026-11-25-v3-local-first-web-design.md`

## Global Constraints

- Preserve `v1_initial/` as the verified behavioral source of truth; do not rewrite its rules for the web port.
- The browser core must not import React, Next.js, DOM, or Three.js APIs.
- Quick/Classic geometry is locked; movement and rendering derive every value from validated configuration.
- Seeded dice must match CPython 3.11 integer-seed MT19937 output, including negative and large integer seeds.
- Canonical snapshots and event payloads must match Python exactly; RNG internals stay outside canonical snapshots.
- `applyMove` owns post-move turn resolution exactly once; reaching home on a six resets the streak.
- Local play uses browser storage only; no database, account system, analytics payload, or deployed backend is added.
- Do not claim online multiplayer, human peer testing, or human visual GUI review that has not happened.
- Every interactive action must remain available through semantic DOM controls; WebGL is optional.
- No emojis. Use tech-stack badges and Mermaid diagrams where they improve documentation.
- Never commit credentials, `.env` files, caches, test artifacts, browser binaries, or generated `__pycache__` content.
- User authorized commits and a push to the existing `msvignesh01/ludo-cli` remote; do not force-push or rewrite history.

---

## Task 0: Freeze and Record the Verified Python Baseline

**Files:**
- Modify: `TRACKER.md`, `docs/04_ai_interaction_log.md`
- Stage: existing v1 source, tests, configs, and documentation only

**Interfaces:**
- Consumes: fresh `python scripts/verify_gates.py --stage v1` output
- Produces: a committed v1 source baseline and exact current evidence

- [ ] **Step 1: Record the fresh observed gate**

Replace prior final timing rows with the latest observed output while retaining the earlier home-on-six fix trace:

```text
Ran 86 tests in 0.126s
OK
Ran 13 tests in 296.485s
OK
Parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919
AST summary: 28 Python files, 10 OOP classes, 0 functional/shared classes
GATE PASSED: Stage 'v1' achieved 100% perfection!
Failures: 0 | Warnings: 0
```

- [ ] **Step 2: Review and stage source explicitly**

Run:

```bash
git status --short
git diff --check
git add PLAN.md README.md TRACKER.md docs configs scripts/verify_gates.py templates 'testing/*.py' 'testing/*.md' 'v1_initial/**/*.py' v1_initial/__init__.py
git status --short
```

Confirm no `.pyc`, `__pycache__`, `.env`, credential, or browser artifact is staged.

- [ ] **Step 3: Commit the verified baseline**

```bash
git commit -m "feat: complete verified multiplayer Ludo showcase"
```

- [ ] **Step 4: Verify the commit**

```bash
git show --stat --oneline HEAD
git diff --check
```

Expected: source/docs are committed, generated caches remain untracked or unstaged, and whitespace checks pass.

---

## Task 1: Scaffold the Web Project and Quality Gates

**Files:**
- Create: `web/package.json`, `web/package-lock.json`, `web/tsconfig.json`
- Create: `web/next.config.ts`, `web/vitest.config.ts`, `web/playwright.config.ts`
- Create: `web/eslint.config.mjs`, `web/.prettierrc.json`, `web/.gitignore`
- Create: `web/README.md`, `web/app/layout.tsx`, `web/app/page.tsx`, `web/app/globals.css`
- Create: `web/tests/smoke.test.ts`

**Interfaces:**
- Consumes: Node 24+, npm, approved spec
- Produces: scripts `dev`, `build`, `lint`, `typecheck`, `test`, `test:parity`, `test:e2e`, `test:a11y`

- [ ] **Step 1: Create the Next.js shell**

```bash
npm create next-app@latest web -- --typescript --eslint --app --src-dir --import-alias "@/*" --use-npm --no-tailwind
```

- [ ] **Step 2: Install pinned runtime and test dependencies**

```bash
cd web
npm install three @fontsource/manrope @fontsource/space-grotesk
npm install -D @types/three vitest @playwright/test @axe-core/playwright prettier
```

Record exact resolved versions in `package-lock.json`; do not use floating version ranges in documentation.

- [ ] **Step 3: Add strict TypeScript and test configuration**

`tsconfig.json` must enable:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

`vitest.config.ts` must include `tests/unit/**/*.test.ts` and `tests/parity/**/*.test.ts` with the Node environment. `playwright.config.ts` must start `npm run dev -- --hostname 127.0.0.1 --port 3100`, use `http://127.0.0.1:3100`, and define desktop and mobile projects.

- [ ] **Step 4: Write the first failing smoke test**

```ts
import { describe, expect, it } from "vitest";
import { PLAYER_SPECS } from "../src/game/presets";

describe("web scaffold", () => {
  it("exposes four labeled player seats", () => {
    expect(PLAYER_SPECS.map((spec) => spec.prefix)).toEqual(["R", "G", "Y", "B"]);
  });
});
```

- [ ] **Step 5: Run and observe the expected failure**

```bash
npm test
```

Expected: FAIL because `src/game/presets.ts` does not exist.

- [ ] **Step 6: Add the minimal preset export and verify green**

Create `src/game/presets.ts` with `PLAYER_SPECS` copied as data from `v1_initial/shared/contracts.py`, then run:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Expected: every command exits 0.

- [ ] **Step 7: Commit the scaffold**

```bash
git add web
git commit -m "feat: scaffold tested Next.js Ludo web app"
```

---

## Task 2: Implement Canonical Types Presets and Configuration

**Files:**
- Create: `web/src/game/types.ts`, `web/src/game/presets.ts`
- Create: `web/src/game/config.ts`, `web/src/game/events.ts`
- Test: `web/tests/unit/config.test.ts`, `web/tests/unit/events.test.ts`

**Interfaces:**
- Consumes: Python `PRESETS`, `PROFILE_RULES`, `MATCH_DEFAULTS`, `EVENT_TYPES`, `build_config`, `config_from_dict`, `merge_setup`
- Produces: `MatchConfig`, `CanonicalSnapshot`, `GameEvent`, `MovePreview`, `SetupInput`, `ResolvedSetup`, `buildConfig`, `configFromDict`, `resolveSetup`, `normalizePlayerNames`, `normalizePlayerKinds`, `makeEvent`

- [ ] **Step 1: Write failing configuration tests**

```ts
import { describe, expect, it } from "vitest";
import { buildConfig, configFromDict, resolveSetup } from "../src/game/config";

describe("configuration", () => {
  it("locks Quick geometry", () => {
    expect(() => buildConfig("quick", "showcase", 2, { track_len: 52 })).toThrow(
      "board geometry cannot be overridden",
    );
  });

  it("uses Showcase defaults", () => {
    const config = buildConfig("quick");
    expect(config.blockades).toBe("safe_pair");
    expect(config.kill_to_enter).toBe(true);
    expect(config.podium_mode).toBe(true);
  });

  it("applies URL overrides above JSON and wizard values", () => {
    const setup = resolveSetup({
      wizard: { mode: "quick", seed: 1 },
      json: { mode: "classic", seed: 2 },
      url: { seed: 42 },
    });
    expect(setup.config.mode).toBe("classic");
    expect(setup.config.seed).toBe(42);
  });

  it("imports the existing Classic preset", () => {
    const config = configFromDict({
      mode: "classic",
      profile: "classic",
      player_count: 2,
      tokens_per_player: 4,
      blockades: "none",
      kill_to_enter: false,
      podium_mode: false,
      max_turns: 250,
      seed: 42,
    });
    expect(config.home_finish).toBe(56);
    expect(config.start_indices_2p).toEqual([0, 26]);
  });
});
```

- [ ] **Step 2: Run and observe failure**

```bash
npm test -- tests/unit/config.test.ts
```

Expected: FAIL because `config.ts` is missing.

- [ ] **Step 3: Implement exact data contracts**

Define `Mode = "quick" | "classic"`, `Profile = "showcase" | "classic"`, `Blockades = "none" | "strict" | "safe_pair"`, `CommentaryMode = "gameplay" | "code" | "both" | "off"`, `PlayerKind = "human" | "bot"`, and `MatchStatus = "PLAYING" | "WON" | "DRAW" | "QUIT"`.

`MatchConfig` contains every Python config key, including `ui: "cli" | "gui"`, `auto_delay`, `commentary`, and `seed: number | null`. Match seeds must be safe integers; the RNG API separately accepts arbitrary integer `BigInt` values for the required negative and large-seed parity fixtures. Canonical player export contains `index`, `name`, `kind`, `color`, `start_index`, `captures_made`, and tokens with only `label` and `steps`. Internal players may additionally contain `color_hex`, `prefix`, and `token_idx`.

- [ ] **Step 4: Implement validation and precedence**

Port these Python behaviors exactly:

- reject boolean values where integers are required;
- reject unknown keys and locked-geometry overrides;
- require player count 2–4, token count 1–4, positive finite turn cap, finite non-negative delay, and safe integer match seeds when provided;
- trim names, fill blanks with `Player N`, and suffix duplicates;
- validate and pad seat kinds, defaulting to bot when autoplay is enabled;
- resolve `defaults < wizard < JSON < URL`;
- accept both existing JSON presets without modification;
- cap imported JSON at 64 KiB before parsing.

- [ ] **Step 5: Add event contract tests and implementation**

```ts
expect(makeEvent("GAME_STARTED", 0, null, { mode: "quick", profile: "showcase" })).toEqual({
  type: "GAME_STARTED",
  turn: 0,
  player: null,
  data: { mode: "quick", profile: "showcase" },
});
```

Implement all fourteen Python event names and reject unknown event types.

- [ ] **Step 6: Verify**

```bash
npm run lint
npm run typecheck
npm test
```

Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add web/src/game web/tests/unit/config.test.ts web/tests/unit/events.test.ts
git commit -m "feat: port canonical web game contracts"
```

---

## Task 3: Implement CPython-Compatible Seeded RNG

**Files:**
- Create: `web/src/game/rng.ts`
- Create: `web/scripts/export-python-fixtures.py`
- Create: `web/fixtures/rng.json`, `web/fixtures/manifest.json`
- Test: `web/tests/unit/rng.test.ts`

**Interfaces:**
- Consumes: Python `random.Random(seed).randint(1, 6)`
- Produces: `PythonRandom`, `createPythonRandom`, `serializeRandom`, `deserializeRandom`

- [ ] **Step 1: Generate Python RNG fixtures**

The exporter must use the repository root explicitly, import `random`, and write decimal seed strings plus 10,000 rolls for seeds `-1`, `0`, `1`, `42`, `2**32`, `2**64 + 7`, and twenty fixed assignment seeds. Record Python version, source revision, schema version, and SHA-256 of the fixture payload in `manifest.json`.

- [ ] **Step 2: Write the failing RNG parity test**

```ts
import { describe, expect, it } from "vitest";
import fixture from "../../fixtures/rng.json";
import { createPythonRandom } from "../src/game/rng";

describe("Python-compatible RNG", () => {
  it.each(fixture.seeds)("matches 10,000 rolls for $seed", ({ seed, rolls }) => {
    const random = createPythonRandom(BigInt(seed));
    const actual = Array.from({ length: 10_000 }, () => random.randint(1, 6));
    expect(actual).toEqual(rolls);
  });
});
```

- [ ] **Step 3: Run and observe failure**

```bash
npm test -- tests/unit/rng.test.ts
```

Expected: FAIL because `rng.ts` is missing.

- [ ] **Step 4: Implement MT19937 and Python seed semantics**

Implement:

1. absolute bigint seed converted to little-endian 32-bit key words;
2. `init_genrand(19650218)` and `init_by_array`;
3. MT state regeneration and tempering;
4. `nextUint32`;
5. Python `getrandbits(k)` using little-endian 32-bit words;
6. `_randbelow(n)` with `k = n.bit_length()` and rejection sampling;
7. `randint(1, 6)` through `_randbelow(6) + 1`.

Use `BigInt` only at seed/conversion boundaries; keep the hot roll path in 32-bit numbers.

- [ ] **Step 5: Implement persistence serialization**

`serializeRandom` returns `{ seed: string | null, index: number, words: number[] }`. `deserializeRandom` validates 624 words, unsigned 32-bit ranges, and index bounds before restoring. Canonical game export must never call it.

- [ ] **Step 6: Verify all seeds**

```bash
npm test -- tests/unit/rng.test.ts
npm run typecheck
```

Expected: all fixed seeds match 10,000 rolls exactly.

- [ ] **Step 7: Commit**

```bash
git add web/src/game/rng.ts web/scripts/export-python-fixtures.py web/fixtures/rng.json web/fixtures/manifest.json web/tests/unit/rng.test.ts
git commit -m "feat: match Python seeded dice in TypeScript"
```

---

## Task 4: Port Locked Geometry and View Models

**Files:**
- Create: `web/src/game/geometry.ts`, `web/src/game/view-model.ts`
- Create: `web/fixtures/geometry.json`
- Test: `web/tests/unit/geometry.test.ts`, `web/tests/unit/view-model.test.ts`

**Interfaces:**
- Consumes: Python `build_board_geometry`, `build_gui_view_model`
- Produces: `BoardGeometry`, `BoardMarker`, `BoardViewModel`, `buildBoardGeometry`, `buildGuiViewModel`

- [ ] **Step 1: Extend the Python exporter for geometry**

Write Quick and Classic geometry for 2P, 3P, and 4P, plus one view model containing base, track, home, and finished markers. Store the fixture hash in the manifest.

- [ ] **Step 2: Write failing geometry tests**

```ts
import { describe, expect, it } from "vitest";
import fixture from "../../fixtures/geometry.json";
import { buildConfig } from "../src/game/config";
import { buildBoardGeometry } from "../src/game/geometry";

describe("locked geometry", () => {
  it("matches the Python Classic 2P board", () => {
    const config = buildConfig("classic", "classic", 2);
    expect(buildBoardGeometry(config)).toEqual(fixture.classic2p);
  });
});
```

- [ ] **Step 3: Run and observe failure**

```bash
npm test -- tests/unit/geometry.test.ts
```

Expected: FAIL because `geometry.ts` is missing.

- [ ] **Step 4: Port the boundary-cycle algorithm**

Translate `_boundary_cycle` directly: build the three-cell-wide cross, identify orthogonal boundary neighbors, connect the two diagonal endpoints, then walk from `(0, center - 1)`. Derive `size = track_len / 4 + 2`; never hardcode 9, 15, 28, 52, 31, or 56 in engine or rendering code.

- [ ] **Step 5: Port home lanes yards and marker mapping**

Use the same four home-lane arrays and four yard boxes as Python. Seat quadrants derive from start indices. Map `steps == -1` to yard center, `steps == home_finish` to center, private-home steps to the player lane, and outer steps to `(start_index + steps) % track_len`.

- [ ] **Step 6: Add exact view-model assertions**

Assert marker order, `location`, `global_pos`, `cell`, `color_hex`, `prefix`, safe tiles, start tiles, status, and last event against the Python fixture. Assert stacked track markers retain distinct `player_index`/`token_idx` identities.

- [ ] **Step 7: Verify**

```bash
npm test -- tests/unit/geometry.test.ts tests/unit/view-model.test.ts
npm run typecheck
```

Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add web/src/game/geometry.ts web/src/game/view-model.ts web/fixtures/geometry.json web/tests/unit/geometry.test.ts web/tests/unit/view-model.test.ts
git commit -m "feat: port locked Ludo board geometry"
```

---

## Task 5: Implement the Pure Rules Core

**Files:**
- Create: `web/src/game/queries.ts`, `web/src/game/transitions.ts`, `web/src/game/engine.ts`
- Create: `web/src/game/stable-json.ts`
- Test: `web/tests/unit/rules.test.ts`

**Interfaces:**
- Consumes: canonical types, validated config, Python functional rules/state
- Produces: `InternalGame`, `createGame(config, names, seed?, kinds?)`, `rollDie`, `processRoll`, `previewMove`, `getValidMoves`, `recordBotDecision`, `applyMove`, `advanceTurn`, `declareMutualDraw`, `quitGame`, `exportCanonicalState`

- [ ] **Step 1: Write failing rule tests before implementation**

Port every intent from `testing/test_rules.py` and `testing/test_automation.py`. Include this exact regression:

```ts
it("resets the six streak when a token reaches home on a six", () => {
  const game = createGame(buildConfig("quick", "classic", 2), ["A", "B"], 42);
  processRoll(game, 6);
  applyMove(game, 0, 6);
  game.players[0]!.tokens[0]!.steps = 25;
  game.players[0]!.tokens[1]!.steps = 30;
  const result = processRoll(game, 6);
  expect(result.valid_moves).toEqual([0]);
  const move = applyMove(game, 0, 6);
  expect(move.reached_home).toBe(true);
  expect(move.bonus_turn).toBe(true);
  expect(game.consecutive_sixes).toBe(0);
  expect(game.current_player).toBe(0);
});
```

Also assert base unlock, circular wrap, private-home boundary, exact overshoot rejection, non-exact clamp, safe tile, disabled safe tiles, single/multi capture, friendly stack, strict intermediate blockade, safe-pair immunity, no-blockade stack capture, capture bonus non-stacking, triple-six forfeit, auto-skip, 2P victory, podium continuation, max-turn draw, mutual draw, and quit.

- [ ] **Step 2: Run and observe failure**

```bash
npm test -- tests/unit/rules.test.ts
```

Expected: FAIL because the engine modules are missing.

- [ ] **Step 3: Implement immutable canonical export around explicit mutable transitions**

`InternalGame` owns config, RNG, players, counters, status, finish order, last event, and events. Transition functions mutate only this internal object. UI code receives deep-cloned canonical snapshots and cannot mutate tokens.

- [ ] **Step 4: Implement queries exactly**

`computeTarget` must return `{ newSteps, wrapped, path }` or `null`. The Kill-to-Enter wrap uses `raw_target % (track_len - 1)` and includes every crossed outer step. `strictPathBlocked` checks every intermediate global tile for an opponent pair. `capturableTokens` excludes safe tiles and safe-pair stacks. `previewMove` returns the exact Python keys and reason strings.

- [ ] **Step 5: Implement roll and move transitions exactly**

`processRoll` emits `DICE_ROLLED`, increments/reset the six streak, voids the third six before movement, auto-skips empty legal lists, and advances once. `applyMove` validates the preview, moves once, emits movement/capture/blockade events, resets the streak on home, appends finish order, computes required finishers, grants at most one bonus, and advances only when it owns the resolution.

- [ ] **Step 6: Implement terminal transitions and canonical export**

Use exact reason strings `Maximum turn limit reached` and `Mutual agreement`. `GAME_QUIT` has empty data. Export the exact Python key set and clone config, finish order, events, players, and tokens. Do not export RNG, `token_idx`, `color_hex`, or `prefix`.

- [ ] **Step 7: Add stable JSON hashing**

```ts
export function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`).join(",")}}`;
}
```

Python fixtures use `json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` before SHA-256.

- [ ] **Step 8: Verify all rule tests**

```bash
npm run lint
npm run typecheck
npm test -- tests/unit/rules.test.ts
```

Expected: exit 0 with no weakened assertions.

- [ ] **Step 9: Commit**

```bash
git add web/src/game/queries.ts web/src/game/transitions.ts web/src/game/engine.ts web/src/game/stable-json.ts web/tests/unit/rules.test.ts
git commit -m "feat: port complete Ludo rules engine"
```

---

## Task 6: Implement Deterministic Bots and Commentary

**Files:**
- Create: `web/src/game/bot.ts`, `web/src/game/commentary.ts`
- Test: `web/tests/unit/bot.test.ts`, `web/tests/unit/commentary.test.ts`

**Interfaces:**
- Consumes: `previewMove`, `getValidMoves`, `GameEvent`
- Produces: `BotDecision`, `decisionDetails`, `chooseMove`, `gameplayMessage`, `codeMessage`, `formatCommentary`

- [ ] **Step 1: Write failing bot-priority tests**

Assert this exact score tuple and final tie-break:

```ts
const score = [
  Number(preview.reached_home),
  preview.captured.length,
  Number(config.kill_to_enter && player.captures_made === 0 && preview.captured.length > 0),
  Number(preview.safe),
  Number(tokenInDanger && !destinationCanBeCaptured),
  preview.new_steps + (preview.wrapped ? config.track_len : 0),
  -tokenIdx,
] as const;
```

Test Finish Home, Capture, Unlock, Safe tile, Escape danger, Advance furthest, lowest-index tie, empty legal list, and exact `BOT_DECISION` payload parity.

- [ ] **Step 2: Run and observe failure**

```bash
npm test -- tests/unit/bot.test.ts
```

Expected: FAIL because `bot.ts` is missing.

- [ ] **Step 3: Implement danger and scoring queries**

Use circular distance `(destination - opponentPosition) % track_len`; danger exists when distance is 1–6 and the tile is not safe. Return the same reason strings as Python: `No legal moves`, `Finish Home`, `Unlock Kill-to-Enter`, `Capture`, `Safe tile`, `Escape danger`, `Advance furthest`.

- [ ] **Step 4: Write failing commentary tests**

Port every event branch from `func_ludo/commentary.py`. Gameplay wording must match exactly. Code mode must name real web entry points, for example:

```text
Web: createGame(config, playerNames, seed)
Web: rollDie(game) -> processRoll(game, roll=3)
Web: applyMove(game, tokenIdx=0, roll=3)
Web: advanceTurn(game)
```

`both` emits `[Gameplay] ...` and `[Code] ...`; `off` emits no lines.

- [ ] **Step 5: Implement commentary and verify**

```bash
npm test -- tests/unit/bot.test.ts tests/unit/commentary.test.ts
npm run typecheck
```

Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add web/src/game/bot.ts web/src/game/commentary.ts web/tests/unit/bot.test.ts web/tests/unit/commentary.test.ts
git commit -m "feat: add deterministic web bots and commentary"
```

---

## Task 7: Generate and Replay the Full Python Oracle Matrix

**Files:**
- Modify: `web/scripts/export-python-fixtures.py`
- Create: `web/fixtures/games.jsonl`, `web/fixtures/rules.json`
- Create: `web/tests/parity/replay.test.ts`

**Interfaces:**
- Consumes: verified Python functional engine, OOP bot policy, web engine
- Produces: 1,080 versioned game action scripts with final snapshots, transition hashes, and measured totals

- [ ] **Step 1: Extend the exporter with compact game records**

Reuse the exact twelve `SCENARIOS` and seed rule `20_000 + game_number` from `testing/parity_test.py`. For every game, emit:

```json
{
  "schema": 1,
  "revision": "git-revision",
  "scenario": ["quick", 2, 2, "classic", "none", false, false, 120, 60],
  "seed": 20001,
  "config": {},
  "names": ["P1", "P2"],
  "kinds": ["bot", "bot"],
  "actions": [
    {"type": "roll", "roll": 6},
    {"type": "bot", "token_idx": 0, "reason": "Advance furthest"},
    {"type": "move", "token_idx": 0, "roll": 6}
  ],
  "transition_hash": "sha256",
  "final": {},
  "stats": {"rolls": 0, "moves": 0, "snapshots": 0}
}
```

Hash the initial snapshot and each snapshot after roll processing, bot decision, move, and final export, matching Python's 238,919 comparison boundaries.

- [ ] **Step 2: Add rule-level oracle fixtures**

Export focused examples for safe tiles, strict path blockade, safe-pair immunity, Kill-to-Enter wrap, exact/non-exact home, home-on-six reset, triple six, no-move skip, capture, bonus, podium, turn-cap draw, mutual draw, and quit. Each record contains setup mutations, action, expected preview/result, and expected canonical snapshot.

- [ ] **Step 3: Write the failing replay test**

```ts
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import {
  createGame,
  rollDie,
  processRoll,
  getValidMoves,
  recordBotDecision,
  applyMove,
  exportCanonicalState,
} from "../src/game/engine";
import { stableStringify } from "../src/game/stable-json";
import { decisionDetails } from "../src/game/bot";

const games = readFileSync(new URL("../../fixtures/games.jsonl", import.meta.url), "utf8")
  .trim().split("\n").map((line) => JSON.parse(line));

describe("Python oracle replay", () => {
  it("replays all 1,080 games with zero transition mismatches", () => {
    expect(games).toHaveLength(1080);
    for (const record of games) {
      const game = createGame(record.config, record.names, BigInt(record.seed), record.kinds);
      const hash = createHash("sha256");
      hash.update(stableStringify(exportCanonicalState(game)));
      for (const action of record.actions) {
        if (action.type === "roll") {
          expect(rollDie(game)).toBe(action.roll);
          processRoll(game, action.roll);
        } else if (action.type === "bot") {
          const validMoves = getValidMoves(game, game.current_player, action.roll);
          const decision = decisionDetails(game, game.current_player, action.roll, validMoves);
          expect(decision).toEqual({ token_idx: action.token_idx, reason: action.reason });
          recordBotDecision(game, action.token_idx, action.roll, action.reason);
        } else {
          applyMove(game, action.token_idx, action.roll);
        }
        hash.update(stableStringify(exportCanonicalState(game)));
      }
      expect(hash.digest("hex")).toBe(record.transition_hash);
      expect(exportCanonicalState(game)).toEqual(record.final);
    }
  });
});
```

- [ ] **Step 4: Run and inspect the first mismatch**

```bash
npm run test:parity
```

Expected before fixes: FAIL at the first divergent game/action. Fix the web engine root cause; never edit expected fixtures or weaken comparisons to pass.

- [ ] **Step 5: Iterate until the complete matrix passes**

Required printed totals:

```text
Web parity matrix: games=1080, wins=362, draws=718,
rolls=93403, moves=71678, snapshots=238919, mismatches=0
```

- [ ] **Step 6: Commit verified fixtures and replay harness**

```bash
git add web/scripts/export-python-fixtures.py web/fixtures web/tests/parity/replay.test.ts
git commit -m "test: prove full Python parity for web engine"
```

---

## Task 8: Implement Match Controller and Browser Persistence

**Files:**
- Create: `web/src/match/controller.ts`, `web/src/match/persistence.ts`, `web/src/match/MatchProvider.tsx`
- Test: `web/tests/unit/controller.test.ts`, `web/tests/unit/persistence.test.ts`

**Interfaces:**
- Consumes: engine, bot, commentary, RNG serialization
- Produces: `MatchController`, `SavedMatch`, `saveMatch`, `loadMatch`, `clearMatch`, `MatchProvider`, `useMatch`

- [ ] **Step 1: Write failing controller tests**

Use fake timers only in React scheduling tests; test the headless controller directly. Assert:

- human turn waits for Roll;
- legal roll exposes only valid token choices;
- bot turn performs one deterministic roll/decision/move;
- autoplay drives human seats without changing `kind`;
- pause blocks scheduling but Step still works;
- speed changes only delay;
- terminal state disables all turn controls;
- draw and quit emit clean terminal events;
- commentary switching does not change canonical state.

- [ ] **Step 2: Run and observe failure**

```bash
npm test -- tests/unit/controller.test.ts
```

Expected: FAIL because the controller is missing.

- [ ] **Step 3: Implement the headless controller**

`MatchController` owns `game`, `pendingRoll`, `validMoves`, `previews`, `paused`, `autoplay`, `speed`, `commentaryMode`, and `eventCursor`. Implement `rollHuman`, `selectMove`, `runAutomatedTurn`, `step`, `setPaused`, `setSpeed`, `setCommentary`, `cycleCommentary`, `declareDraw`, `quit`, `getSnapshot`, `getPendingRoll`, `getValidMoves`, `getPreviews`, `getScheduleDelayMs`, and `drainCommentary`.

`runAutomatedTurn` returns false when paused, terminal, human-controlled without autoplay, or awaiting a choice. Otherwise it rolls, records the bot decision, and applies the move exactly once.

- [ ] **Step 4: Write failing persistence tests**

```ts
const saved = saveMatch(controller);
const restored = MatchController.restore(saved);
expect(restored.getSnapshot()).toEqual(controller.getSnapshot());
expect(restored.getPendingRoll()).toBe(controller.getPendingRoll());
```

Also assert schema mismatch, invalid RNG words, malformed config, oversized payload, and corrupt JSON return a typed invalid-save result without throwing.

- [ ] **Step 5: Implement versioned persistence**

Use key `ludo-showcase:match:v1`. Save schema version, timestamp, config, names/kinds through canonical players, canonical snapshot, RNG state, pending roll/choices, and UI preferences. Validate before use. Do not store credentials or send data externally. Import/export uses the same validated record and a 64 KiB limit.

- [ ] **Step 6: Implement the React provider**

`MatchProvider` owns one controller, subscribes React consumers to controller revisions, persists after each revision, and schedules automated turns with `setTimeout`. Clear timers on pause, unmount, terminal state, and controller replacement.

- [ ] **Step 7: Verify**

```bash
npm test -- tests/unit/controller.test.ts tests/unit/persistence.test.ts
npm run typecheck
```

Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add web/src/match web/tests/unit/controller.test.ts web/tests/unit/persistence.test.ts
git commit -m "feat: add web match controller and recovery"
```

---

## Task 9: Build the Responsive Interface and Three.js Board

**Files:**
- Create: `web/app/layout.tsx`, `web/app/page.tsx`, `web/app/globals.css`, `web/app/error.tsx`
- Create: `web/components/setup/SetupWizard.tsx`, `web/components/setup/JsonConfigPanel.tsx`
- Create: `web/components/game/MatchHud.tsx`, `web/components/game/TokenChoiceList.tsx`
- Create: `web/components/game/CommentaryPanel.tsx`, `web/components/game/PlaybackControls.tsx`
- Create: `web/components/game/DrawDialog.tsx`, `web/components/game/QuitDialog.tsx`, `web/components/game/ResultPanel.tsx`
- Create: `web/components/board/DomBoard.tsx`, `web/components/board/BoardCanvas.tsx`
- Test: `web/tests/e2e/local-match.spec.ts`

**Interfaces:**
- Consumes: `MatchProvider`, canonical snapshot, previews, board view model
- Produces: complete setup, match, result, resume, export, and fallback flows

- [ ] **Step 1: Implement the visual system**

Import self-hosted Manrope and Space Grotesk in `layout.tsx`. Define CSS variables for ink `#0B1020`, ivory `#F7F3EA`, gold `#D4A24C`, and the four Python player colors. Use CSS Modules for components, visible focus rings, 44×44 minimum targets, responsive desktop/tablet/mobile layouts, and `prefers-reduced-motion`.

- [ ] **Step 2: Implement setup and resume**

`SetupWizard` controls mode, profile, player count, token count, names, human/bot seats, all seven boolean rule toggles, blockade mode, exact home, turn cap, seed, autoplay, speed, and commentary. `JsonConfigPanel` accepts drag/drop or file selection, caps size at 64 KiB, displays field errors, and imports existing presets. URL values override JSON, JSON overrides wizard, and wizard overrides defaults.

If a valid save exists, show `Resume match` and `Start new match`; if invalid, explain the problem and offer `Reset saved data`.

- [ ] **Step 3: Implement match HUD and accessible controls**

`MatchHud` shows current player, turn count, status, captures, finished tokens, rule summary, last event, and finish order. `TokenChoiceList` renders one button per legal preview with token label, destination, capture names, safe status, wrap, home, and blockade facts. `PlaybackControls` provides Roll, Pause/Resume, Step, speed, autoplay, commentary, draw, quit, export, and Reset View. Terminal controls are disabled.

- [ ] **Step 4: Implement draw and quit confirmation**

Use native `<dialog>` with focus restoration. Mutual draw asks every seat in order in local hot-seat play; a decline resumes the same turn without advancing. Quit requires confirmation and ends with `GAME_QUIT`.

- [ ] **Step 5: Implement the semantic DOM board**

`DomBoard` renders route cells, home lanes, yards, center, safe markers, and all player tokens from `buildGuiViewModel`. It uses semantic headings/status text and visible labels. It must remain complete when the canvas is absent.

- [ ] **Step 6: Implement the Three.js presentation**

`BoardCanvas` creates one reusable cell mesh system and one token group per marker. Map grid coordinates to an orthographic top-down scene. Use distinct token shapes per player, deterministic stack offsets, current-player and legal-destination highlights, and Reset View. Render only when the snapshot changes; do not run a perpetual decorative animation. Catch WebGL creation/context failures and set `webglAvailable=false` so `DomBoard` remains visible.

- [ ] **Step 7: Write failing desktop/mobile E2E tests**

```ts
test("keyboard user can roll and choose a legal token", async ({ page }) => {
  await page.goto("/?mode=quick&profile=classic&players=2&tokens=1&seed=42&max_turns=120");
  await page.getByRole("button", { name: "Start match" }).click();
  const roll = page.getByRole("button", { name: "Roll" });
  await roll.focus();
  await page.keyboard.press("Enter");
  const choice = page.getByRole("button", { name: /Move R1/ });
  await expect(choice).toBeVisible();
  await choice.focus();
  await page.keyboard.press("Enter");
  await expect(choice).toHaveCount(0);
  await expect(roll).toBeEnabled();
});
```

Add tests for four-bot autoplay to terminal, pause/step, commentary, draw decline/accept, quit confirmation, JSON import, URL override, localStorage resume, corrupt save, result actions, mobile overflow, and WebGL fallback.

- [ ] **Step 8: Run E2E and inspect real screenshots**

```bash
npx playwright install chromium
npm run test:e2e
```

Open the dev server in a browser, inspect desktop and mobile screenshots, exercise keyboard and pointer paths, and fix visual or interaction defects. Do not claim visual success from unit tests alone.

- [ ] **Step 9: Commit**

```bash
git add web/app web/components web/tests/e2e/local-match.spec.ts
git commit -m "feat: build responsive Ludo web interface"
```

---

## Task 10: Accessibility Hardening Documentation and Release

**Files:**
- Create: `web/tests/e2e/accessibility.spec.ts`
- Create: `docs/07_web_architecture.md`, `docs/08_web_user_flow.md`, `docs/09_deployment.md`
- Modify: `README.md`, `PLAN.md`, `TRACKER.md`, `docs/04_ai_interaction_log.md`, `docs/06_v3_web_build_plan.md`
- Create: `web/README.md`

**Interfaces:**
- Consumes: completed app and measured verification output
- Produces: badges, Mermaid diagrams, deployment guide, release evidence, Vercel URL if deployment succeeds

- [ ] **Step 1: Add automated accessibility tests**

```ts
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("setup and match have no critical or serious violations", async ({ page }) => {
  await page.goto("/");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole("button", { name: "Start match" }).click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
```

Also assert keyboard focus visibility, heading order, form labels, live regions, 44×44 targets, no color-only token distinction, reduced motion, and mobile reflow.

- [ ] **Step 2: Run the complete release gate**

```bash
npm run lint
npm run typecheck
npm test
npm run test:parity
npm run test:e2e
npm run test:a11y
npm run build
python scripts/verify_gates.py --stage v1
git diff --check
```

Expected: every command exits 0; web parity prints zero mismatches; Python v1 remains unchanged and passing.

- [ ] **Step 3: Update documentation with measured evidence only**

Add Next.js, TypeScript, React, Three.js, Vitest, Playwright, and Vercel badges. Add Mermaid architecture, user flow, state, automation, persistence, and future Render sequence diagrams. Record exact versions, commands, test counts, parity totals, browser viewports, accessibility result, and deployment status. Update `docs/06_v3_web_build_plan.md` from future-plan status to the implemented local-first release with online rooms explicitly deferred.

- [ ] **Step 4: Validate documentation**

Run a local-link/code-fence/unfinished-marker scan across current docs. Peer templates and intentionally blank future fields are excluded. `git diff --check` must pass.

- [ ] **Step 5: Review and commit all release source**

```bash
git status --short
git diff --stat
git add README.md PLAN.md TRACKER.md docs 'web/**/*.py' 'web/**/*.ts' 'web/**/*.tsx' 'web/**/*.css' 'web/**/*.json' 'web/**/*.md' web/package-lock.json web/.gitignore web/.prettierrc.json
git status --short
git commit -m "feat: release local-first Ludo web showcase"
```

Inspect staged paths and exclude every cache, `.env`, credential, screenshot artifact, `test-results`, `playwright-report`, `node_modules`, and generated binary.

- [ ] **Step 6: Push the reviewed release**

```bash
git push origin main
```

Do not force-push. Verify the remote commit with `git ls-remote origin refs/heads/main`.

- [ ] **Step 7: Deploy to Vercel**

```bash
npx vercel whoami
npx vercel link --project ludo-web --yes
npx vercel deploy --prod
```

Run the Vercel command from `web/` or configure `web/` as the project root. If authentication is absent, do not invent credentials or claim deployment; report the exact blocker and leave the project ready for `npx vercel deploy --prod`.

- [ ] **Step 8: Smoke-test production and record the result**

Open the returned production URL, run setup, seeded autoplay, keyboard roll/choice, mobile layout, localStorage reload, and WebGL fallback. Record the URL and observed results only after they succeed.

---

## Self-Review Coverage Map

| Spec requirement | Plan task |
|---|---|
| Frozen Python baseline and fresh evidence | Task 0 |
| Next.js scaffold and quality scripts | Task 1 |
| Canonical contracts and precedence | Task 2 |
| CPython-compatible deterministic dice | Task 3 |
| Locked Quick/Classic geometry | Task 4 |
| All rules events and terminal states | Task 5 |
| Deterministic bots and commentary | Task 6 |
| Full 1,080-game Python parity | Task 7 |
| Pause/step/speed/autoplay and persistence | Task 8 |
| Responsive DOM and Three.js interface | Task 9 |
| Accessibility docs badges diagrams release | Task 10 |
| Vercel hosting and GitHub push | Task 10 |
| Future Render online-room design | Spec Section 13 and `docs/09_deployment.md`; no backend deployment |

## Type and Interface Consistency Check

- `MatchConfig`, `CanonicalSnapshot`, `GameEvent`, `MovePreview`, `InternalGame`, `BoardGeometry`, `BoardMarker`, `BotDecision`, `SavedMatch`, and `MatchController` are defined once in the listed type/controller modules.
- Engine functions use `playerIdx`/`tokenIdx` in TypeScript while canonical event payload keys remain Python's `player_idx`/`token_idx`.
- Controller actions dispatch engine transitions and never call `advanceTurn` after `applyMove`.
- Fixture hashes use `stableStringify`, never ordinary object insertion order.
- Rendering consumes `buildGuiViewModel(snapshot)` and never calculates movement rules.
- Persistence stores RNG state separately from canonical snapshots.
- Browser UI always uses the web implementation; imported Python `ui: "cli"` values remain canonical data only.
