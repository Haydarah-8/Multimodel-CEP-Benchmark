import pathlib


def main() -> None:
    t = pathlib.Path("docs/FIGURE_COMPANION_WRITER.md").read_text(encoding="utf-8")
    start_marker = "```python"
    i = t.find(start_marker)
    if i == -1:
        raise SystemExit("docs/FIGURE_COMPANION_WRITER.md: missing ```python block")
    start = t.find("\n", i)
    if start == -1:
        raise SystemExit("malformed ```python block")
    start += 1
    end = t.rfind("```")
    if end <= start:
        raise SystemExit("docs/FIGURE_COMPANION_WRITER.md: missing closing ``` for python block")
    body = t[start:end].strip("\n")
    pathlib.Path("scripts/write_figure_companions.py").write_text(body + "\n", encoding="utf-8")
    print("synced", len(body), "chars -> scripts/write_figure_companions.py")


if __name__ == "__main__":
    main()
