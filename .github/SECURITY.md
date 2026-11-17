# Security

## Report a malicious pact

If a pact in this index contains malicious code (it steals data, opens a
backdoor, or runs something on install or build), or impersonates another
project, **do not open a public issue**. Report it privately:

**[Report a vulnerability](https://github.com/pledgeandgrow/pacts/security/advisories/new)**
(GitHub's private reporting)

Include the pact's name, the affected versions, and what the code does
(a file and line, or a commit). Once confirmed, maintainers yank every
affected version, and remove the owner's rights if the owner is behind
it.

## A vulnerability in a pact

A security bug in a pact that is not malicious goes to the pact's own
repository (its URL is in the pact's file here). If the owner does not
answer, report it as above: maintainers can yank the affected versions.

## A vulnerability in ark or this index

A weakness in `fid ark` itself (the tag check, the lock, the capability
check) goes to the
[Fid repository's security policy](https://github.com/pledgeandgrow/fid/security/policy).
A weakness in this index's rules or scripts (`.github/scripts/check.py`, the
workflows) is reported here, privately, as above.

## What the index already protects against

- **A moved tag.** Each version records the commit its tag pointed at when
  it was published. ark refuses to install a version whose tag has moved
  off that commit.
- **A changed version.** A published line can never be edited or removed;
  the check refuses such a pull request.
- **A takeover.** Only a pact's owners can publish or yank its versions.
- **Lookalike names** (`jsno` next to `json`) need a maintainer.
- **Shadowing the standard library.** Its module names are
  [reserved](reserved).

What the index does not do: review the code of pacts. Read what you
install, and use `fid ark audit` and `[capabilities]` to see and limit what
each pact may use.
