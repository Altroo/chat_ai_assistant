import { ButtonBase } from "@mui/material";
import styles from "./chat-ai.module.css";
export type ChatShortcut = {
  command: string;
  title: string;
  help: string;
  example: string;
};
export const ChatAIShortcuts = ({
  draft,
  shortcuts,
  language = "fr",
  choose,
  listId = "chat-ai-shortcuts",
  activeIndex = 0,
  highlight,
}: {
  draft: string;
  shortcuts: ChatShortcut[];
  language?: "fr" | "en";
  choose: (value: string) => void;
  listId?: string;
  activeIndex?: number;
  highlight?: (index: number) => void;
}) => {
  const matches = shortcuts.filter((item) =>
    item.command
      .toLowerCase()
      .startsWith(draft.trim().split(/\s+/)[0].toLowerCase()),
  );
  return (
    <>
      <h3>
        {language === "en"
          ? "Assistant shortcuts"
          : "Raccourcis de l’assistant"}
      </h3>
      <p>
        {language === "en"
          ? "Choose a module or action. You can also write normally without a shortcut."
          : "Choisissez un module ou une action. Vous pouvez aussi écrire normalement, sans raccourci."}
      </p>
      <div
        id={listId}
        role="listbox"
        aria-label={
          language === "en"
            ? "Assistant shortcuts"
            : "Raccourcis de l’assistant"
        }
        className={styles.shortcutList}
      >
        {matches.map((item, index) => (
          <ButtonBase
            disableRipple
            type="button"
            role="option"
            id={`${listId}-${index}`}
            key={item.command}
            aria-selected={index === activeIndex}
            onPointerMove={() => highlight?.(index)}
            onClick={() => choose(item.command + " ")}
            ref={(node) => {
              if (node && index === activeIndex)
                node.scrollIntoView?.({ block: "nearest" });
            }}
          >
            <strong>
              <code>{item.command}</code> {item.title}
            </strong>
            <span>{item.help}</span>
            <small>
              {language === "en" ? "Example: " : "Exemple : "}
              {item.example}
            </small>
          </ButtonBase>
        ))}
      </div>
      {!matches.length && (
        <p role="status">
          {language === "en"
            ? "No matching shortcut. Remove the letters after / to see the available commands."
            : "Aucun raccourci correspondant. Effacez les lettres après / pour voir les commandes disponibles."}
        </p>
      )}
    </>
  );
};
