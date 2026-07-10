# fusion — the notary of the Fusion Convention

The reference CLI. It records, checks, and composes; it never judges —
judgment belongs to the skill family. Buckets that follow
[the convention](../SPEC.md) are Fusion whether or not this tool ever
touches them.

## Install

```sh
uv tool install fusion-cli
```

## The eight commands (there is no ninth)

| Command | Does |
|---|---|
| `fusion new <path>` | Scaffold a complete bucket + register it in the hub |
| `fusion hub` | List / register (`add <path>`) / retire (`remove <name>`) buckets |
| `fusion log <verb> <object>` | Append a ledger entry — the only writer. No args: read the ledger |
| `fusion index [path]` | Regenerate `INDEX.md` in `library/` and `activities/` |
| `fusion check [path]` | Audit a bucket against SPEC §11 — exit 1 on errors |
| `fusion status [path]` | One bucket at a glance |
| `fusion today` | The composed day, across every bucket in the hub |
| `fusion agenda` | The wider horizon — dated and active, across the hub |

Every command takes `--json` (agents parse, never scrape). `log`, `new`,
and `index` take `--as <actor>`; the pen defaults to `FUSION_ACTOR`, then
the OS username. `status` and `log` take `--since <date|last-reflection>`.
`log` also takes `--bucket` (resolves the ledger; default: walk up from the current directory).
The hub lives at `~/.fusion/hub.md` (`FUSION_HUB` overrides).

## Development

```sh
cd cli
uv run pytest        # the suite — golden tests run against ../examples/crazy-ones
uv run fusion check ../examples/crazy-ones
```
