"use client";

import { useEffect, useState } from "react";
import { SPEED_DELAYS } from "../game/presets";
import type { ResolvedSetup, Speed } from "../game/types";
import { MatchController } from "../match/controller";
import { MatchProvider } from "../match/MatchProvider";
import { clearMatch, loadMatch } from "../match/persistence";
import type { LoadMatchResult, SavedMatch } from "../match/persistence";
import { MatchScreen } from "./match/MatchScreen";
import { SetupWizard } from "./setup/SetupWizard";

function speedForDelay(delay: number): Speed {
  const match = Object.entries(SPEED_DELAYS).find(([, value]) => value === delay);
  return (match?.[0] as Speed | undefined) ?? "normal";
}

export function LudoApp() {
  const [controller, setController] = useState<MatchController | null>(null);
  const [savedMatch, setSavedMatch] = useState<LoadMatchResult | null>(null);

  useEffect(() => {
    let active = true;
    queueMicrotask(() => {
      if (active) setSavedMatch(loadMatch());
    });
    return () => {
      active = false;
    };
  }, []);

  function startMatch(setup: ResolvedSetup, reducedMotion: boolean): void {
    clearMatch();
    setController(
      new MatchController(
        setup.config,
        setup.names,
        setup.config.seed === null ? null : BigInt(setup.config.seed),
        setup.kinds,
        {
          autoplay: setup.autoplay,
          speed: speedForDelay(setup.config.auto_delay),
          commentary: setup.config.commentary,
          reducedMotion,
        },
      ),
    );
  }

  function resumeMatch(match: SavedMatch): void {
    setController(MatchController.restore(match));
  }

  function resetSaved(): void {
    clearMatch();
    setSavedMatch({ status: "empty" });
  }

  function newMatch(): void {
    resetSaved();
    setController(null);
  }

  if (controller) {
    return (
      <MatchProvider controller={controller}>
        <MatchScreen controller={controller} onNewMatch={newMatch} />
      </MatchProvider>
    );
  }

  return (
    <SetupWizard
      savedMatch={savedMatch}
      onStart={startMatch}
      onResume={resumeMatch}
      onResetSaved={resetSaved}
    />
  );
}
