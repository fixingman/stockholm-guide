#!/usr/bin/env bash
# Publish ONLY previously validated, public newsletter artifacts to a dedicated
# GitHub branch. Never stores recipient data or sends email.
set -euo pipefail
source_dir="${1:?Usage: publish_verified_release.sh RELEASE_DIR production|smoke}"
channel="${2:?channel required}"
case "$channel" in production) branch="validated-sunday";; smoke) branch="validated-sunday-smoke";; *) echo "Invalid channel" >&2; exit 2;; esac
test -f "$source_dir/outgoing.html"
test -f "$source_dir/delivery-manifest.json"
test -f "$source_dir/issue.json"
tmp="$(mktemp -d)"
cp "$source_dir/outgoing.html" "$source_dir/delivery-manifest.json" "$source_dir/issue.json" "$tmp/"
[ ! -f "$source_dir/client-qa.json" ] || cp "$source_dir/client-qa.json" "$tmp/"
python - "$tmp" "$channel" <<'PY'
import hashlib,json,sys,os
from pathlib import Path
path=Path(sys.argv[1]);channel=sys.argv[2]
m=json.loads((path/"delivery-manifest.json").read_text())
assert m["ready_for_delivery"] is True, "Release must be validated"
issue=json.loads((path/"issue.json").read_text())
assert m["issue_number"] == issue["issue_number"] and m["date_range"] == issue["date_range"]
content=(path/"outgoing.html").read_text()
from hashlib import sha256
# Same MIME-newline normalization as delivery_guard.html_digest.
actual=sha256(content.replace("\r\n","\n").rstrip("\n").encode()).hexdigest()
assert actual == m["html_sha256"], "HTML differs from delivery manifest"
if channel=="production":
    assert m.get("editorial_quality",{}).get("ready_for_editorial_release"), "Strict editorial gate missing"
    assert m.get("freshness",{}).get("ready_for_send"), "Freshness gate missing"
    assert len(m.get("image_checks",[])) == len(m.get("featured_images",[])), "Live image checks missing"
else:
    m["smoke_test_only"]=True
m["release_channel"]=channel
m["source_commit_sha"]=os.environ.get("GITHUB_SHA","unknown")
(path/"delivery-manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
print("Validated release",channel,issue["issue_number"],actual)
PY

rm -rf "$source_dir" # avoid untracked artifacts conflicting with release branch checkout

git config user.name "stockholm-guide-release-bot"
git config user.email "stockholm-guide-release-bot@users.noreply.github.com"
# An independent branch avoids races with the main branch's Pages deployment.
if git ls-remote --exit-code --heads origin "$branch" >/dev/null; then
    git fetch origin "$branch"
    git checkout -B "$branch" "FETCH_HEAD"
else
    git checkout --orphan "$branch"
fi
# Release branches intentionally contain ONLY verified public artifacts, never
# the source repository, test fixture, or stray files.
git rm -rf . >/dev/null 2>&1 || true
git clean -fdx >/dev/null 2>&1 || true
mkdir -p verified
cp "$tmp/"* verified/
printf 'This branch contains validated newsletter editorial artifacts only. Never put recipients here.\n' > README.md
git add -A
if ! git diff --cached --quiet; then
    git commit -m "Publish validated $channel issue [skip ci]"
    git push origin "HEAD:refs/heads/$branch"
fi
echo "VALIDATED_BRANCH=$branch"
echo "VALIDATED_COMMIT=$(git rev-parse HEAD)"
