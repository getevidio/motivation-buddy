#!/bin/sh
# Creates start.command with the correct Python path and folder baked in,
# then makes it runnable. Run once:   sh install.sh

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(which python3)"

if [ -z "$PY" ]; then
  echo "python3 not found. Install it from https://www.python.org/downloads/"
  exit 1
fi

echo "Folder : $DIR"
echo "Python : $PY"
echo

cat > "$DIR/start.command" << EOF
#!/bin/sh
cd "$DIR"
exec "$PY" encourager.py
EOF

chmod +x "$DIR/start.command"

echo "Created start.command"
echo
echo "Test it:  double-click start.command in Finder"
echo
echo "Start at login:"
echo "  System Settings > General > Login Items"
echo "  Click + under 'Open at Login', pick:"
echo "  $DIR/start.command"
