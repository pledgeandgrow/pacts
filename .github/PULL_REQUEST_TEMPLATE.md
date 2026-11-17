<!-- A pull request here publishes or yanks versions of a pact. The title: "<pact> <version>" (or "<pact> <version> yanked"). -->

**Pact:**
**Version(s):**
**Repository:**

- [ ] The tag `v<version>` is pushed and points at the commit on the line
- [ ] `ark.toml` at that commit has this name and this version
- [ ] Only this pact's file changes, and existing lines are unchanged (apart from ` yanked`)
- [ ] `python3 .github/scripts/check.py --base origin/main --head HEAD --author <me>` passes

<!-- First version of a new pact? Say in one line what it does. -->
