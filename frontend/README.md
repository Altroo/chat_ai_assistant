# Shared assistant interface

The canonical MUI interface is in `chat-ai/`. It reproduces Design Workflow's assistant geometry, typography, local SVG line icons and light/dark palette without adding a design or icon dependency. The reference uses a 14px root; dimensions here are resolved explicitly so host application root sizes do not change the panel.

The shared empty state shows up to four authorized suggestions. Bold message-author labels are retained by request. Opening shortcut help inserts `/` only when the draft is empty, preserves existing prose and enables Send; bare `/` is handled by each adapter’s existing permission-filtered help.

The application adapter owns authentication, capabilities, API requests, company context, conversations, streaming, navigation, confirmation and audit. It passes the app name, authorized suggestions and shortcuts, handlers and content into the shared UI. Only apps with company tabs render the company control. Management Projet uses a trusted singleton company internally and has no company row in the panel.

Change the canonical files, then copy them to an authorized MUI frontend:

```sh
python scripts/sync_frontend.py --write ../facturation/facturation_frontend
python scripts/sync_frontend.py ../facturation/facturation_frontend
```

Verification compares every file and its versioned checksum manifest. Do not edit the application copies or add app-specific conditions to the shared UI. Run each application's assistant regressions and compare empty/populated chats, with/without shortcuts, in both themes and at mobile sizes. The script refuses a frontend without existing MUI; Design Workflow keeps its native reference implementation.

The default command is read-only verification. No backend configuration, private data or credentials is copied. Production feature activation and model acceptance remain separately controlled.
