#!/usr/bin/env bash
set -u
TP3="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$TP3/pids.txt" ]]; then
  while read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < "$TP3/pids.txt"
  rm -f "$TP3/pids.txt"
fi
echo "Services TP3 arrêtés."
