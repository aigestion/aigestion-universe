# @aigestion/ui

Shared neural design system for Daniela OS.

- **Tokens** — neural palette (cyan `#00f0ff`, magenta `#e024c3`, bg `#01050e`), radius, spacing, fonts
- **Components** — `NeuralButton` (primary/secondary/ghost), `NeuralCard` (accent bar)

```tsx
import { NeuralButton, NeuralCard, colors } from "@aigestion/ui"

<NeuralCard accent={colors.magenta}>
  <NeuralButton variant="primary">Enter Neural Shell</NeuralButton>
</NeuralCard>
```
