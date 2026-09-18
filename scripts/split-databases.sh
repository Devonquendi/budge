#!/usr/bin/env bash
#
# Give the public demo and branch previews a database each, so neither of them
# writes into the one holding real rows.
#
# Needs a Neon login. Two ways, and the second is the reliable one:
#
#   npx neon@latest auth        browser sign in, times out after 60 seconds
#   export NEON_API_KEY=...     from Neon Console > Account settings > API keys
#
# The API key skips the browser entirely and does not expire mid-command.
#
# Safe to re-run. It skips a database that already exists, and it only touches
# DATABASE_URL and DATABASE_URL_UNPOOLED on the Vercel project this repo is
# linked to.

set -euo pipefail

NEON="npx -y neon@latest"
DEMO_DB="budge_demo"
PREVIEW_DB="budge_preview"

cd "$(dirname "$0")/.."

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

# ---------------------------------------------------------------- Neon side

say "Checking the Neon login"
if ! $NEON projects list -o json >/dev/null 2>&1; then
  cat <<'MSG'
Not signed in to Neon. Either works:

  1. An API key, which does not time out:
       Neon Console > Account settings > API keys > Create new API key
       export NEON_API_KEY=<the key>

  2. The browser flow, which gives you 60 seconds to finish signing in:
       npx neon@latest auth

Then run me again.
MSG
  exit 1
fi

PROJECT_ID=$($NEON projects list -o json | python3 -c '
import json, sys
projects = json.load(sys.stdin)
rows = projects.get("projects", projects) if isinstance(projects, dict) else projects
if len(rows) == 1:
    print(rows[0]["id"])
else:
    for row in rows:
        print(row["id"], row["name"], sep="\t", file=sys.stderr)
    raise SystemExit("More than one Neon project. Set PROJECT_ID by hand above.")
')
say "Neon project: $PROJECT_ID"

existing=$($NEON databases list --project-id "$PROJECT_ID" -o json | python3 -c '
import json, sys
print(" ".join(d["name"] for d in json.load(sys.stdin)))
')
echo "Databases now: $existing"

for db in "$DEMO_DB" "$PREVIEW_DB"; do
  if [[ " $existing " == *" $db "* ]]; then
    echo "  $db already there, leaving it alone"
  else
    say "Creating $db"
    $NEON databases create --project-id "$PROJECT_ID" --name "$db"
  fi
done

url_for() { $NEON connection-string --project-id "$PROJECT_ID" --database-name "$1" --pooled; }
direct_for() { $NEON connection-string --project-id "$PROJECT_ID" --database-name "$1"; }

DEMO_URL=$(url_for "$DEMO_DB")
DEMO_DIRECT=$(direct_for "$DEMO_DB")
PREVIEW_URL=$(url_for "$PREVIEW_DB")
PREVIEW_DIRECT=$(direct_for "$PREVIEW_DB")

# -------------------------------------------------------------- Vercel side
#
# Vercel holds one value per name per environment, so the existing entry has to
# go before a per-environment one can replace it. Production first, then
# preview, and a redeploy at the end: between the remove and the add the
# running deployment keeps the values it was built with, so nothing that is
# already live goes down while this runs.

say "Repointing Vercel at the new databases"

drop() { mise exec -- vercel env rm "$1" "$2" --yes >/dev/null 2>&1 || true; }
put() { printf '%s' "$3" | mise exec -- vercel env add "$1" "$2" >/dev/null; echo "  $1 -> $2"; }

for name in DATABASE_URL DATABASE_URL_UNPOOLED; do
  drop "$name" production
  drop "$name" preview
done

put DATABASE_URL production "$DEMO_URL"
put DATABASE_URL_UNPOOLED production "$DEMO_DIRECT"
put DATABASE_URL preview "$PREVIEW_URL"
put DATABASE_URL_UNPOOLED preview "$PREVIEW_DIRECT"

say "Done. Both databases are empty, so deploy to migrate them:"
cat <<'EOF'

    mise exec -- vercel deploy --prod     # the public demo
    mise exec -- vercel deploy            # a preview

The build step runs "python -m alembic upgrade head" against whichever
database it is building for, so the tables appear on their own.

Your original database still holds every row it did. Nothing here deleted
anything; the demo simply stops writing into it.
EOF
