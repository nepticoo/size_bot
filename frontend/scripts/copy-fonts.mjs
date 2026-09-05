// Self-hosts Vazirmatn from the npm package into src/fonts — never loaded from Google Fonts,
// which is unreliable from inside Iran and from the deployed server.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const pkgFontsDir = join(__dirname, "..", "node_modules", "vazirmatn", "fonts", "webfonts");
const destDir = join(__dirname, "..", "src", "fonts");

if (!existsSync(pkgFontsDir)) {
  console.warn("vazirmatn package fonts not found, skipping font copy");
  process.exit(0);
}

mkdirSync(destDir, { recursive: true });

const files = ["Vazirmatn-Regular.woff2", "Vazirmatn-Medium.woff2", "Vazirmatn-Bold.woff2"];
for (const f of files) {
  const src = join(pkgFontsDir, f);
  if (existsSync(src)) {
    copyFileSync(src, join(destDir, f));
  }
}
console.log("Vazirmatn fonts copied to src/fonts");
