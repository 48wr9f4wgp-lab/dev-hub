# Scriptable Dashboard

Personal iPhone dashboard loaded by Scriptable from GitHub.

## Files
- `loader.js` — paste this once into Scriptable.
- `main.js` — remotely updated dashboard implementation.

The loader downloads `main.js` on each run and caches the last successfully executed version locally. If GitHub/network loading fails, it falls back to the last good cached version.

Remote URL:
`https://raw.githubusercontent.com/48wr9f4wgp-lab/dev-hub/main/scriptable-dashboard/main.js`
