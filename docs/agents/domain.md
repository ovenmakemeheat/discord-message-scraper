# Domain docs

- **Layout:** Multi-context
- **Root map:** `CONTEXT-MAP.md` lists all bounded contexts and points to their individual `CONTEXT.md` files
- **ADRs:** Each context may have its own `docs/adr/` directory, or share a root-level `docs/adr/`

## Consumer rules

- Before working in a context, read its `CONTEXT.md` to learn the domain language
- Read `CONTEXT-MAP.md` first to identify which context you're operating in
- When making architectural decisions, check `docs/adr/` for prior decisions that may constrain your options
- If you create a new ADR, follow the numbering and format of existing ones
