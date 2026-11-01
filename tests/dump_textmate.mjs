// Tokenizes a file with VS Code's TextMate engine and prints, per line, the
// scope stack of every column as JSON: [[["source.tide", ...], ...], ...].
// Usage: node dump_textmate.mjs <grammar.json> <file>
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vsctm from "vscode-textmate";
import oniguruma from "vscode-oniguruma";

const require = createRequire(import.meta.url);
const [grammarPath, inputPath] = process.argv.slice(2);

const wasm = readFileSync(require.resolve("vscode-oniguruma/release/onig.wasm")).buffer;
await oniguruma.loadWASM(wasm);

const registry = new vsctm.Registry({
  onigLib: Promise.resolve({
    createOnigScanner: (patterns) => new oniguruma.OnigScanner(patterns),
    createOnigString: (s) => new oniguruma.OnigString(s),
  }),
  loadGrammar: async () => vsctm.parseRawGrammar(readFileSync(grammarPath, "utf8"), grammarPath),
});

const grammar = await registry.loadGrammar(JSON.parse(readFileSync(grammarPath, "utf8")).scopeName);
let state = vsctm.INITIAL;
const out = [];
for (const line of readFileSync(inputPath, "utf8").replace(/\n$/, "").split("\n")) {
  const { tokens, ruleStack } = grammar.tokenizeLine(line, state);
  const cols = [];
  for (const t of tokens) for (let c = t.startIndex; c < Math.min(t.endIndex, line.length); c++) cols.push(t.scopes);
  out.push(cols);
  state = ruleStack;
}
process.stdout.write(JSON.stringify(out));
