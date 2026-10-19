#!/usr/bin/env bash
# Container smoke test for V_citations (upgrade safety net, see TESTING.md).
# Runs the BUILT image, then: index page, a real CSV upload -> .docx download, non-CSV rejected,
# and no Python traceback in the logs.
#
#   docker build -t citations:smoke V_citations && bash scripts/smoke.sh citations:smoke
#
# Hardening: cap_drop ALL + no-new-privileges. Not --read-only / non-root: the app writes
# ./export.csv and ./generated_citation.docx into / (see TESTING.md, "Known gaps").
set -euo pipefail

IMAGE="${1:-citations:smoke}"
NAME="citations-smoke-$$"
PORT="${SMOKE_PORT:-18451}"
BASE="http://127.0.0.1:${PORT}"
TMP="$(mktemp -d)"
cd "$TMP" # fixtures are referenced by relative name (portable curl -F)

dk() { MSYS_NO_PATHCONV=1 docker "$@"; }  # Git Bash on Windows rewrites /paths in args
cleanup() {
  cd /
  if [ "${SMOKE_OK:-0}" != 1 ]; then echo "---- container log ----"; dk logs "$NAME" 2>&1 | tail -n 40 || true; fi
  dk rm -f "$NAME" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT
fail() { echo "SMOKE FAIL: $*" >&2; exit 1; }
step() { echo "== $*"; }
code() { # code <expected> <curl args...>   body saved to body.out
  local want="$1"; shift
  local got
  got="$(curl -sS -o body.out -w '%{http_code}' "$@")"
  [ "$got" = "$want" ] || { head -c 300 body.out >&2; fail "expected $want got $got for: $*"; }
}

step "start $IMAGE (cap_drop ALL, no-new-privileges)"
dk run -d --name "$NAME" --cap-drop ALL --security-opt no-new-privileges:true \
  -e PORT=6451 -p "127.0.0.1:${PORT}:6451" "$IMAGE" >/dev/null
for _ in $(seq 1 60); do
  curl -fsS -o /dev/null "$BASE/" 2>/dev/null && break
  [ "$(dk inspect --format '{{.State.Running}}' "$NAME")" = true ] || fail "container exited"
  sleep 1
done

step "index page"
code 200 "$BASE/"
grep -qi 'upload' body.out || fail "index has no upload form"

step "CSV upload -> Word document"
{
  echo 'handleId,name,collection,productOptionDescription2,productOptionDescription3,additionalInfoDescription2,additionalInfoDescription3,additionalInfoDescription4,additionalInfoDescription5'
  echo '1,composition viii,wassily kandinsky,1923,Paris,Service photo,Huile sur toile,140 X 201 CM,Guggenheim'
} >export.csv
code 200 -F "export=@export.csv;type=text/csv" "$BASE/upload"
[ "$(head -c 2 body.out)" = PK ] || fail "not a .docx (zip) file"

step "non-CSV rejected"
echo hello >note.txt
code 400 -F "export=@note.txt;type=text/plain" "$BASE/upload"

step "no tracebacks in logs"
if dk logs "$NAME" 2>&1 | grep -E 'Traceback'; then fail "traceback in container log"; fi

SMOKE_OK=1
echo "SMOKE OK ($IMAGE)"
