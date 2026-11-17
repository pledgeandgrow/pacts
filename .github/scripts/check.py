#!/usr/bin/env python3
"""Check a change to the pacts index (a pull request) before it is merged.

The index is the list `fid ark` reads: one file per pact at the top of the
repository, named as the pact, one line per version:

    <version> <git-url> <tag> <commit> [yanked]

Usage:
    check.py --base <rev> --head <rev> --author <login> [--maintainer]
             [--offline] [--allow-local]

--maintainer  the author may change .github/, remove or rename pacts, take
              a name one edit away from another, and publish without being
              an owner.
--offline     skip the checks that reach the pact's repository.
--allow-local accept git URLs that are local paths (tests only).
--owners-ref  where .github/owners is read (default origin/owners, the
              branch the owners workflow writes; else --base).

Exit status 0 when every check passes; otherwise each problem is printed
(as a GitHub annotation when run in Actions) and the status is 1.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
VERSION_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
URL_RE = re.compile(r"^https://[A-Za-z0-9.-]+(:[0-9]+)?/[A-Za-z0-9._~/-]+$")

errors = []
notes = []


def error(path, msg):
    errors.append((path, msg))


def git(*args, cwd=None, check=True):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    if "GIT_ALLOW_PROTOCOL" not in env:
        env["GIT_ALLOW_PROTOCOL"] = "https:file" if ALLOW_LOCAL else "https"
    r = subprocess.run(["git", *args], cwd=cwd, env=env,
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("git %s: %s" % (" ".join(args), r.stderr.strip()))
    return r


def show(rev, path):
    """The file at `rev`, or None when it does not exist there."""
    r = git("show", "%s:%s" % (rev, path), check=False)
    if r.returncode != 0:
        return None
    return r.stdout


def top_names(rev):
    """The pacts at `rev`: files at the top level not starting with '.'."""
    out = git("ls-tree", "--name-only", rev).stdout.split("\n")
    names = []
    for n in out:
        n = n.strip()
        if n and not n.startswith("."):
            names.append(n)
    return names


def read_list(rev, path):
    text = show(rev, path) or ""
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def owners_rev(owners_ref, base):
    """Where the owners file is read: the `owners` branch (the owners
    workflow writes it there, as main requires pull requests), else the
    base revision (an index that keeps it on main)."""
    if owners_ref and git("rev-parse", "--verify", "-q", owners_ref + "^{commit}",
                          check=False).returncode == 0             and show(owners_ref, ".github/owners") is not None:
        return owners_ref
    return base


def owners_at(rev):
    owners = {}
    for line in read_list(rev, ".github/owners"):
        f = line.split()
        owners[f[0]] = [x.lower() for x in f[1:]]
    return owners


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        cur = [i + 1]
        for j, cb in enumerate(b):
            cur.append(min(prev[j + 1] + 1, cur[j] + 1,
                           prev[j] + (0 if ca == cb else 1)))
        prev = cur
    return prev[len(b)]


def lines_of(text):
    """The non-empty lines of an index file; errors for CR and blanks."""
    return [l for l in text.split("\n") if l != ""]


def parse_line(line):
    f = line.split(" ")
    if len(f) == 4:
        return f, False
    if len(f) == 5 and f[4] == "yanked":
        return f[:4], True
    return None, False


def toml_package(text):
    """name and version of [package] in an ark.toml (a small reader)."""
    section = ""
    found = {}
    key = re.compile(r'^(name|version)\s*=\s*"([^"]*)"')
    for raw in text.split("\n"):
        line = raw.strip()
        if line.startswith("[") and "]" in line:
            section = line[1:line.index("]")].strip()
            continue
        m = key.match(line)
        if section == "package" and m:
            found.setdefault(m.group(1), m.group(2))
    return found.get("name"), found.get("version")


def check_remote(name, version, url, tag, commit):
    """The tag is in the repository at `commit`, and the pact there is
    `name` `version` with Fid sources."""
    r = git("ls-remote", url, "refs/tags/" + tag, "refs/tags/" + tag + "^{}",
            check=False)
    if r.returncode != 0:
        error(name, "%s: cannot read %s (%s)" % (version, url, r.stderr.strip()[:200]))
        return
    direct = peeled = None
    for line in r.stdout.split("\n"):
        parts = line.split()
        if len(parts) != 2:
            continue
        if parts[1].endswith("^{}"):
            peeled = parts[0]
        else:
            direct = parts[0]
    at = peeled or direct
    if at is None:
        error(name, "%s: %s has no tag %s" % (version, url, tag))
        return
    if at != commit:
        error(name, "%s: the tag %s is at %s, not %s" % (version, tag, at, commit))
        return
    tmp = tempfile.mkdtemp(prefix="pact-")
    try:
        git("init", "-q", tmp)
        f = git("fetch", "-q", "--depth", "1", url, commit, cwd=tmp, check=False)
        if f.returncode != 0:
            # servers that refuse a fetch by commit: fetch the tag
            f = git("fetch", "-q", "--depth", "1", url,
                    "refs/tags/%s:refs/tags/%s" % (tag, tag), cwd=tmp, check=False)
        if f.returncode != 0:
            error(name, "%s: cannot fetch %s from %s" % (version, commit, url))
            return
        git("checkout", "-q", commit, cwd=tmp)
        toml = os.path.join(tmp, "ark.toml")
        if not os.path.isfile(toml):
            error(name, "%s: no ark.toml at the top of %s at %s" % (version, url, tag))
            return
        with open(toml, encoding="utf-8", errors="replace") as fh:
            pname, pversion = toml_package(fh.read())
        if pname != name:
            error(name, "%s: ark.toml names the package %r, not %r" % (version, pname, name))
        if pversion != version:
            error(name, "%s: ark.toml's version is %r, not %r" % (version, pversion, version))
        has_fd = False
        for root, dirs, files in os.walk(tmp):
            if ".git" in dirs:
                dirs.remove(".git")
            if any(x.endswith(".fd") for x in files):
                has_fd = True
                break
        if not has_fd:
            error(name, "%s: no .fd source at %s" % (version, tag))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_pact(name, status, args, owners, existing, reserved):
    old_text = show(args.base, name) if status != "A" else None
    new_text = show(args.head, name)
    is_new = old_text is None

    if status == "D" or new_text is None:
        if not args.maintainer:
            error(name, "a pact is never removed (yank its versions instead)")
        return
    if not NAME_RE.match(name):
        error(name, "a pact's name is a lowercase letter, then lowercase letters, digits or _ (at most 64)")
        return
    if "\r" in new_text:
        error(name, "the file has CR line endings; use LF")
        return
    if is_new:
        if name in reserved:
            error(name, "'%s' is reserved (a standard library module or a name of the project)" % name)
        near = [n for n in existing if n != name and edit_distance(n, name) == 1]
        if near and not args.maintainer:
            error(name, "'%s' is one edit away from %s: a maintainer must approve a name this close" % (name, ", ".join(near)))
    else:
        listed = owners.get(name)
        if not args.maintainer:
            if listed is None:
                error(name, "the pact has no owners entry: a maintainer must review this change")
            elif args.author.lower() not in listed:
                error(name, "%s is not an owner of '%s' (owners: %s)" % (args.author, name, ", ".join(listed)))

    old = lines_of(old_text or "")
    new = lines_of(new_text)
    if len(new) < len(old):
        error(name, "versions are never removed (yank them instead)")
        return
    versions = {}
    git_url = None
    for i, line in enumerate(old):
        f, _ = parse_line(line)
        if f:
            versions[f[0]] = True
            git_url = f[1]
        n = new[i]
        if n == line:
            continue
        if n == line + " yanked":
            notes.append("%s %s: yanked" % (name, f[0] if f else "?"))
            continue
        if line.endswith(" yanked") and n == line[: -len(" yanked")]:
            notes.append("%s %s: yank undone" % (name, f[0] if f else "?"))
            continue
        error(name, "line %d changed; a published version never changes (only ' yanked' may be added or removed)" % (i + 1))
    added = new[len(old):]
    if not added:
        return
    for line in added:
        f, yanked = parse_line(line)
        if f is None or yanked:
            error(name, "%r: a new line is `<version> <git-url> <tag> <commit>`, single spaces" % line)
            continue
        version, url, tag, commit = f
        if not VERSION_RE.match(version):
            error(name, "%s: not a version (major.minor.patch, optional -pre)" % version)
            continue
        if version in versions:
            error(name, "%s is already published; versions never change" % version)
            continue
        versions[version] = True
        if tag != "v" + version:
            error(name, "%s: the tag must be v%s, not %s" % (version, version, tag))
        if not COMMIT_RE.match(commit):
            error(name, "%s: the commit must be a full 40-character lowercase hash" % version)
        local = args.allow_local and "://" not in url
        if not local and not URL_RE.match(url):
            error(name, "%s: the git URL must be https://host/path with no credentials" % version)
            continue
        if git_url is not None and url != git_url and not args.maintainer:
            error(name, "%s: the repository changed from %s to %s: a maintainer must approve" % (version, git_url, url))
        git_url = url
        if not args.offline and COMMIT_RE.match(commit) and tag == "v" + version:
            check_remote(name, version, url, tag, commit)
        notes.append("%s %s: %s at %s" % (name, version, url, commit[:12]))


def main():
    global ALLOW_LOCAL
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--author", required=True)
    ap.add_argument("--maintainer", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--allow-local", action="store_true")
    ap.add_argument("--owners-ref", default="origin/owners",
                    help="the revision whose .github/owners lists the owners")
    args = ap.parse_args()
    ALLOW_LOCAL = args.allow_local

    owners = owners_at(owners_rev(args.owners_ref, args.base))
    reserved = set(read_list(args.base, ".github/reserved"))
    existing = top_names(args.base)
    diff = git("diff", "--name-status", "--no-renames", args.base, args.head).stdout
    changed = 0
    for line in diff.split("\n"):
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        status = status[0]
        changed += 1
        if path.startswith(".github/") or path.startswith("."):
            if not args.maintainer:
                error(path, "only a maintainer changes %s (a pull request publishes or yanks pact versions only)" % path)
            continue
        if "/" in path:
            error(path, "a pact is one file at the top of the repository")
            continue
        check_pact(path, status, args, owners, existing, reserved)
    if changed == 0:
        notes.append("nothing changed")

    gh = os.environ.get("GITHUB_ACTIONS") == "true"
    for n in notes:
        print("ok: " + n)
    for path, msg in errors:
        if gh:
            print("::error file=%s::%s" % (path, msg))
        else:
            print("error: %s: %s" % (path, msg))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("## Index check\n\n")
            for n in notes:
                fh.write("- ok: %s\n" % n)
            for path, msg in errors:
                fh.write("- **error** `%s`: %s\n" % (path, msg))
            if not errors:
                fh.write("\nEvery check passed.\n")
    return 1 if errors else 0


ALLOW_LOCAL = False

if __name__ == "__main__":
    sys.exit(main())
