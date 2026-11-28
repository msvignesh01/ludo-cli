"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { buildGuiViewModel } from "../../game/view-model";
import type { CanonicalSnapshot, LegalMovePreview } from "../../game/types";
import type { BoardGeometry, Cell } from "../../game/geometry";
import { PLAYER_SPECS } from "../../game/presets";
import styles from "./BoardCanvas.module.css";

interface SceneHandle {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.OrthographicCamera;
  boardGroup: THREE.Group;
  tokenGroup: THREE.Group;
  highlightGroup: THREE.Group;
  geometryKey: string;
  size: number;
  observer: ResizeObserver;
}

function disposeGroup(group: THREE.Group): void {
  for (const child of [...group.children]) {
    group.remove(child);
    child.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose();
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach((material) => material.dispose());
      }
    });
  }
}

function worldCell(cell: Cell, size: number): [number, number] {
  return [cell[0] - (size - 1) / 2, (size - 1) / 2 - cell[1]];
}

function targetCell(
  preview: LegalMovePreview,
  geometry: BoardGeometry,
  snapshot: CanonicalSnapshot,
): Cell {
  if (preview.global_pos !== null) return geometry.track_cells[preview.global_pos]!;
  if (preview.reached_home) return geometry.home_center;
  const laneIndex = preview.new_steps - (snapshot.config.track_len - 1);
  return geometry.home_cells[snapshot.current_player]![laneIndex] ?? geometry.home_center;
}

function tokenGeometry(playerIndex: number): THREE.BufferGeometry {
  switch (playerIndex) {
    case 0:
      return new THREE.SphereGeometry(0.23, 18, 12);
    case 1:
      return new THREE.BoxGeometry(0.38, 0.38, 0.28);
    case 2:
      return new THREE.ConeGeometry(0.27, 0.46, 4);
    default:
      return new THREE.TorusGeometry(0.19, 0.085, 10, 20);
  }
}

function buildCellSystem(
  handle: SceneHandle,
  geometry: BoardGeometry,
  snapshot: CanonicalSnapshot,
): void {
  disposeGroup(handle.boardGroup);
  const { scene, size } = handle;

  const border = new THREE.Mesh(
    new THREE.BoxGeometry(size + 0.35, size + 0.35, 0.18),
    new THREE.MeshStandardMaterial({ color: "#0b1020", roughness: 0.85 }),
  );
  border.position.z = -0.22;
  handle.boardGroup.add(border);

  const surface = new THREE.Mesh(
    new THREE.PlaneGeometry(size, size),
    new THREE.MeshStandardMaterial({ color: "#fffdf8", roughness: 0.95 }),
  );
  surface.position.z = -0.1;
  handle.boardGroup.add(surface);

  const trackMaterial = new THREE.MeshStandardMaterial({ color: "#ffffff", roughness: 0.9 });
  const track = new THREE.InstancedMesh(
    new THREE.BoxGeometry(0.92, 0.92, 0.09),
    trackMaterial,
    geometry.track_cells.length,
  );
  const dummy = new THREE.Object3D();
  const safeTiles = new Set(snapshot.config.safe_tiles_enabled ? snapshot.config.safe_tiles : []);
  const startOwners = new Map<number, number>();
  snapshot.players.forEach((player) => startOwners.set(player.start_index, player.index));
  geometry.track_cells.forEach((cell, index) => {
    const [x, y] = worldCell(cell, size);
    dummy.position.set(x, y, 0);
    dummy.updateMatrix();
    track.setMatrixAt(index, dummy.matrix);
    const owner = startOwners.get(index);
    const color =
      owner === undefined
        ? safeTiles.has(index)
          ? new THREE.Color("#ead7ad")
          : new THREE.Color("#fffdf8")
        : new THREE.Color(PLAYER_SPECS[owner]!.hex);
    track.setColorAt(index, color);
  });
  track.instanceMatrix.needsUpdate = true;
  if (track.instanceColor) track.instanceColor.needsUpdate = true;
  handle.boardGroup.add(track);

  geometry.home_cells.forEach((lane, playerIndex) => {
    const color = new THREE.Color(PLAYER_SPECS[playerIndex]!.hex).lerp(
      new THREE.Color("#fffdf8"),
      0.68,
    );
    const home = new THREE.InstancedMesh(
      new THREE.BoxGeometry(0.92, 0.92, 0.09),
      new THREE.MeshStandardMaterial({ color, roughness: 0.9 }),
      lane.length,
    );
    lane.forEach((cell, index) => {
      const [x, y] = worldCell(cell, size);
      dummy.position.set(x, y, 0.01);
      dummy.updateMatrix();
      home.setMatrixAt(index, dummy.matrix);
    });
    home.instanceMatrix.needsUpdate = true;
    handle.boardGroup.add(home);
  });

  geometry.yard_boxes.forEach((box, playerIndex) => {
    const width = box[2] - box[0] + 1;
    const height = box[3] - box[1] + 1;
    const color = new THREE.Color(PLAYER_SPECS[playerIndex]!.hex).lerp(
      new THREE.Color("#fffdf8"),
      0.84,
    );
    const yard = new THREE.Mesh(
      new THREE.BoxGeometry(width * 0.9, height * 0.9, 0.08),
      new THREE.MeshStandardMaterial({ color, roughness: 0.95 }),
    );
    const [x, y] = worldCell([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2], size);
    yard.position.set(x, y, 0.02);
    handle.boardGroup.add(yard);
  });

  const homeCenter = new THREE.Mesh(
    new THREE.BoxGeometry(0.94, 0.94, 0.12),
    new THREE.MeshStandardMaterial({ color: "#d4a24c", roughness: 0.75 }),
  );
  homeCenter.position.set(0, 0, 0.06);
  handle.boardGroup.add(homeCenter);

  scene.add(handle.boardGroup);
}

function buildTokens(handle: SceneHandle, snapshot: CanonicalSnapshot): void {
  disposeGroup(handle.tokenGroup);
  const view = buildGuiViewModel(snapshot);
  const stacks = new Map<string, typeof view.markers>();
  for (const marker of view.markers) {
    const key = marker.cell.join(",");
    const stack = stacks.get(key) ?? [];
    stack.push(marker);
    stacks.set(key, stack);
  }
  for (const stack of stacks.values()) {
    stack.forEach((marker, stackIndex) => {
      const group = new THREE.Group();
      const mesh = new THREE.Mesh(
        tokenGeometry(marker.player_index),
        new THREE.MeshStandardMaterial({
          color: marker.color_hex,
          roughness: 0.45,
          metalness: 0.05,
        }),
      );
      mesh.position.z = 0.24;
      group.add(mesh);
      const [x, y] = worldCell(marker.cell, handle.size);
      const offset = (stackIndex - (stack.length - 1) / 2) * 0.17;
      group.position.set(x + offset, y + offset, 0);
      handle.tokenGroup.add(group);
    });
  }
}

function buildHighlights(
  handle: SceneHandle,
  snapshot: CanonicalSnapshot,
  previews: LegalMovePreview[],
): void {
  disposeGroup(handle.highlightGroup);
  const view = buildGuiViewModel(snapshot);
  const cells: Cell[] = previews.map((preview) => targetCell(preview, view.geometry, snapshot));
  const currentStart =
    view.geometry.track_cells[snapshot.players[snapshot.current_player]!.start_index]!;
  cells.push(currentStart);
  for (const cell of cells) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(0.28, 0.37, 28),
      new THREE.MeshBasicMaterial({ color: "#d4a24c", side: THREE.DoubleSide }),
    );
    const [x, y] = worldCell(cell, handle.size);
    ring.position.set(x, y, 0.2);
    handle.highlightGroup.add(ring);
  }
}

export function BoardCanvas({
  snapshot,
  previews,
  resetSignal,
  onAvailability,
}: {
  snapshot: CanonicalSnapshot;
  previews: LegalMovePreview[];
  resetSignal: number;
  onAvailability: (available: boolean) => void;
}) {
  const mount = useRef<HTMLDivElement>(null);
  const handle = useRef<SceneHandle | null>(null);
  const reportedAvailable = useRef(false);

  useEffect(() => {
    const element = mount.current;
    if (!element) return;
    const container = element;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      onAvailability(false);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.domElement.setAttribute("aria-hidden", "true");
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-8, 8, 8, -8, 0.1, 100);
    camera.position.set(0, 0, 30);
    camera.lookAt(0, 0, 0);
    scene.add(new THREE.AmbientLight("#ffffff", 2.1));
    const light = new THREE.DirectionalLight("#ffffff", 2.4);
    light.position.set(-6, 9, 14);
    scene.add(light);

    const boardGroup = new THREE.Group();
    const tokenGroup = new THREE.Group();
    const highlightGroup = new THREE.Group();
    scene.add(tokenGroup, highlightGroup);

    function resize(): void {
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (width === 0 || height === 0) return;
      const current = handle.current;
      if (!current) return;
      renderer.setSize(width, height, false);
      const half = current.size * 0.57;
      const aspect = width / height;
      camera.left = -half * aspect;
      camera.right = half * aspect;
      camera.top = half;
      camera.bottom = -half;
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
    }

    const observer = new ResizeObserver(resize);
    observer.observe(container);
    const sceneHandle: SceneHandle = {
      renderer,
      scene,
      camera,
      boardGroup,
      tokenGroup,
      highlightGroup,
      geometryKey: "",
      size: 9,
      observer,
    };
    handle.current = sceneHandle;
    const contextLost = (event: Event): void => {
      event.preventDefault();
      reportedAvailable.current = false;
      onAvailability(false);
    };
    const contextRestored = (): void => {
      if (reportedAvailable.current) return;
      reportedAvailable.current = true;
      onAvailability(true);
    };
    renderer.domElement.addEventListener("webglcontextlost", contextLost);
    renderer.domElement.addEventListener("webglcontextrestored", contextRestored);

    return () => {
      observer.disconnect();
      renderer.domElement.removeEventListener("webglcontextlost", contextLost);
      renderer.domElement.removeEventListener("webglcontextrestored", contextRestored);
      disposeGroup(boardGroup);
      disposeGroup(tokenGroup);
      disposeGroup(highlightGroup);
      renderer.dispose();
      renderer.domElement.remove();
      handle.current = null;
      reportedAvailable.current = false;
    };
  }, [onAvailability]);

  useEffect(() => {
    const current = handle.current;
    if (!current) return;
    const geometry = buildGuiViewModel(snapshot).geometry;
    const geometryKey = `${snapshot.config.mode}:${snapshot.config.player_count}:${geometry.size}`;
    const geometryChanged = current.geometryKey !== geometryKey || current.size !== geometry.size;
    current.geometryKey = geometryKey;
    current.size = geometry.size;
    if (geometryChanged) buildCellSystem(current, geometry, snapshot);
    buildTokens(current, snapshot);
    buildHighlights(current, snapshot, previews);
    const width = mount.current?.clientWidth ?? 0;
    const height = mount.current?.clientHeight ?? 0;
    if (width > 0 && height > 0) {
      current.renderer.setSize(width, height, false);
      const half = geometry.size * 0.57;
      const aspect = width / height;
      current.camera.left = -half * aspect;
      current.camera.right = half * aspect;
      current.camera.top = half;
      current.camera.bottom = -half;
      current.camera.updateProjectionMatrix();
    }
    current.renderer.render(current.scene, current.camera);
    if (!reportedAvailable.current) {
      reportedAvailable.current = true;
      onAvailability(true);
    }
  }, [snapshot, previews, onAvailability]);

  useEffect(() => {
    const current = handle.current;
    if (!current) return;
    current.camera.zoom = 1;
    current.camera.position.set(0, 0, 30);
    current.camera.lookAt(0, 0, 0);
    current.camera.updateProjectionMatrix();
    current.renderer.render(current.scene, current.camera);
  }, [resetSignal]);

  return <div className={styles.canvas} ref={mount} aria-hidden="true" />;
}
