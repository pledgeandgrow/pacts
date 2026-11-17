# Publishing a pact

A pull request to this repository publishes a version of a pact, or yanks
one. Nothing else changes through pull requests: `.github/` is for
maintainers.

- [Before you publish](#before-you-publish)
- [Publish with ark](#publish-with-ark)
- [Or write the line yourself](#or-write-the-line-yourself)
- [Check before you open the pull request](#check-before-you-open-the-pull-request)
- [Yank a version](#yank-a-version)
- [Names](#names)
- [Ownership](#ownership)
- [For maintainers](#for-maintainers)

## Before you publish

Your pact is a public git repository, reachable over `https://`, with an
`ark.toml` at its top and its `.fd` sources:

```toml
[package]
name = "textkit"
version = "1.2.0"
description = "Text utilities"
license = "MIT"
```

- `name` is the pact's name in the index: a lowercase letter, then
  lowercase letters, digits or `_`, at most 64 characters. It must not be
  [reserved](reserved).
- `version` is `major.minor.patch`, with an optional `-pre` (`1.2.0-rc.1`).
- `description` and `license` are shown by `fid ark search`. Name an
  [SPDX licence](https://spdx.org/licenses/).

Worth doing before a first release: a README in the pact's repository, a
test (`fid ark test`), and `[capabilities]` in `ark.toml` stating what the
pact may use. ark shows those to the projects that install it
([docs](https://github.com/pledgeandgrow/fid/blob/main/docs/reference/ark.md#capabilities-of-each-dependency-cd1)).

## Publish with ark

1. Tag the version and push the tag:

   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

2. Publish:

   ```bash
   fid ark publish
   ```

   ark checks the tag, and refuses a version that is already published. It
   also refuses a minor or patch version that removes or changes the
   public API of the release before it (`fid ark api --against v1.1.0`
   shows what changed). It then adds the version's line to its copy of
   the index and commits it.

3. Open a pull request with that commit. Without write access to this
   repository the push fails, and the commit waits in your copy of the
   index (`~/.ark/index`):

   ```bash
   cd ~/.ark/index
   gh repo fork --remote --remote-name fork   # once
   git push fork HEAD:publish-textkit-1.2.0
   gh pr create --title "textkit 1.2.0" --body "" --head <you>:publish-textkit-1.2.0
   ```

   Then reset your copy to the index: `git reset --hard origin/main`, or
   delete `~/.ark/index` and let ark clone it again.

## Or write the line yourself

In your fork of this repository, append one line to the file named as your
pact (create the file for a first version):

```
1.2.0 https://github.com/you/textkit.git v1.2.0 <full 40-character commit of v1.2.0>
```

`git rev-parse v1.2.0^{commit}` prints the commit. Use single spaces and LF
line endings, and leave every existing line as it is.

## Check before you open the pull request

The **check** workflow runs `main`'s copy of
[`scripts/check.py`](scripts/check.py) on every pull request. Run it
yourself first:

```bash
python3 .github/scripts/check.py --base origin/main --head HEAD --author <your-github-login>
```

It verifies that:

- only pact files change;
- the name is valid, not reserved, and not one edit away from another pact;
- you own the pact, when it already exists;
- existing lines are unchanged, apart from ` yanked`;
- each new line is well formed, its version is new, and its tag is
  `v<version>`;
- the tag exists in the repository and points at the commit;
- the repository at that commit has an `ark.toml` naming this pact and this
  version, and `.fd` sources.

A pull request that passes is merged by a maintainer.

## Yank a version

```bash
fid ark yank 1.2.0          # adds " yanked" to the end of 1.2.0's line
fid ark yank 1.2.0 --undo   # removes it
```

Then open a pull request as for a publish. A yanked version is never chosen
for a new lock. Projects whose `ark.lock` already records it keep it, with
a warning, until `fid ark update`. Lines are never removed, and a yanked
version number cannot be published again. Yank a version that is broken or
unsafe, and publish a fixed one.

## Names

- **First come, first served**, for names that are not reserved.
- **Reserved names** ([`reserved`](reserved)) are the standard library's
  modules and the project's own names. A pact named like a standard module
  would make `use <name>` ambiguous.
- **Lookalikes**: a new name one edit away from an existing pact (`jsno`
  next to `json`) needs a maintainer's approval.
- **Squatting**: if a name is taken with no real pact behind it (a
  placeholder), say so in an issue. Maintainers decide case by case.

## Ownership

Whoever publishes a pact's first version becomes its owner. The **owners**
workflow writes them to [`owners`](owners) after the merge. Only an owner may
publish or yank later versions.

To add an owner, or to hand a pact over, open an issue
([ownership form](https://github.com/pledgeandgrow/pacts/issues/new?template=ownership.yml))
from an existing owner's account. A maintainer changes `owners`.

## For maintainers

- Merge only pull requests whose **check** passed. Changes to `.github/`
  (rules, scripts, workflows) go through a pull request too, so the check
  and the history show them.
- Approve a lookalike name, or a pact that moves to another repository,
  only after confirming with the owner.
- For a malicious pact: yank every version (`fid ark yank`, with the
  `--package` option), record the decision in the issue, and remove the
  owners entry. Lines stay in the index, so that `ark.lock` files can
  still explain what they hold.
- Keep [`reserved`](reserved) in step with the standard library: every new
  `stdlib/<name>.fd` in the Fid repository is a reserved name here.
