# hooks

React hooks that two or more features use, one per file, named
`use<Thing>.ts`. A hook only one feature uses lives in that feature's
`hooks/` folder instead.

May import `lib/` (not `lib/server/`) and `types/`. Never a feature, a route
or a component: ESLint refuses them.
