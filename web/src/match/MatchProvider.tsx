"use client";

import { createContext, useContext, useEffect, useMemo, useSyncExternalStore } from "react";
import type { ReactNode } from "react";
import type { MatchController } from "./controller";
import { saveMatch } from "./persistence";

export interface MatchContextValue {
  controller: MatchController;
  revision: number;
}

const MatchContext = createContext<MatchContextValue | null>(null);

export function MatchProvider({
  controller,
  children,
}: {
  controller: MatchController;
  children?: ReactNode;
}) {
  const revision = useSyncExternalStore(
    controller.subscribe,
    controller.getRevision,
    controller.getRevision,
  );
  const value = useMemo(() => ({ controller, revision }), [controller, revision]);

  useEffect(() => {
    saveMatch(controller);
  }, [controller, revision]);

  useEffect(() => {
    const snapshot = controller.getSnapshot();
    const currentPlayer = snapshot.players[snapshot.current_player];
    if (
      controller.isPaused() ||
      snapshot.status !== "PLAYING" ||
      controller.getPendingRoll() !== null ||
      !currentPlayer ||
      (currentPlayer.kind !== "bot" && !controller.getAutoplay())
    ) {
      return;
    }
    const timer = setTimeout(() => controller.runAutomatedTurn(), controller.getScheduleDelayMs());
    return () => clearTimeout(timer);
  }, [controller, revision]);

  return <MatchContext.Provider value={value}>{children}</MatchContext.Provider>;
}

export function useMatch(): MatchContextValue {
  const value = useContext(MatchContext);
  if (!value) throw new Error("useMatch must be used inside MatchProvider");
  return value;
}
