#!/usr/bin/env python3
"""Give each new pact an owner: the author of the pull request that added
it (or, for a direct push, the person who pushed).

Run in a checkout of main after a merge. The owners file lives on the
`owners` branch (main requires pull requests and the check, which the
workflow's token cannot bypass); --owners is its path in a checkout of
that branch. Prints the pacts it recorded; the workflow commits the change
there. Needs `gh` (GH_TOKEN) to find the pull request of a commit;
without it, the pusher (--pusher) is the owner.
"""

import argparse
import json
import os
import subprocess
import sys


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True)


def pr_author(repo, sha):
    r = run("gh", "api", "repos/%s/commits/%s/pulls" % (repo, sha))
    if r.returncode != 0:
        return None
    try:
        pulls = json.loads(r.stdout)
    except ValueError:
        return None
    for p in pulls:
        if p.get("merged_at") and p.get("user"):
            return p["user"]["login"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    ap.add_argument("--pusher", required=True)
    ap.add_argument("--owners", default=os.path.join(".github", "owners"),
                    help="the owners file to read and extend")
    args = ap.parse_args()

    path = args.owners
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    known = set()
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            known.add(line.split()[0])

    added = []
    for name in sorted(os.listdir(".")):
        if name.startswith(".") or not os.path.isfile(name) or name in known:
            continue
        first = run("git", "log", "--diff-filter=A", "--format=%H", "--", name)
        shas = [s for s in first.stdout.split("\n") if s.strip()]
        owner = None
        if shas and args.repo:
            owner = pr_author(args.repo, shas[-1])
        if not owner:
            owner = args.pusher
        added.append("%s %s" % (name, owner))

    if not added:
        print("every pact has an owner")
        return 0
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n".join(added) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    for a in added:
        print("owner recorded: " + a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
