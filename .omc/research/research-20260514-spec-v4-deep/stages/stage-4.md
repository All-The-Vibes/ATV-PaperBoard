# Stage 4 — OpenCode Plugin Loader: SPEC v4 §2.3 Verification

**Date:** 2026-05-14
**Budget used:** 8 fetches
**Sources:** opencode.ai/docs, npm registry `@opencode-ai/plugin@1.14.51` type definitions (extracted from tarball)

---

## Finding 1 — Import path: `@opencode/plugin` does NOT exist

[FINDING] The SPEC's import path `import type { Plugin, Hooks } from "@opencode/plugin"` is **WRONG**.

The correct package name is **`@opencode-ai/plugin`** (with `-ai`). The package `@opencode/plugin` returns 404 on the npm registry.

[EVIDENCE]
- `curl https://registry.npmjs.org/@opencode/plugin/latest` → 404
- `curl https://registry.npmjs.org/@opencode-ai/plugin/latest` → HTTP 200, `version: 1.14.51`
- Correct import: `import type { Plugin } from "@opencode-ai/plugin"`

[CONFIDENCE] HIGH (direct npm registry query)

---

## Finding 2 — `Plugin` type: async, returns `Promise<Hooks>`; export must be named `server`

[FINDING] The SPEC writes:
```ts
import type { Plugin, Hooks } from "@opencode/plugin";
export const paperboardPlugin: Plugin = (ctx) => { ... };
```

The **actual** type from `@opencode-ai/plugin@1.14.51`:
```ts
export type Plugin = (input: PluginInput, options?: PluginOptions) => Promise<Hooks>;
export type PluginModule = {
  id?: string;
  server: Plugin;
  tui?: never;
};
```

Three divergences:
1. Package name wrong (see Finding 1).
2. `Plugin` returns `Promise<Hooks>` — must be async.
3. OpenCode discovers the plugin via the named export `server` on a `PluginModule`. `export const paperboardPlugin` would not be auto-discovered.

Correct shape:
```ts
export const server: Plugin = async (input, options) => { return hooks; };
```

[EVIDENCE] `/tmp/package/dist/index.d.ts` lines 36-55 (extracted from tarball).

[CONFIDENCE] HIGH

---

## Finding 3 — `PluginInput` has NO `pluginDir` field

[FINDING] The SPEC uses `ctx.pluginDir` to locate the Python core:
```ts
spawn("python", [`${ctx.pluginDir}/core/cli.py`, ...])
```

The actual `PluginInput` type has **no `pluginDir` property**:
```ts
export type PluginInput = {
  client: ReturnType<typeof createOpencodeClient>;
  project: Project;
  directory: string;    // project directory (git root equivalent)
  worktree: string;     // worktree path
  experimental_workspace: { ... };
  serverUrl: URL;
  $: BunShell;
};
```

To resolve the plugin's own directory, use ESM `import.meta.dirname` at module scope — not `ctx`.

[EVIDENCE] Full `PluginInput` type in tarball `index.d.ts` lines 36-51. No `pluginDir` field.

[CONFIDENCE] HIGH

---

## Finding 4 — `"tool.execute.after"` event name: CORRECT (but signature has two args)

[FINDING] The event name `"tool.execute.after"` is **verified correct**.

Actual signature from `Hooks` interface:
```ts
"tool.execute.after"?: (
  input: { tool: string; sessionID: string; callID: string; args: any; },
  output: { title: string; output: string; metadata: any; }
) => Promise<void>;
```

The SPEC's handler reads `input.output` for the tool result — **wrong**. The tool result is in `output.output` (second argument). The SPEC wrote a single-argument handler when it needs two.

[CONFIDENCE] HIGH

---

## Finding 5 — `OPENCODE_CONFIG_DIR`: CONFIRMED; default is `~/.config/opencode/`

[FINDING] `OPENCODE_CONFIG_DIR` is a real, documented env var. Default config dir is `~/.config/opencode/` (XDG). The SPEC uses it correctly in `core/persist.py` and `core/detect.py`.

[EVIDENCE] opencode.ai/docs/config: "Specify a custom config directory using the `OPENCODE_CONFIG_DIR` environment variable."

[CONFIDENCE] HIGH

---

## Finding 6 — `opencode.json` plugin key is `"plugin"` (singular), NOT `"plugins"`

[FINDING] The SPEC shows `{ "plugins": ["atv-paperboard"] }`. Wrong.

Actual `Config` type:
```ts
export type Config = Omit<SDKConfig, "plugin"> & {
  plugin?: Array<string | [string, PluginOptions]>;
};
```

Key is `"plugin"` (singular). Supports tuples: `["atv-paperboard", { option: val }]`.

[EVIDENCE] `index.d.ts` lines 48-50.

[CONFIDENCE] HIGH

---

## Finding 7 — SKILL.md discovery paths: confirmed Claude-compatible multi-path

[FINDING] OpenCode reads SKILL.md from multiple paths — the SPEC's claim of "Claude-compatible paths" is confirmed. Both project-local and global paths are supported:
- `.opencode/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md`
- `~/.config/opencode/skills/<name>/SKILL.md`
- `~/.claude/skills/<name>/SKILL.md`
- `~/.agents/skills/<name>/SKILL.md`

[EVIDENCE] opencode.ai/docs/skills

[CONFIDENCE] HIGH

---

## Finding 8 — SKILL.md `allowed_tools` vs `allowed-tools`: moot for OpenCode

[FINDING] OpenCode's SKILL.md frontmatter schema recognizes only: `name`, `description`, `license`, `compatibility`, `metadata`. All other fields are silently ignored — including both `allowed_tools` (underscore) and `allowed-tools` (hyphen).

SPEC §8 Q2 concern is **a non-issue for OpenCode**. The portability concern only applies between Claude Code (uses `allowed-tools` hyphen) and Codex (uses `allowed_tools` underscore in `openai.yaml`).

[EVIDENCE] opencode.ai/docs/skills: "Only these fields are recognized" + "Unknown frontmatter fields are ignored."

[CONFIDENCE] MEDIUM

---

## Summary of SPEC v4 §2.3 Defects

| # | SPEC Claim | Actual | Severity |
|---|---|---|---|
| D1 | `import ... from "@opencode/plugin"` | Package is `@opencode-ai/plugin` | BREAKING |
| D2 | `export const paperboardPlugin: Plugin = (ctx) => { return { hooks }; }` | Must be `export const server: Plugin = async (input) => { return hooks; }` | BREAKING |
| D3 | `ctx.pluginDir` in PluginInput | No such field; use `import.meta.dirname` | BREAKING |
| D4 | `"tool.execute.after"` event name | Correct | None |
| D5 | Single-arg hook `(input)`, reads `input.output` | Two-arg `(input, output)`, tool result is `output.output` | BUG |
| D6 | `{ "plugins": [...] }` in opencode.json | Key is `"plugin"` (singular) | BREAKING |
| D7 | `OPENCODE_CONFIG_DIR` documented | Confirmed | None |
| D8 | SKILL.md Claude-compatible paths | Confirmed; multi-path discovery | None |

---

## Corrected §2.3 Plugin Snippet

```ts
// adapters/opencode/opencode.plugin.ts
import type { Plugin } from "@opencode-ai/plugin";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join, dirname } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

export const server: Plugin = async (input) => {
  return {
    "tool.execute.after": async (toolInput, toolOutput) => {
      if (toolInput.tool === "Write") {
        spawn("python", [
          join(__dirname, "../core/cli.py"),
          "detect-artifact-candidate",
          JSON.stringify(toolOutput.output),
        ], { stdio: "inherit", detached: true });
      }
    },
  };
};
```

```json
{ "plugin": ["atv-paperboard"] }
```

---

[STAGE_COMPLETE:4]
