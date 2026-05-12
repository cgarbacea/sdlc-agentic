---
tags: [i18n, Lingui, Trans, translation, locales, compile-time, react-i18next]
executor: fe
---

# i18n Rules

Check `package.json` to confirm the i18n library in use. The project uses compile-time i18n (e.g. Lingui) — not runtime i18n.

## Usage (Lingui example)

```tsx
import { Trans } from "@lingui/react/macro";
import { t } from "@lingui/core/macro";
import { useLingui } from "@lingui/react";

// In JSX
<Trans>Save changes</Trans>

// In expressions
const label = t`Save changes`;

// Dynamic strings
const { _ } = useLingui();
const message = _(msg`Hello ${name}`);
```

## Rules

- All user-visible strings must be wrapped — no hardcoded strings in JSX
- Never use `react-i18next` or `next-i18next` — this project uses Lingui
- Check the project's `locales/` directory for the supported locale list
- After adding new strings: run `pnpm lingui:extract` then `pnpm lingui:compile`
