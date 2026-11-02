# tide-syntax

Syntax highlighting for [Tide](https://github.com/paoloanzn/tide) (`.tid`) in
VS Code, Vim and Neovim.

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

## Development

The grammars for both editors are generated from `syntax.yaml`. Edit that file,
never the generated files under `vscode/` and `vim/`, then run:

```sh
python3 generate.py                               # needs PyYAML
(cd tests && npm install) && python3 tests/run_tests.py
```

The tests tokenize `tests/cases.tid` with VS Code's TextMate engine, Vim and
Neovim, and compare the result with the `// ^^^ class` annotations in the file.

To publish a new version of the extension, bump `version` in `syntax.yaml`,
regenerate, then run this in `vscode/`:

```sh
npx @vscode/vsce publish && npx ovsx publish
```

## Known limitations

The grammars use regular expressions, not a parser. So contextual keywords
(`amount`, `slot`, `from`, ...) and type names get highlighted even where they
are used as variable names.

## License

[Apache-2.0](LICENSE)
