"use client";
import {
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent,
  type PointerEvent,
} from "react";

type Position = { right: number; bottom: number };
type Gesture = Position & {
  pointerId: number;
  x: number;
  y: number;
  moved: boolean;
};
const STEP = 24;
const THRESHOLD = 6;

/** Framework-independent behavior shared by all six application launchers.
 * Position belongs to this mounted authenticated layout, never to chat data.
 */
export function useDraggableLauncher(activate: () => void) {
  const ref = useRef<HTMLButtonElement>(null);
  const gesture = useRef<Gesture | null>(null);
  const suppressClick = useRef(false);
  const [position, setPosition] = useState<Position | null>(null);
  const [dragging, setDragging] = useState(false);
  const currentPosition = (button: HTMLButtonElement): Position => {
    const rect = button.getBoundingClientRect();
    return {
      right: document.documentElement.clientWidth - rect.right,
      bottom: document.documentElement.clientHeight - rect.bottom,
    };
  };
  const bounded = (point: Position, button: HTMLButtonElement): Position => {
    const rect = button.getBoundingClientRect();
    return {
      right: Math.max(
        16,
        Math.min(
          point.right,
          Math.max(16, document.documentElement.clientWidth - rect.width - 16),
        ),
      ),
      bottom: Math.max(
        16,
        Math.min(
          point.bottom,
          Math.max(
            16,
            document.documentElement.clientHeight - rect.height - 16,
          ),
        ),
      ),
    };
  };
  const finish = (event: PointerEvent<HTMLButtonElement>) => {
    const active = gesture.current;
    if (!active || active.pointerId !== event.pointerId) return;
    suppressClick.current = active.moved;
    gesture.current = null;
    setDragging(false);
    if (event.currentTarget.hasPointerCapture?.(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  };
  const style: CSSProperties = {
    // Percentages match the fixed containing block, excluding scrollbar gutters.
    // CSS bounds include device safe areas and remain effective after resize.
    right: `clamp(max(16px, env(safe-area-inset-right)), ${position ? position.right + "px" : "var(--chat-ai-launcher-right, 24px)"}, calc(100% - var(--chat-ai-launcher-size, 56px) - max(16px, env(safe-area-inset-left))))`,
    bottom: `clamp(max(16px, env(safe-area-inset-bottom)), ${position ? position.bottom + "px" : "96px"}, calc(100% - var(--chat-ai-launcher-size, 56px) - max(16px, env(safe-area-inset-top))))`,
    touchAction: "none",
    userSelect: "none",
    cursor: dragging ? "grabbing" : "grab",
  };
  return {
    ref,
    style,
    onPointerDown(event: PointerEvent<HTMLButtonElement>) {
      if (!event.isPrimary || event.button !== 0) return;
      suppressClick.current = false;
      gesture.current = {
        ...currentPosition(event.currentTarget),
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        moved: false,
      };
      event.currentTarget.setPointerCapture?.(event.pointerId);
    },
    onPointerMove(event: PointerEvent<HTMLButtonElement>) {
      const active = gesture.current;
      if (!active || active.pointerId !== event.pointerId) return;
      const dx = event.clientX - active.x;
      const dy = event.clientY - active.y;
      if (!active.moved && Math.hypot(dx, dy) < THRESHOLD) return;
      active.moved = true;
      suppressClick.current = true;
      setDragging(true);
      setPosition(
        bounded(
          { right: active.right - dx, bottom: active.bottom - dy },
          event.currentTarget,
        ),
      );
    },
    onPointerUp: finish,
    onPointerCancel: finish,
    onLostPointerCapture: finish,
    onClick(event: MouseEvent<HTMLButtonElement>) {
      if (suppressClick.current && event.detail !== 0) {
        suppressClick.current = false;
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      suppressClick.current = false;
      activate();
    },
    onKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const direction: Record<string, Position> = {
        ArrowLeft: { right: STEP, bottom: 0 },
        ArrowRight: { right: -STEP, bottom: 0 },
        ArrowUp: { right: 0, bottom: STEP },
        ArrowDown: { right: 0, bottom: -STEP },
      };
      if (event.key !== "Home" && !direction[event.key]) return;
      event.preventDefault();
      suppressClick.current = false;
      if (event.key === "Home") {
        setPosition(null);
        return;
      }
      const point = currentPosition(event.currentTarget);
      const delta = direction[event.key];
      setPosition(
        bounded(
          {
            right: point.right + delta.right,
            bottom: point.bottom + delta.bottom,
          },
          event.currentTarget,
        ),
      );
    },
  };
}
