import pathlib

AGENTS_DIR = pathlib.Path(__file__).parent / "agents"

def fix_agent_file(path: pathlib.Path):
    raw = path.read_text(encoding="utf-8")

    # If the file already looks like normal Python (no "\n" escapes), skip it
    if "\\n" not in raw:
        print(f"[SKIP] {path.name} (no \\n escapes)")
        return

    # Many of your files look like:
    # class Agent:\n    def run(self, context):\n        return \"...\" + context.get('task','')\n
    # We want to turn the escape sequences into real newlines and quotes.
    fixed = raw.encode("utf-8").decode("unicode_escape")

    # Extra safety: strip any leading/trailing whitespace
    fixed = fixed.strip() + "\n"

    path.write_text(fixed, encoding="utf-8")
    print(f"[FIXED] {path.name}")

def main():
    if not AGENTS_DIR.exists():
        raise SystemExit(f"Agents directory not found: {AGENTS_DIR}")

    for py in AGENTS_DIR.glob("*.py"):
        if py.name == "__init__.py":
            continue
        fix_agent_file(py)

if __name__ == "__main__":
    main()
