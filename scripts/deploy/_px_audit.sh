#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  _px_audit.sh — auditoria EN VIVO de Termux (solo lectura)
#  Se ejecuta dentro de Termux. Vuelca todo a /sdcard para
#  que el PC lo lea por adb.
#  Uso:  bash /sdcard/DanielaOS/deploy/_px_audit.sh
# ============================================================
O=/sdcard/DanielaOS/audit/termux_audit_live.txt
mkdir -p /sdcard/DanielaOS/audit

{
echo "################ AUDIT LIVE $(date '+%F %T') ################"
echo
echo "=== 1. HOME (tamanos) ==============================="
du -sm "$HOME"/* 2>/dev/null | sort -rn | head -40

echo
echo "=== 2. apps/ (contenido exacto) ====================="
ls -la "$HOME/apps" 2>&1

echo
echo "=== 3. buscar carpetas aig/AIG/monorepo ============="
find "$HOME" -maxdepth 4 \( -iname '*aig*' -o -iname '*monorepo*' \) 2>/dev/null | head -40

echo
echo "=== 4. GIT: estado de cada repo en apps/ ============"
for g in "$HOME"/apps/*/; do
  [ -d "$g/.git" ] || continue
  echo "-------- $g"
  git -C "$g" status -sb 2>&1 | head -20
  echo "  -- log:"
  git -C "$g" log --oneline -8 2>&1
  echo "  -- remotes:"
  git -C "$g" remote -v 2>&1
  echo "  -- ramas:"
  git -C "$g" branch -a 2>&1 | head -15
done

echo
echo "=== 5. daniela-os (deploy instalado) ================"
ls -la "$HOME/daniela-os" 2>&1 | head -30
du -sm "$HOME/daniela-os" 2>/dev/null

echo
echo "=== 6. scripts locales NO subidos (guardian etc) ===="
ls -la "$HOME/apps"/*/scripts/*.sh 2>/dev/null | head -30
ls -la "$HOME/scripts" 2>/dev/null

echo
echo "=== 7. procesos / servicios vivos ==================="
ps -ef 2>/dev/null | grep -Ei 'python|sshd|runsv|guardian|server\.py|cloudflared' | grep -v grep | head -25

echo
echo "=== 8. duplicados verificados (llama/whisper/models) ="
for d in llama.cpp whisper.cpp models; do
  a=$(du -sm "$HOME/$d" 2>/dev/null | cut -f1)
  b=$(du -sm "$HOME/apps/$d" 2>/dev/null | cut -f1)
  echo "$d: ~/=$a MB  ~/apps/=$b MB"
  if [ -n "$a" ] && [ -n "$b" ]; then
    echo "   diff -rq (primeras lineas):"
    diff -rq "$HOME/$d" "$HOME/apps/$d" 2>/dev/null | head -8
    echo "   -> lineas diferentes: $(diff -rq "$HOME/$d" "$HOME/apps/$d" 2>/dev/null | wc -l)"
  fi
done

echo
echo "=== 9. espacio y ram ================================="
df -h "$HOME" 2>/dev/null | tail -2
free -m 2>/dev/null | head -3

echo
echo "################ FIN $(date '+%F %T') ################"
} > "$O" 2>&1

echo "AUDIT OK -> $O"
