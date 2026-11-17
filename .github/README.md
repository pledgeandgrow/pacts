<p align="center">
  <a href="https://github.com/pledgeandgrow/fid">
    <img src="https://raw.githubusercontent.com/pledgeandgrow/fid/main/docs/fid-logo.svg" alt="Fid" width="88">
  </a>
</p>

<h1 align="center">pacts</h1>

<p align="center">
  <b>The package index of the <a href="https://github.com/pledgeandgrow/fid">Fid</a> language.</b><br>
  <code>fid ark</code> reads it to find, add and install pacts, as cargo reads the crates.io index.
</p>

<p align="center">
  <a href="https://github.com/pledgeandgrow/pacts/actions/workflows/check.yml"><img alt="index check" src="https://github.com/pledgeandgrow/pacts/actions/workflows/check.yml/badge.svg"></a>
  <a href="https://github.com/pledgeandgrow/fid/blob/main/docs/reference/ark.md"><img alt="ark docs" src="https://img.shields.io/badge/read-the%20ark%20docs-262626"></a>
  <a href="CONTRIBUTING.md"><img alt="publish a pact" src="https://img.shields.io/badge/publish-a%20pact-C2255C"></a>
</p>

<p align="center">
  <a href="#use-a-pact">Use a pact</a> ·
  <a href="#publish-a-pact">Publish a pact</a> ·
  <a href="#how-the-index-works">How it works</a> ·
  <a href="#the-rules">The rules</a> ·
  <a href="#report-a-problem">Report a problem</a>
</p>

---

A **pact** is a Fid package: a public git repository with an `ark.toml`
and `.fd` sources. This repository holds **no code**. For each pact it
records where the code lives and which commit each version is, and ark
refuses to install a version whose tag has moved.

## Use a pact

```bash
fid ark search json                  # pacts whose name holds "json"
fid ark add textkit --version ^1.2   # writes textkit = "^1.2" in ark.toml
fid ark install                      # installs it; ark.lock records the commit
```

```fid
// textkit is an example name
use textkit;

fn main() {
    println(textkit_title("hello pacts"));
}
```

Version specs are `1.2.3`, `^1.2`, `~1.2.3`, `>=1.0, <2.0`, `1.x` and `*`.
ark keeps a copy of this index in `<ARK_HOME or your home>/.ark/index`,
pulls it before each lookup, and still answers offline from the copy it
has.

## Publish a pact

```bash
git tag v1.2.0 && git push origin v1.2.0   # tag the version in your pact's repository
fid ark publish                            # checks it, then adds its line to the index
```

ark refuses a version that is already published, and a minor or patch
version that removes or changes the public API of the release before it.
Without write access here, the commit waits in your copy of the index and
you open a pull request with it. The **check** workflow verifies it and a
maintainer merges it.

The whole guide, including writing the line by hand: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## How the index works

One file per pact, at the top of the repository, named as the pact. One
line per version:

```
<version> <git-url> <tag> <commit> [yanked]
```

For example, a file `textkit` (the commits are illustrative):

```
1.0.0 https://github.com/you/textkit.git v1.0.0 4f1c2a9e0b7d3c5e8a6f1b2d4c7e9a0b3d5f7e1c
1.2.0 https://github.com/you/textkit.git v1.2.0 9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d
```

| Path | What it is |
|---|---|
| `<pact>` (top level) | A pact's versions, one per line |
| [`.github/owners`](https://github.com/pledgeandgrow/pacts/blob/owners/.github/owners) on the `owners` branch | Who may publish and yank each pact. Written by the **owners** workflow after a merge |
| [`.github/reserved`](reserved) | Names no pact may take: the standard library's modules and the project's own names |
| [`.github/scripts/check.py`](scripts/check.py) | The check every pull request must pass, run from `main`'s copy |
| [`.github/workflows/`](workflows) | `check` (pull requests) and `owners` (after a merge) |

Files and directories starting with `.` are not pacts, so everything else
lives in `.github/`. `main` takes changes only through pull requests that
pass the check. The owners list is kept on its own `owners` branch, so that
the owners workflow can record new owners without a pull request.

## The rules

- **Versions never change.** A merged line is never edited or removed. To
  withdraw a version, yank it (`fid ark yank 1.2.0`). A yanked version is
  never chosen for a new lock; projects whose `ark.lock` already has it
  keep it, with a warning.
- **The tag is the version.** The tag is `v<version>`, and the commit is
  the full 40-character hash it points at. The repository at that commit
  has an `ark.toml` with this name and version.
- **Owners publish.** Whoever publishes a pact's first version owns it.
  Only an owner may publish or yank later versions.
- **Names are protected.** Standard library module names are reserved, so
  `use json` is never ambiguous. A name one edit away from an existing
  pact (`jsno` next to `json`) needs a maintainer.
- **One repository per pact.** Every version comes from the same
  repository; moving it needs a maintainer.

## Report a problem

- A pact that is malicious, impersonates another project, or squats a
  name: see [SECURITY.md](SECURITY.md) (malicious code is reported
  privately).
- A name, ownership or index question:
  [open an issue](https://github.com/pledgeandgrow/pacts/issues/new/choose).
- A bug in `fid ark` itself: the [Fid repository](https://github.com/pledgeandgrow/fid/issues).

## Another index

`ARK_INDEX=<git url>` makes ark read another index, for a company's own
pacts or a mirror. Any git host works, with the same layout.

<sub>The index lists pacts; it does not relicense them. Each pact has its
own licence, named in its `ark.toml`.</sub>
