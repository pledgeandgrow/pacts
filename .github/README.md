# pacts

The index of **pacts**, the packages of the [Fid](https://github.com/pledgeandgrow/fid)
language. `fid ark` reads it to find, add and install pacts. It is to ark
what the crates.io index is to cargo.

The index holds no code. Each pact's code stays in its own git repository;
the index records where it is and which commit each version is, and ark
refuses to install a version whose tag has moved.

## Using pacts

```bash
fid ark search json            # pacts whose name holds "json"
fid ark add textkit --version ^1.2
fid ark install
```

`fid ark add <name> --version <spec>` writes `name = "<spec>"` in ark.toml's
`[dependencies]`; ark.lock records the commit installed. Version specs:
`1.2.3`, `^1.2`, `~1.2.3`, `>=1.0, <2.0`, `1.x`, `*`
(docs/reference/ark.md in the Fid repository).

ark keeps a copy of the index in `<ARK_HOME or your home>/.ark/index` and
pulls it before each lookup. Offline, the copy it has still answers.

## Publishing a pact

1. Your pact is a git repository with an `ark.toml` at its top:

   ```toml
   [package]
   name = "textkit"
   version = "1.2.0"
   description = "Text utilities"
   license = "MIT"
   ```

   and its `.fd` sources. The repository must be public and reachable over
   `https://`.

2. Tag the version and push the tag:

   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

3. Publish:

   ```bash
   fid ark publish
   ```

   ark checks the tag, refuses a version that is already published, and
   refuses a minor or patch version that removes or changes the public API
   of the release before it. It then adds the version's line to its copy of
   the index and commits it.

4. Open a pull request with that commit. Without write access to this
   repository the push fails, and the commit waits in your copy of the
   index (`~/.ark/index`):

   ```bash
   cd ~/.ark/index
   gh repo fork --remote --remote-name fork   # once
   git push fork HEAD:publish-textkit-1.2.0
   gh pr create --title "textkit 1.2.0" --body "" --head <you>:publish-textkit-1.2.0
   ```

   Then reset your copy to the index (`git reset --hard origin/main`, or
   delete `~/.ark/index` and let ark clone it again).

   Or write the line yourself: in your fork, append to the file named as
   your pact (create it for a first version)

   ```
   1.2.0 https://github.com/you/textkit.git v1.2.0 <full 40-character commit of v1.2.0>
   ```

   (`git rev-parse v1.2.0^{commit}` prints the commit).

The **check** workflow verifies every pull request; a maintainer merges it.

## The rules

- **One file per pact**, at the top of this repository, named as the pact.
  Names are a lowercase letter, then lowercase letters, digits and `_`, at
  most 64 characters. Files and directories starting with `.` are not pacts.
- **One line per version**: `<version> <git-url> <tag> <commit>`, single
  spaces, LF line endings. The version is `major.minor.patch` with an
  optional `-pre`; the tag is `v<version>`; the commit is the full hash the
  tag points at; the URL is `https://` with no credentials.
- **Versions never change.** A line, once merged, is never edited or
  removed. To withdraw a version, yank it: `fid ark yank 1.2.0` adds
  ` yanked` to the end of its line (`--undo` removes it). A yanked version
  is never chosen for a new lock; projects whose ark.lock already has it
  keep it, with a warning.
- **Owners.** Whoever publishes a pact's first version becomes its owner
  (`.github/owners`, written after the merge). Only an owner may publish or
  yank later versions. A maintainer adds or changes owners.
- **Reserved names.** The standard library's modules (`json`, `http`, ...)
  and the project's own names (`.github/reserved`) cannot be taken: `use
  json` must not be ambiguous.
- **Lookalike names.** A new name one edit away from an existing pact
  (`jsno` next to `json`) needs a maintainer's approval.
- **One repository per pact.** Every version comes from the same
  repository; moving it needs a maintainer.

## What the check verifies

`.github/scripts/check.py`, run from the base branch on every pull request:

- only pact files change (`.github/` is for maintainers);
- the name is valid, not reserved, not a lookalike;
- the author owns the pact (for a pact that already exists);
- existing lines are unchanged except for ` yanked`;
- each new line is well formed, its version new, its tag `v<version>`;
- the tag exists in the repository and points at the commit;
- the repository at that commit has an `ark.toml` naming this pact and this
  version, and `.fd` sources.

Run it yourself before opening a pull request:

```bash
python3 .github/scripts/check.py --base origin/main --head HEAD --author <you>
```

## Another index

`ARK_INDEX=<git url>` makes ark read another index, for a company's own
pacts or a mirror. Any git host works; the layout is the one above.
