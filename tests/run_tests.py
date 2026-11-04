#!/usr/bin/env python3
"""Check the generated grammars against the annotations in tests/cases.tid.

Each backend tokenizes the file with the real engine and the expected class
from syntax.yaml is mapped to that engine's name for it:
  vscode  vscode-textmate + vscode-oniguruma (the engine VS Code uses)
  vim     vim -es, synID() per column
  nvim    nvim --headless, synID() per column
  emacs   emacs --batch, the face of every column after font-lock

The emacs backend also checks that `compilation-mode` finds the locations and
severities in sample `tide` output (COMPILE_OUTPUT).

Usage: python3 tests/run_tests.py [backend ...]   (default: all available)
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TESTS = Path(__file__).resolve().parent
ROOT = TESTS.parent
sys.path.insert(0, str(ROOT))
import generate  # noqa: E402

CASES = TESTS / "cases.tid"
ANNOTATION = re.compile(r"^//(\s*)(<-+|\^+)\s+(\S+)\s*$")


def parse_cases(path):
    """Return [(line_index, column, class_or_None, annotation_lineno)]."""
    expectations, source = [], None
    for i, line in enumerate(path.read_text().splitlines()):
        m = ANNOTATION.match(line)
        if not m:
            source = i
            continue
        marks, cls = m.group(2), m.group(3)
        if marks.startswith("<"):
            cols = range(0, len(marks) - 1)
        else:
            start = 2 + len(m.group(1))
            cols = range(start, start + len(marks))
        for c in cols:
            expectations.append((source, c, None if cls == "none" else cls, i + 1))
    return expectations


def dump_vscode(spec):
    if not (TESTS / "node_modules").exists():
        raise RuntimeError("run `npm install` in tests/ first")
    grammar = ROOT / "vscode" / "syntaxes" / f"{spec['language']['id']}.tmLanguage.json"
    out = subprocess.run(["node", TESTS / "dump_textmate.mjs", grammar, CASES],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def dump_vim(cmd):
    def run(_spec):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.json"
            setup = f"let g:rtp={json.dumps(str(ROOT / 'vim'))} | let g:out={json.dumps(str(out))}"
            args = [cmd, "-Nu", "NONE", "-i", "NONE", "--cmd", setup, "-S", TESTS / "dump_vim.vim", CASES]
            args[1:1] = ["--headless"] if cmd == "nvim" else ["-es"]
            proc = subprocess.run(args, capture_output=True, text=True, timeout=60)
            if not out.exists():
                raise RuntimeError(f"{cmd} failed:\n{proc.stdout}{proc.stderr}")
            if proc.stdout.strip() or proc.stderr.strip():
                raise RuntimeError(f"{cmd} reported errors:\n{proc.stdout}{proc.stderr}")
            return json.loads(out.read_text())
    return run


def run_emacs(what, path):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        mode = ROOT / "emacs" / f"{generate.load_spec()['emacs']['package']}.el"
        proc = subprocess.run(["emacs", "-Q", "--batch", "-l", TESTS / "dump_emacs.el", mode, what, path, out],
                              capture_output=True, text=True, timeout=60)
        if not out.exists():
            raise RuntimeError(f"emacs failed:\n{proc.stdout}{proc.stderr}")
        return json.loads(out.read_text())


def dump_emacs(_spec):
    return run_emacs("faces", CASES)


# Real `tide check` / `tide up` output (NO_COLOR=1), plus a source line quoting
# a diagnostic, which must not be taken for one.
COMPILE_OUTPUT = """\
/work/bad.tid:2:5: error: redeclaration of 'a'
 2 | let a = 2;
   |     ^
/work/bad.tid:1:5: note: previous declaration is here
 1 | let a = 1;
   |     ^
lib/common.tid:4:13: warning: account HWrCL2DiCckyFMw4Z4BR8fWq1QHFGecjh19DReM3Epye has 0 lamports and will not exist on chain
 4 |     account alice.pubkey { lamports = 0; owner = system_program(); }
   |             ^~~~~
/work/bad.tid:7:9: error: unknown identifier 'undefined_thing'
 7 | let s = "x.tid:1:2: error: not a diagnostic";
   |         ^~~~~~~~~~~~~~~
tide: cannot read 'missing.tid'
2 error(s), 1 warning(s)
"""
COMPILE_EXPECTED = [
    ["/work/bad.tid", 2, 5, 2],
    ["/work/bad.tid", 1, 5, 0],
    ["lib/common.tid", 4, 13, 1],
    ["/work/bad.tid", 7, 9, 2],
]


def check_emacs_compile():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "output.txt"
        path.write_text(COMPILE_OUTPUT)
        got = run_emacs("compile", path)
    if got == COMPILE_EXPECTED:
        return []
    return [f"  compile: want {COMPILE_EXPECTED}", f"  compile: got  {got}"]


def check_vscode(spec, cls, scopes):
    lang = spec["language"]["id"]
    if cls is None:
        return scopes == [spec["language"]["scope"]], scopes
    want = f"{spec['classes'][cls]['scope']}.{lang}"
    return want in scopes, scopes


def check_vim(spec, cls, group):
    if cls is None or spec["classes"][cls]["vim"] is None:
        return group == "", group or "(none)"
    return group == generate.vim_group(spec, cls), group or "(none)"


def check_emacs(spec, cls, face):
    want = spec["classes"][cls]["emacs"] if cls else None
    # Emacs draws comment starters (`//`, `/*`) with a face that inherits the comment face.
    if face == "font-lock-comment-delimiter-face":
        face = "font-lock-comment-face"
    return face == (want or ""), face or "(none)"


BACKENDS = {
    "vscode": (lambda: shutil.which("node"), dump_vscode, check_vscode),
    "vim": (lambda: shutil.which("vim"), dump_vim("vim"), check_vim),
    "nvim": (lambda: shutil.which("nvim"), dump_vim("nvim"), check_vim),
    "emacs": (lambda: shutil.which("emacs"), dump_emacs, check_emacs),
}


def main():
    if subprocess.run([sys.executable, ROOT / "generate.py", "--check"]).returncode:
        return 1
    spec = generate.load_spec()
    lines = CASES.read_text().splitlines()
    expectations = parse_cases(CASES)
    names = sys.argv[1:] or list(BACKENDS)
    failed = False
    for name in names:
        available, dump, check = BACKENDS[name]
        if not available():
            print(f"{name}: SKIP (not installed)")
            continue
        try:
            table = dump(spec)
        except Exception as e:  # noqa: BLE001
            print(f"{name}: ERROR {e}")
            failed = True
            continue
        errors = check_emacs_compile() if name == "emacs" else []
        for line, col, cls, ann in expectations:
            row = table[line]
            ok, got = check(spec, cls, row[col] if col < len(row) else None)
            if not ok:
                errors.append(f"  cases.tid:{ann}: line {line + 1} col {col} "
                              f"{lines[line][col]!r}: want {cls or 'none'}, got {got}")
        print(f"{name}: {'FAIL' if errors else 'ok'} ({len(expectations) - len(errors)}/{len(expectations)} columns)")
        print("\n".join(errors[:40]), end="\n" if errors else "")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
