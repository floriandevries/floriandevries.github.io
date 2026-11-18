#!/usr/bin/env bash
set -euo pipefail

repo_args=()
if [[ $# -ge 1 ]]; then
  repo_args=(--repo "$1")
fi

create() {
  gh label create "$1" --color "$2" --description "$3" --force "${repo_args[@]}"
}

create idea "0E8A16" "Blog post idea captured from an issue"
create scout "1D76DB" "Scout run output: candidate topics"
create this-week "5319E7" "Selected for this week's push"
create lookback "FBCA04" "Monthly look-back review"
create nudged "D93F0B" "Owner already nudged about this item"
create workflow-failure "B60205" "A Claude workflow run failed"
