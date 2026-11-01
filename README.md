# tide-syntax

Syntax highlighting for [Tide](../tide) (`.tid`) in **VS Code**, **Vim** and
**Neovim**, generated from one declarative specification.

VS Code highlights with TextMate grammars and Vim with its own syntax engine;
no single grammar format works in both. Instead, `syntax.yaml` describes the
language once and `generate.py` emits a native grammar for each editor:

```text
syntax.yaml ──generate.py──┬─▶ vscode/syntaxes/tide.tmLanguage.json   (VS Code)
                           ├─▶ vscode/language-configuration.json
                           ├─▶ vscode/package.json
                           ├─▶ vim/syntax/tide.vim                    (Vim / Neovim)
                           ├─▶ vim/ftdetect/tide.vim
                           └─▶ vim/ftplugin/tide.vim
```

Generated files are committed so the editors can load them directly. Never
edit them by hand: change `syntax.yaml` (or the generator) and regenerate.

## Install

**VS Code**: link the extension folder and reload the window:

```sh
ln -s "$PWD/vscode" ~/.vscode/extensions/paoloanzn.tide-syntax-0.1.0
```

To get a `.vsix` instead, run `npx @vscode/vsce package` in `vscode/`.

**Vim**: use a native package:

```sh
mkdir -p ~/.vim/pack/tide/start && ln -s "$PWD/vim" ~/.vim/pack/tide/start/tide
```

**Neovim**:

```sh
mkdir -p ~/.local/share/nvim/site/pack/tide/start && ln -s "$PWD/vim" ~/.local/share/nvim/site/pack/tide/start/tide
```

With a plugin manager, point the runtime path at `vim/`, for example
`Plug '<repo>', { 'rtp': 'vim' }` with vim-plug.

Open `examples/local_defi.tid` to check the result.

## The specification

`syntax.yaml` mirrors the reference implementation: keywords from
`tide/src/parser.cpp`, builtins and types from `tide/src/sema.cpp`, and the
lexical rules from `lang-design.md`. It has two parts:

- **Classes**: semantic categories such as `keyword_action`, `builtin` or
  `unit`. Each one names a TextMate scope (for VS Code themes) and a standard
  Vim highlight group (for Vim colorschemes).
- **Token rules**: comments, strings and escapes, numbers with unit suffixes,
  keyword groups, declarations (a keyword and the name it introduces), fields,
  member access, builtin and user calls, types, operators and punctuation.
  Every rule points to a class.

The generator puts the rules in one priority order. Fields come before
keywords, because record keys can be reserved words (`mint = usd.pubkey;`).
Builtins only count as builtins when called (`token_program()` versus
`token_program = ...`). The two engines settle ties in opposite ways: TextMate
takes the first matching pattern, Vim takes the last definition. So the
generator writes the same rule list forwards for VS Code and backwards for Vim.

Common edits:

- **New keyword, builtin or type**: add the word to its list.
- **New category**: add an entry under `classes` and point the rule at it.
- **Different colours**: change a class's `scope` or `vim` group.

Then run:

```sh
python3 generate.py            # needs PyYAML
```

## Tests

`tests/cases.tid` is a Tide file with annotations. Each `// ^^^ class` comment
states the class expected for the marked columns of the source line above it
(`<-` marks column 0, `none` means not highlighted). `tests/run_tests.py`
first checks that the generated files are up to date. It then tokenizes the
case file with each real engine and compares the result with the annotations:

| Backend  | Engine |
|---|---|
| `vscode` | `vscode-textmate` + `vscode-oniguruma`, the libraries VS Code uses |
| `vim`    | `vim -es`, `synID()` for each column |
| `nvim`   | `nvim --headless`, `synID()` for each column |

```sh
(cd tests && npm install)
python3 tests/run_tests.py           # all installed backends
python3 tests/run_tests.py vim       # just one
```

## Known limitations

These grammars are regex-based, not parsers:

- Contextual keywords (`amount`, `slot`, `epoch`, `time`, `from`, `to`, ...)
  are highlighted wherever they appear. A variable with one of these names is
  coloured as a keyword. A call such as `slot()` is still shown as a builtin.
- Type names are highlighted wherever they appear, not only in type
  positions. A variable named `range` is coloured as a type.
- In `Option<string>`, the `<` and `>` are coloured as comparison operators.
- Object-literal keys (`{ value: 0 }`) are not highlighted.

Getting exact context would take a real parser, such as a Tree-sitter grammar
for Neovim. VS Code would still need a TextMate grammar, or a semantic-token
provider, alongside it.
