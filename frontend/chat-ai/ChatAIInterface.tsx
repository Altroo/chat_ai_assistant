"use client";
import { ButtonBase } from "@mui/material";

import {
  useEffect,
  useEffectEvent,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { Bot, ArrowRight, Clock3, MessageSquarePlus, X } from "./ChatAIIcons";
import styles from "./chat-ai.module.css";
export type ChatAILanguage = "en" | "fr";

export const ChatAIFloatingButton = ({
  open,
  toggle,
  offset = false,
}: {
  open: boolean;
  toggle: () => void;
  offset?: boolean;
}) => (
  <ButtonBase
    disableRipple
    type="button"
    className={styles.floating}
    aria-label="Ask AI Assistant"
    title={open ? undefined : "Ask AI Assistant"}
    aria-expanded={open}
    aria-controls="chat-ai-panel"
    hidden={open}
    onClick={toggle}
    style={{
      position: "fixed",
      width: 56,
      height: 56,
      ...(offset ? { bottom: 96 } : {}),
    }}
  >
    <Bot size={26} aria-hidden="true" />
  </ButtonBase>
);

export const ChatAIPanel = ({
  children,
  close,
  minimized,
  offset = false,
}: {
  children: ReactNode;
  close: () => void;
  minimized: boolean;
  offset?: boolean;
}) => {
  const panel = useRef<HTMLElement>(null);
  const [viewport, setViewport] = useState<{
    height: number;
    top: number;
  } | null>(null);
  useEffect(() => {
    const view = window.visualViewport;
    if (!view) return;
    const resize = () =>
      setViewport({ height: view.height, top: view.offsetTop });
    resize();
    view.addEventListener("resize", resize);
    view.addEventListener("scroll", resize);
    return () => {
      view.removeEventListener("resize", resize);
      view.removeEventListener("scroll", resize);
    };
  }, []);
  const onClose = useEffectEvent(close);
  useEffect(() => {
    if (minimized) return;
    const previous = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !event.defaultPrevented) onClose();
      if (
        event.key !== "Tab" ||
        event.defaultPrevented ||
        !panel.current?.contains(event.target as Node) ||
        !window.matchMedia("(max-width: 640px)").matches
      )
        return;
      const controls = Array.from(
        panel.current.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href], [tabindex="0"]',
        ),
      ).filter((item) => item.getClientRects().length > 0);
      const first = controls[0],
        last = controls.at(-1);
      if (
        event.shiftKey &&
        (document.activeElement === first ||
          document.activeElement === panel.current)
      ) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", keydown);
    return () => {
      document.removeEventListener("keydown", keydown);
      previous?.focus();
    };
  }, [minimized]);
  return (
    <aside
      ref={panel}
      id="chat-ai-panel"
      role="dialog"
      aria-label="AI Assistant"
      tabIndex={-1}
      className={styles.panel}
      hidden={minimized}
      style={
        {
          display: minimized ? "none" : undefined,
          "--chat-ai-bottom": offset ? "96px" : "24px",
          ...(viewport
            ? {
                "--assistant-height": `${viewport.height}px`,
                "--assistant-top": `${viewport.top}px`,
              }
            : {}),
        } as CSSProperties
      }
    >
      {children}
    </aside>
  );
};

/** Business state and authorized content remain in each application's adapter. */
export const ChatAIInterface = ({
  children,
  open,
  onOpenChange,
  suppressed = false,
  offset = false,
}: {
  children: ReactNode;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  suppressed?: boolean;
  offset?: boolean;
}) => (
  <div data-chat-ai-shell style={{ display: suppressed ? "none" : "contents" }}>
    <ChatAIFloatingButton
      open={open}
      toggle={() => onOpenChange(!open)}
      offset={offset}
    />
    <ChatAIPanel
      minimized={!open || suppressed}
      close={() => onOpenChange(false)}
      offset={offset}
    >
      {children}
    </ChatAIPanel>
  </div>
);

export const ChatAIHeader = ({
  close,
  newConversation,
  history,
  historyExpanded,
  appName,
  language = "fr",
}: {
  close: () => void;
  newConversation?: () => void;
  history?: () => void;
  historyExpanded?: boolean;
  appName: string;
  language?: ChatAILanguage;
}) => (
  <>
    <header className={styles.header}>
      <span className={styles.botIcon}>
        <Bot size={23} aria-hidden="true" />
      </span>
      <div>
        <h2 className={styles.srOnly}>AI Assistant</h2>
        <p>
          {language === "en" ? "Your help in" : "Votre aide dans"} {appName}
        </p>
      </div>
      <ButtonBase
        disableRipple
        type="button"
        className={styles.iconButton}
        aria-label={language === "en" ? "Close" : "Fermer"}
        title={language === "en" ? "Close assistant" : "Fermer l’assistant"}
        onClick={close}
      >
        <X size={20} />
      </ButtonBase>
    </header>
    {newConversation && (
      <nav
        className={styles.toolbar}
        aria-label={language === "en" ? "Conversations" : "Conversations"}
      >
        <ButtonBase disableRipple type="button" onClick={newConversation}>
          <MessageSquarePlus size={17} aria-hidden="true" />
          {language === "en" ? "New conversation" : "Nouvelle conversation"}
        </ButtonBase>
        <ButtonBase
          disableRipple
          type="button"
          onClick={history}
          aria-expanded={historyExpanded}
        >
          <Clock3 size={17} aria-hidden="true" />
          {language === "en" ? "History" : "Historique"}
        </ButtonBase>
      </nav>
    )}
  </>
);

export const ChatAIWelcome = ({
  language,
  suggestions,
  busy,
  send,
}: {
  language: ChatAILanguage;
  suggestions: string[];
  busy: boolean;
  send: (question: string) => void;
}) => (
  <div className={styles.welcome}>
    <span className={styles.botIcon}>
      <Bot size={28} aria-hidden="true" />
    </span>
    <h3>
      {language === "en"
        ? "What would you like to do?"
        : "Que souhaitez-vous faire ?"}
    </h3>
    <p>
      {language === "en"
        ? "Select a question to send it, or describe what you need."
        : "Cliquez sur une question pour l’envoyer, ou décrivez votre besoin."}
    </p>
    <div className={styles.suggestions}>
      {suggestions.slice(0, 4).map((question) => (
        <ButtonBase
          disableRipple
          type="button"
          key={question}
          disabled={busy}
          onClick={() => send(question)}
        >
          <ArrowRight size={18} aria-hidden="true" />
          {question}
        </ButtonBase>
      ))}
    </div>
  </div>
);

export const ChatAIMessageBox = ({
  role,
  text,
  children,
  language = "fr",
}: {
  role: "user" | "assistant";
  text?: string;
  children?: ReactNode;
  language?: ChatAILanguage;
}) => (
  <article
    className={role === "user" ? styles.userMessage : styles.assistantMessage}
    aria-label={
      role === "user"
        ? language === "en"
          ? "Your message"
          : "Message de vous"
        : "AI Assistant"
    }
  >
    <div className={styles.messageAuthor}>
      {role === "assistant" && <Bot size={17} aria-hidden="true" />}
      <strong>{role === "user" ? (language === "en" ? "You" : "Vous") : "AI Assistant"}</strong>
    </div>
    {text && (
      <p dir="auto" className={styles.messageText}>
        {text}
      </p>
    )}
    {children}
  </article>
);
