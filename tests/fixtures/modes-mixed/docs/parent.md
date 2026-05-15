---
depends_on:
  - always-dep
  - {id: shared-dep, when: [narration, plan]}
  - {id: narration-only, when: [narration]}
---
