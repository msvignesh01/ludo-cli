export interface PlayerSpec {
  color: "RED" | "GREEN" | "YELLOW" | "BLUE";
  hex: string;
  prefix: string;
}

export const PLAYER_SPECS: readonly PlayerSpec[] = [
  { color: "RED", hex: "#EF4444", prefix: "R" },
  { color: "GREEN", hex: "#22C55E", prefix: "G" },
  { color: "YELLOW", hex: "#EAB308", prefix: "Y" },
  { color: "BLUE", hex: "#3B82F6", prefix: "B" },
];
