# tide-syntax

Syntax highlighting for [Tide](https://github.com/paoloanzn/tide) (`.tid`) in
VS Code, Vim, Neovim and Emacs, and for Tide code blocks in Obsidian.

## Install

### VS Code

Install **Tide Syntax** from the
[Marketplace](https://marketplace.visualstudio.com/items?itemName=paoloanzn.tide-syntax),
or run:

```sh
code --install-extension paoloanzn.tide-syntax
```

The extension is also on [Open VSX](https://open-vsx.org/extension/paoloanzn/tide-syntax),
for Cursor, VSCodium and other VS Code forks.

### Obsidian

[Shiki Highlighter](https://github.com/mProjectsCode/obsidian-shiki-plugin)
uses the same TextMate grammar as the VS Code extension to highlight Tide
code blocks in Reading view, Live Preview and Source mode.

1. In Obsidian, open **Settings → Community plugins → Browse**, then install
   and enable **Shiki Highlighter**.
2. Copy [tide.tmLanguage.json](vscode/syntaxes/tide.tmLanguage.json) into a
   folder inside your vault, for example `syntax/tide.tmLanguage.json`.
3. In the plugin settings, set **Custom languages folder location** to that
   folder (`syntax` in this example).
4. Run **Shiki Highlighter: Reload highlighter** from the command palette.

Use `tide` after the opening fence in your notes:

````markdown
```tide
keypair alice = seed("alice");
let amount = 10 SOL;
```
````

To update, replace the grammar file with the latest copy and reload the
highlighter. This setup highlights code blocks in Markdown notes; it does
not add an editor for standalone `.tid` files.

### Vim and Neovim

```sh
curl -fsSL https://raw.githubusercontent.com/paoloanzn/tide-syntax/main/install.sh | sh
```

This sets it up for every editor it finds (Vim, Neovim). Run it again to
update.

If you use a plugin manager, point it at the `vim/` folder instead. With
vim-plug:

```vim
Plug 'paoloanzn/tide-syntax', { 'rtp': 'vim' }
```

With lazy.nvim:

```lua
{ "paoloanzn/tide-syntax", config = function(p) vim.opt.rtp:append(p.dir .. "/vim") end }
```

### Emacs

`tide-lang-mode` needs Emacs 29.1 or later. Install it from this repository
with Emacs 30's `use-package`:

```elisp
(use-package tide-lang-mode
  :vc (:url "https://github.com/paoloanzn/tide-syntax" :lisp-dir "emacs"))
```

On Emacs 29, evaluate this once (`M-:`):

```elisp
(package-vc-install
 '(tide-lang-mode :url "https://github.com/paoloanzn/tide-syntax" :lisp-dir "emacs"))
```

The package is also coming to [MELPA](https://melpa.org). Once it's there,
`(use-package tide-lang-mode :ensure t)` will work.

It is called `tide-lang-mode` because MELPA's `tide` package, for TypeScript,
already owns `tide-mode`. Both can be installed at the same time.

Besides highlighting and indentation, it sets up `M-x compile`. The default
command is `tide check` on the current file, and `next-error` (`M-g n`) jumps
to each error and warning. Set `tide-lang-program` if `tide` is not on your
`exec-path`. Compiling sets `NO_COLOR=1`, so you need a Tide release that
honors it. Older releases print colors on the terminal Emacs gives them, and
Emacs can't read those error locations.

## Development

The grammars for every editor are generated from `syntax.yaml`. Edit that
file, never the generated files under `vscode/`, `vim/` and `emacs/`, then
run:

```sh
python3 generate.py                               # needs PyYAML
(cd tests && npm install) && python3 tests/run_tests.py
```

The tests tokenize `tests/cases.tid` with VS Code's TextMate engine, Vim,
Neovim and Emacs, and compare the result with the `// ^^^ class` annotations
in the file. The Emacs backend also checks that `compilation-mode` reads
sample `tide` output correctly.

To publish a new version of the extension, bump `version` in `syntax.yaml`,
regenerate, then run this in `vscode/`:

```sh
npx @vscode/vsce publish && npx ovsx publish
```

MELPA builds the Emacs package from `emacs/tide-lang-mode.el` on `main`, so
committing the regenerated file publishes it.

## Known limitations

The grammars use regular expressions, not a parser. So contextual keywords
(`amount`, `slot`, `from`, ...) and type names get highlighted even where they
are used as variable names.

## License

[Apache-2.0](LICENSE)
