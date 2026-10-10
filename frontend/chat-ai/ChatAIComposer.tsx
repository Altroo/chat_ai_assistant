import { ButtonBase, TextareaAutosize } from "@mui/material";
import { useId, useRef, useState } from "react";

import { Send, Square } from "./ChatAIIcons";
import { ChatAIShortcuts } from "./ChatAIShortcuts";
import type { ChatShortcut } from "./ChatAIShortcuts";
import styles from "./chat-ai.module.css";

export const ChatAIComposer = ({
  draft,
  setDraft,
  busy,
  historyOpen,
  shortcuts,
  language,
  send,
  cancel,
}: {
  draft: string;
  setDraft: (value: string) => void;
  busy: boolean;
  historyOpen: boolean;
  shortcuts: ChatShortcut[];
  language: "en" | "fr";
  send: () => void;
  cancel: () => void;
}) => {
  const input = useRef<HTMLTextAreaElement>(null);
  const listId = useId();
  const [selection, setSelection] = useState({ draft: "", index: 0 });
  const [dismissedDraft, setDismissedDraft] = useState<string | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const prefix = helpOpen ? "/" : draft;
  const matches = shortcuts.filter((item) =>
    item.command.toLowerCase().startsWith(prefix.toLowerCase()),
  );
  const visible =
    !historyOpen &&
    !busy &&
    (helpOpen || /^\/[^\s]*$/.test(draft)) &&
    dismissedDraft !== draft;
  const activeIndex = Math.min(
    selection.draft === draft ? selection.index : 0,
    Math.max(0, matches.length - 1),
  );
  const en = language === "en";
  const choose = (value: string) => {
    const description = helpOpen ? draft.replace(/^\/\S*\s*/, "") : "";
    setDraft(value + description);
    setHelpOpen(false);
    setDismissedDraft(null);
    input.current?.focus();
  };
  const submit = () => {
    setHelpOpen(false);
    setDismissedDraft(draft);
    send();
  };
  if (historyOpen) return null;
  return (
    <>
      {visible && (
        <section className={styles.shortcuts}>
          <ChatAIShortcuts
            draft={prefix}
            shortcuts={shortcuts}
            language={language}
            listId={listId}
            activeIndex={activeIndex}
            choose={choose}
            highlight={(index) => setSelection({ draft, index })}
          />
        </section>
      )}
      <footer className={styles.footer}>
        <div className={styles.composer}>
          <TextareaAutosize
            ref={input}
            minRows={2}
            maxRows={6}
            maxLength={4000}
            dir="auto"
            placeholder={en ? "Ask a question…" : "Posez votre question…"}
            value={draft}
            disabled={busy}
            aria-label={en ? "Your message" : "Votre message"}
            aria-autocomplete="list"
            aria-controls={visible ? listId : undefined}
            aria-activedescendant={
              visible && matches.length ? `${listId}-${activeIndex}` : undefined
            }
            onChange={(event) => {
              setDraft(event.target.value);
              setHelpOpen(false);
              setDismissedDraft(null);
            }}
            onKeyDown={(event) => {
              if (event.nativeEvent.isComposing) return;
              if (visible && event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                setDismissedDraft(draft);
                setHelpOpen(false);
                return;
              }
              if (visible && matches.length && !event.shiftKey) {
                if (event.key === "ArrowDown" || event.key === "ArrowUp") {
                  event.preventDefault();
                  setSelection({
                    draft,
                    index:
                      (activeIndex +
                        (event.key === "ArrowDown" ? 1 : -1) +
                        matches.length) %
                      matches.length,
                  });
                  return;
                }
                if (event.key === "Enter" || event.key === "Tab") {
                  event.preventDefault();
                  choose(matches[activeIndex].command + " ");
                  return;
                }
              }
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit();
              }
            }}
          />
          <ButtonBase
            disableRipple
            type="button"
            className={styles.send}
            aria-label={
              busy
                ? en
                  ? "Cancel response"
                  : "Annuler la réponse"
                : en
                  ? "Send"
                  : "Envoyer"
            }
            disabled={!busy && !draft.trim()}
            onClick={busy ? cancel : submit}
          >
            {busy ? (
              <Square size={18} aria-hidden="true" />
            ) : (
              <Send size={20} aria-hidden="true" />
            )}
          </ButtonBase>
        </div>
        <p className={styles.composerHint}>
          {en
            ? "Enter to send · Shift + Enter for a new line · "
            : "Entrée pour envoyer · Maj + Entrée pour une nouvelle ligne · "}
          <ButtonBase
            disableRipple
            type="button"
            disabled={busy}
            onClick={() => {
              if (!draft.trim()) setDraft("/");
              setHelpOpen(true);
              setDismissedDraft(null);
              setSelection({ draft, index: 0 });
              input.current?.focus();
            }}
          >
            {en ? "/ Shortcuts" : "/ Raccourcis"}
          </ButtonBase>
        </p>
        <p className={styles.privacy}>
          {en
            ? "Your permissions stay the same. Changes require your confirmation."
            : "Vos accès restent les mêmes. Toute modification demande votre confirmation."}
        </p>
      </footer>
    </>
  );
};
