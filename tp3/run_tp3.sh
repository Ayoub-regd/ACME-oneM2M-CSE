#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TP3="$ROOT/tp3"
cd "$ROOT"

echo "== R505 TP3 oneM2M / ACME =="
echo "Repository: $ROOT"

# 1) Environnement Python
if [[ ! -d "$ROOT/myenv" ]]; then
  echo "Création de myenv avec Python 3.12..."
  python3.12 -m venv myenv
fi
source "$ROOT/myenv/bin/activate"
python --version
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
python -m pip install -q requests flask

# Nettoyage d'anciens processus TP3 si présents
if [[ -f "$TP3/pids.txt" ]]; then
  while read -r pid; do
    kill "$pid" 2>/dev/null || true
  done < "$TP3/pids.txt"
fi
: > "$TP3/pids.txt"
rm -f "$TP3/notifications.log"

wait_http() {
  local url="$1"
  local name="$2"
  for _ in {1..60}; do
    if curl -fsS       -H 'X-M2M-Origin: CAdmin'       -H "X-M2M-RI: wait-$RANDOM"       -H 'X-M2M-RVI: 3'       "$url" >/dev/null 2>&1; then
      echo "✅ $name prêt"
      return 0
    fi
    sleep 1
  done
  echo "❌ $name ne répond pas. Voir les logs dans tp3/" >&2
  return 1
}

echo "Démarrage IN-CSE :8080..."
nohup python -m acmecse --config "$TP3/acme-in.ini" > "$TP3/in-cse.log" 2>&1 &
IN_PID=$!
echo "$IN_PID" >> "$TP3/pids.txt"
wait_http "http://127.0.0.1:8080/id-in" "IN-CSE"

echo "Démarrage MN-CSE :8081..."
nohup python -m acmecse --config "$TP3/acme-mn8081.ini" > "$TP3/mn-cse.log" 2>&1 &
MN_PID=$!
echo "$MN_PID" >> "$TP3/pids.txt"
wait_http "http://127.0.0.1:8081/id-mn" "MN-CSE"

echo "Démarrage serveur de notification :5000..."
nohup python "$TP3/notification_server.py" > "$TP3/notification-server.log" 2>&1 &
NOTIFY_PID=$!
echo "$NOTIFY_PID" >> "$TP3/pids.txt"
sleep 2
curl -fsS http://127.0.0.1:5000/ >/dev/null
echo "✅ serveur notification prêt"

echo "Exécution des requêtes REST du TP..."
python "$TP3/tp3_rest.py" | tee "$TP3/rest-results.log"

echo
echo "============================================================"
echo "✅ TP3 automatisé lancé."
echo "IN-CSE : http://127.0.0.1:8080"
echo "MN-CSE : http://127.0.0.1:8081"
echo "Structure IN : http://127.0.0.1:8080/__structure__"
echo "Structure MN : http://127.0.0.1:8081/__structure__"
echo
echo "Logs utiles :"
echo "  tp3/in-cse.log"
echo "  tp3/mn-cse.log"
echo "  tp3/rest-results.log"
echo "  tp3/notifications.log"
echo
echo "Pour arrêter les services : bash tp3/stop_tp3.sh"
echo "============================================================"
