import type { MatchConfig } from "./types";

export type Cell = [number, number];
export type YardBox = [number, number, number, number];

export interface BoardGeometry {
  size: number;
  center: number;
  track_cells: Cell[];
  home_cells: Cell[][];
  yard_boxes: YardBox[];
  home_center: Cell;
}

function cellKey(cell: Cell): string {
  return `${cell[0]},${cell[1]}`;
}

function boundaryCycle(size: number, center: number): Cell[] {
  const cross = new Set<string>();
  for (let x = 0; x < size; x += 1) {
    for (let y = 0; y < size; y += 1) {
      if (center - 1 <= x && x <= center + 1) {
        cross.add(`${x},${y}`);
      } else if (center - 1 <= y && y <= center + 1) {
        cross.add(`${x},${y}`);
      }
    }
  }

  const orthogonal: Cell[] = [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
  ];
  const boundary: Cell[] = [];
  for (let x = 0; x < size; x += 1) {
    for (let y = 0; y < size; y += 1) {
      const cell: Cell = [x, y];
      const inside = cross.has(cellKey(cell));
      const exposed = orthogonal.some(([dx, dy]) => !cross.has(`${x + dx},${y + dy}`));
      if (inside && exposed) {
        boundary.push(cell);
      }
    }
  }

  const boundaryKeys = new Set(boundary.map(cellKey));
  const links = new Map<string, Cell[]>();
  for (const cell of boundary) {
    links.set(
      cellKey(cell),
      orthogonal
        .map(([dx, dy]): Cell => [cell[0] + dx, cell[1] + dy])
        .filter((neighbor) => boundaryKeys.has(cellKey(neighbor))),
    );
  }

  const endpoints = boundary.filter((cell) => links.get(cellKey(cell))!.length === 1);
  for (const cell of endpoints) {
    const diagonal = endpoints.filter(
      (other) =>
        other !== cell && Math.abs(other[0] - cell[0]) === 1 && Math.abs(other[1] - cell[1]) === 1,
    );
    if (diagonal.length === 1) {
      const neighbor = diagonal[0]!;
      links.get(cellKey(cell))!.push(neighbor);
      links.get(cellKey(neighbor))!.push(cell);
    }
  }

  const start: Cell = [0, center - 1];
  const cycle: Cell[] = [[...start]];
  const visited = new Set([cellKey(start)]);
  let previous = start;
  let current: Cell = [1, center - 1];
  while (cellKey(current) !== cellKey(start)) {
    cycle.push([...current]);
    visited.add(cellKey(current));
    const candidates = links
      .get(cellKey(current))!
      .filter((cell) => cellKey(cell) !== cellKey(previous) && !visited.has(cellKey(cell)));
    if (candidates.length === 0) {
      break;
    }
    previous = current;
    current = candidates[0]!;
  }
  return cycle;
}

export function buildBoardGeometry(config: MatchConfig): BoardGeometry {
  const quadrants = config.track_len / 4;
  const size = quadrants + 2;
  const center = Math.floor(size / 2);
  const homeLength = config.home_len;
  const allHomeCells: Cell[][] = [
    Array.from({ length: homeLength }, (_, index): Cell => [index + 1, center]),
    Array.from({ length: homeLength }, (_, index): Cell => [center, index + 1]),
    Array.from({ length: homeLength }, (_, index): Cell => [size - 2 - index, center]),
    Array.from({ length: homeLength }, (_, index): Cell => [center, size - 2 - index]),
  ];
  const corner = center - 1;
  const rightStart = center + 2;
  const allYardBoxes: YardBox[] = [
    [0, 0, corner - 1, corner - 1],
    [rightStart, 0, size - 1, corner - 1],
    [rightStart, rightStart, size - 1, size - 1],
    [0, rightStart, corner - 1, size - 1],
  ];
  const startKey = config.player_count === 2 ? "start_indices_2p" : "start_indices_4p";
  const starts = config[startKey].slice(0, config.player_count);
  const seatQuadrants = starts.map(
    (start) => ((start * allYardBoxes.length) / config.track_len) % allYardBoxes.length,
  );
  return {
    size,
    center,
    track_cells: boundaryCycle(size, center),
    home_cells: seatQuadrants.map((quadrant) => allHomeCells[quadrant]!.map((cell) => [...cell])),
    yard_boxes: seatQuadrants.map((quadrant) => [...allYardBoxes[quadrant]!]),
    home_center: [center, center],
  };
}
