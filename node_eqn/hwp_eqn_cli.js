#!/usr/bin/env node

/**
 * Simple CLI that consumes LaTeX from stdin and outputs HwpEqn code.
 */

const { Parser, Tokenizer } = require("hwp-eqn-ts");

async function readStdin() {
  if (process.stdin.isTTY) {
    return "";
  }

  return await new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf-8");
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data.trim()));
    process.stdin.on("error", reject);
  });
}

function latexToHwpEqn(latex) {
  const tokens = Tokenizer.tokenize(latex, "latex");
  const ast = Parser.parseExpression(tokens, "latex");
  return Tokenizer.decode(ast, "hwpeqn");
}

(async () => {
  try {
    const input = (await readStdin()) || process.argv.slice(2).join(" ").trim();
    if (!input) {
      console.error("No LaTeX provided. Pass via stdin or argv.");
      process.exit(1);
      return;
    }
    const result = latexToHwpEqn(input);
    process.stdout.write(result);
  } catch (err) {
    console.error("Failed to convert LaTeX:", err.message || err);
    process.exit(2);
  }
})();

