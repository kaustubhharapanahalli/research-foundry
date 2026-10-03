# components/shared

Composites that two or more features use, such as a reader pane or a data
table built from `components/ui/` pieces. A component moves here from
`features/<area>/components/` when a second feature needs it, not before.

May import `components/ui/`, `hooks/`, `lib/` (not `lib/server/`), `types/`
and `styles/`. Never a feature or a route: ESLint refuses both.
