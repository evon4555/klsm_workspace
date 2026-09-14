#!/usr/bin/env sh
set -eu

if [ -n "${QA_WESTK_ROOT:-}" ]; then
  target="$QA_WESTK_ROOT/02-automation/04-tools/full_flow.sh"
else
  target="/d/Workspace/west-kowloon/02-automation/04-tools/full_flow.sh"
fi

exec "$target" "$@"
