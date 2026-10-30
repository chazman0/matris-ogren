#!/usr/bin/env bash
# op4 CI bekleyici (MIMARI §20.2): bir GitHub Actions çalışmasını api.github.com üzerinden izler; çalışma bitene ya da
# bir adım başarısız olana dek bekler, sonra işlerin ve adımların özetini yazar.
#
#   op4/araclar/ci_bekle.sh <run_id>
#   op4/araclar/ci_bekle.sh --isleme <tam sha> [--is-akisi op4.yml]  (o işlemenin çalışması görünene dek de bekler)
#
# Ortam: OP4_DEPO (varsayılan chazman0/matris-ogren), OP4_BEKLE_SN (yoklama aralığı, varsayılan 30),
#        OP4_SURE_SN (en uzun bekleme, varsayılan 5400), GITHUB_TOKEN (varsa yetkili istek; yoksa yetkisiz).
# Ön planda uyku yasak olan ortamlarda arka planda çalıştırılır; bitince tek satırlık sonuç ve adım tablosu basar.
# Çıkış kodu: 0 çalışma başarılı; 1 başarısız / iptal; 3 süre doldu; 4 kullanım ya da erişim hatası.
set -u

DEPO="${OP4_DEPO:-chazman0/matris-ogren}"
ARALIK="${OP4_BEKLE_SN:-30}"
SURE="${OP4_SURE_SN:-5400}"
API="https://api.github.com/repos/$DEPO/actions"

kullanim() { sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 4; }

calisma="" isleme="" is_akisi="op4.yml"
while [ $# -gt 0 ]; do
  case "$1" in
    --isleme) isleme="${2:-}"; shift 2 ;;
    --is-akisi) is_akisi="${2:-}"; shift 2 ;;
    -h|--help) kullanim ;;
    *) calisma="$1"; shift ;;
  esac
done
[ -n "$calisma" ] || [ -n "$isleme" ] || kullanim

al() {  # al <yol> — JSON yanıtı standart çıktıya
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    curl -fsS -m 30 -H "Accept: application/vnd.github+json" -H "Authorization: Bearer $GITHUB_TOKEN" "$API/$1"
  else
    curl -fsS -m 30 -H "Accept: application/vnd.github+json" "$API/$1"
  fi
}

bas=$(date +%s)
sure_doldu() { [ $(( $(date +%s) - bas )) -ge "$SURE" ]; }

# 1) İşlemeden çalışma kimliği (çalışma kuyruğa düşene dek bekle)
if [ -z "$calisma" ]; then
  while :; do
    calisma=$(al "workflows/$is_akisi/runs?head_sha=$isleme&per_page=5" 2>/dev/null | python3 -c '
import json, sys
try:
    r = json.load(sys.stdin)["workflow_runs"]
except Exception:
    sys.exit()
if r:
    print(max(r, key=lambda x: x["run_number"])["id"])
' 2>/dev/null)
    [ -n "$calisma" ] && break
    if sure_doldu; then echo "SÜRE DOLDU: $isleme için $is_akisi çalışması görünmedi"; exit 3; fi
    sleep "$ARALIK"
  done
  echo "çalışma $calisma (işleme ${isleme:0:12}, $is_akisi)"
fi

# 2) Çalışmayı izle
while :; do
  ozet=$( { al "runs/$calisma"; echo; echo "-----"; al "runs/$calisma/jobs?per_page=50"; } 2>/dev/null | python3 -c '
import json, sys
metin = sys.stdin.read()
try:
    calisma_m, isler_m = metin.split("\n-----\n", 1)
    c = json.loads(calisma_m)
    isler = json.loads(isler_m)["jobs"]
except Exception:
    print("BEKLE erişilemedi")
    sys.exit()
kotu = [(j["name"], s["name"]) for j in isler for s in j.get("steps", []) if s.get("conclusion") in ("failure", "cancelled")]
if c.get("status") != "completed" and not kotu:
    print("BEKLE", c.get("status"))
    sys.exit()
print("BITTI", c.get("status"), c.get("conclusion") or ("adım başarısız" if kotu else "?"),
      "çalışma", c.get("id"), "işleme", (c.get("head_sha") or "")[:12], c.get("html_url", ""))
for j in isler:
    print("iş %s %s: %s %s" % (j["id"], j["name"], j.get("status"), j.get("conclusion")))
    for s in j.get("steps", []):
        b, e = (s.get("started_at") or "")[11:19], (s.get("completed_at") or "")[11:19]
        print("  %2s %-72s %-9s %s %s" % (s["number"], s["name"][:72], s.get("conclusion"), b, e))
')
  case "$ozet" in
    BITTI*)
      echo "$ozet"
      case "$(echo "$ozet" | head -1)" in
        "BITTI completed success"*) exit 0 ;;
        *) exit 1 ;;
      esac ;;
  esac
  if sure_doldu; then echo "SÜRE DOLDU: çalışma $calisma ($ozet)"; exit 3; fi
  sleep "$ARALIK"
done
