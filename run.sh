INSTALL_DIR="$HOME/.config/Ax-Shell"
echo "Starting Ax-Shell..."
killall ax-shell 2>/dev/null || true
uwsm app -- python "$INSTALL_DIR/main.py" >/dev/null 2>&1 &
disown
echo "Run complete."
