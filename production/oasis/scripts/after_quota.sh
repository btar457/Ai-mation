cd "$(dirname "$0")"
echo "== exercises"; python3 lip/ex.py
echo "== shaheen 32 35 36"; python3 lip/shaheen.py gen 32 35 36
echo "== longcat"; python3 lip/jobs.py lc2
echo "== build"; python3 edit/build3.py 2>&1 | grep -E "fallback|DONE|Error"
