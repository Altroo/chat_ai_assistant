import { fireEvent, render, screen } from "@testing-library/react";
import { useDraggableLauncher } from "./useDraggableLauncher";

const activate = jest.fn();
function Launcher() {
  const launcher = useDraggableLauncher(activate);
  return <button {...launcher}>AI Assistant</button>;
}
const pointer = (
  button: HTMLElement,
  type: string,
  values: Record<string, unknown> = {},
) => {
  const event = new MouseEvent(type, {
    bubbles: true,
    clientX: 972,
    clientY: 676,
    button: 0,
    ...values,
  });
  Object.defineProperties(event, {
    pointerId: { value: values.pointerId ?? 1 },
    isPrimary: { value: values.isPrimary ?? true },
    pointerType: { value: values.pointerType ?? "mouse" },
  });
  fireEvent(button, event);
};
function setup() {
  render(<Launcher />);
  const button = screen.getByRole("button", { name: "AI Assistant" });
  jest.spyOn(button, "getBoundingClientRect").mockReturnValue({
    x: 944,
    y: 648,
    left: 944,
    top: 648,
    right: 1000,
    bottom: 704,
    width: 56,
    height: 56,
    toJSON: () => ({}),
  });
  button.setPointerCapture = jest.fn();
  button.hasPointerCapture = jest.fn(() => true);
  button.releasePointerCapture = jest.fn();
  return button;
}
beforeEach(() => {
  jest.clearAllMocks();
  Object.defineProperty(document.documentElement, "clientWidth", {
    configurable: true,
    value: 1024,
  });
  Object.defineProperty(document.documentElement, "clientHeight", {
    configurable: true,
    value: 800,
  });
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    value: 1024,
  });
  Object.defineProperty(window, "innerHeight", {
    configurable: true,
    value: 800,
  });
});
it("keeps a normal click and keyboard activation available", () => {
  const button = setup();
  pointer(button, "pointerdown");
  pointer(button, "pointerup");
  fireEvent.click(button, { detail: 1 });
  fireEvent.click(button, { detail: 0 });
  expect(activate).toHaveBeenCalledTimes(2);
});
it("allows click despite a small hand movement", () => {
  const button = setup();
  pointer(button, "pointerdown");
  pointer(button, "pointermove", { clientX: 969, clientY: 674 });
  pointer(button, "pointerup");
  fireEvent.click(button, { detail: 1 });
  expect(activate).toHaveBeenCalledTimes(1);
  expect(button.style.cursor).toBe("grab");
});
it.each(["mouse", "touch", "pen"])(
  "moves with %s and suppresses only the following pointer click",
  (pointerType) => {
    const button = setup();
    pointer(button, "pointerdown", { pointerType });
    pointer(button, "pointermove", { pointerType, clientX: 772, clientY: 476 });
    expect(button.style.right).toContain("224px");
    expect(button.style.bottom).toContain("296px");
    expect(button.style.cursor).toBe("grabbing");
    pointer(button, "pointerup", { pointerType });
    fireEvent.click(button, { detail: 1 });
    expect(activate).not.toHaveBeenCalled();
    expect(button.style.cursor).toBe("grab");
    expect(button.releasePointerCapture).toHaveBeenCalledWith(1);
    pointer(button, "pointerdown", { pointerType });
    pointer(button, "pointerup", { pointerType });
    fireEvent.click(button, { detail: 1 });
    expect(activate).toHaveBeenCalledTimes(1);
  },
);
it.each(["pointercancel", "lostpointercapture"])(
  "recovers after %s without opening the chat",
  (eventType) => {
    const button = setup();
    pointer(button, "pointerdown");
    pointer(button, "pointermove", { clientX: 772 });
    pointer(button, eventType);
    fireEvent.click(button, { detail: 1 });
    expect(activate).not.toHaveBeenCalled();
    expect(button.style.cursor).toBe("grab");
    fireEvent.click(button, { detail: 0 });
    expect(activate).toHaveBeenCalledTimes(1);
  },
);
it("ignores secondary pointers and non-left buttons", () => {
  const button = setup();
  pointer(button, "pointerdown", { isPrimary: false });
  pointer(button, "pointermove", { clientX: 772 });
  expect(button.style.cursor).toBe("grab");
  pointer(button, "pointerdown", { button: 2 });
  pointer(button, "pointermove", { clientX: 772 });
  expect(button.style.cursor).toBe("grab");
  pointer(button, "pointerdown");
  pointer(button, "pointermove", { pointerId: 2, clientX: 772 });
  expect(button.style.cursor).toBe("grab");
});
it("bounds dragged coordinates to the viewport", () => {
  const button = setup();
  pointer(button, "pointerdown");
  pointer(button, "pointermove", { clientX: -5000, clientY: -5000 });
  expect(button.style.right).toContain("952px");
  expect(button.style.bottom).toContain("728px");
  pointer(button, "pointermove", { clientX: 5000, clientY: 5000 });
  expect(button.style.right).toContain("16px");
  expect(button.style.bottom).toContain("16px");
});
it("supports arrow movement and Home reset without opening the assistant", () => {
  const button = setup();
  fireEvent.keyDown(button, { key: "ArrowUp" });
  expect(button.style.bottom).toContain("120px");
  fireEvent.keyDown(button, { key: "Home" });
  expect(button.style.bottom).toContain("96px");
  expect(button.style.right).toContain("var(--chat-ai-launcher-right");
  expect(activate).not.toHaveBeenCalled();
});
it("preserves browser modifier shortcuts", () => {
  const button = setup();
  fireEvent.keyDown(button, { key: "ArrowLeft", altKey: true });
  expect(button.style.right).toContain("var(--chat-ai-launcher-right");
  expect(activate).not.toHaveBeenCalled();
});

it("excludes scrollbar gutters from arrow movement and the first drag", () => {
  Object.defineProperty(document.documentElement, "clientWidth", {
    configurable: true,
    value: 1009,
  });
  Object.defineProperty(document.documentElement, "clientHeight", {
    configurable: true,
    value: 785,
  });
  const button = setup();
  jest.mocked(button.getBoundingClientRect).mockReturnValue({
    x: 929,
    y: 633,
    left: 929,
    top: 633,
    right: 985,
    bottom: 689,
    width: 56,
    height: 56,
    toJSON: () => ({}),
  });
  fireEvent.keyDown(button, { key: "ArrowUp" });
  expect(button.style.right).toContain(", 24px,");
  expect(button.style.bottom).toContain(", 120px,");
  fireEvent.keyDown(button, { key: "ArrowRight" });
  expect(button.style.bottom).toContain(", 96px,");
  fireEvent.keyDown(button, { key: "Home" });
  pointer(button, "pointerdown", { clientX: 957, clientY: 661 });
  pointer(button, "pointermove", { clientX: 937, clientY: 641 });
  expect(button.style.right).toContain(", 44px,");
  expect(button.style.bottom).toContain(", 116px,");
  pointer(button, "pointermove", { clientX: -5000, clientY: -5000 });
  expect(button.style.right).toContain(", 937px,");
  expect(button.style.bottom).toContain(", 713px,");
});
