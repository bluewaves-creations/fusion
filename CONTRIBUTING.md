# Contributing

The spec is the contribution. Fusion is a convention first
([SPEC.md](SPEC.md)); the CLI and skills in this repository are reference
implementations. That shapes what contributing means here:

## Amend the convention

SPEC.md changes rarely, and only through a versioned change: open an issue
stating the problem the current convention causes (real usage evidence
beats taste), the amendment lands with a version bump and a line in the
spec's history. Vocabulary sets (auroras, ledger verbs, error codes) are
closed on purpose — the bar for widening them is high.

## Improve the reference tools

Bug fixes and capability work on the CLI (`cli/`) and skills (`skills/`)
are welcome as pull requests. House rules: TDD (the suites are the spec's
teeth), `fusion check examples/crazy-ones` stays at zero errors and zero
warnings, the four `references/fusion-conventions.md` stay byte-identical,
and single-writer registers are never hand-edited — not even in tests.

## Rewrite it entirely

The intended fork: reimplement the tools in any language you like. Buckets
that follow the convention are Fusion, whether or not our tools ever touch
them. You don't need permission — but we'd love an issue telling us it
exists.
