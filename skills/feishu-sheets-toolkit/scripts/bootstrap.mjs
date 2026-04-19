import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import readline from "node:readline/promises";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SKILL_ROOT = path.resolve(__dirname, "..");
const LOCAL_DIR = path.join(SKILL_ROOT, ".local");
const CREDENTIALS_PATH = path.join(LOCAL_DIR, "credentials.json");
const INSTALL_LOCK_PATH = path.join(LOCAL_DIR, "install.lock");

function parseArgs(argv) {
  const [, , command, ...rest] = argv;
  const options = {};
  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = rest[index + 1];
    if (!next || next.startsWith("--")) {
      options[key] = true;
      continue;
    }
    options[key] = next;
    index += 1;
  }
  return { command, options };
}

function printUsage() {
  console.log(`Usage:
  node scripts/bootstrap.mjs setup [--app-id <APP_ID>] [--app-secret <APP_SECRET>]
  node scripts/bootstrap.mjs info --url <FEISHU_URL>
  node scripts/bootstrap.mjs sheets --url <FEISHU_URL>
  node scripts/bootstrap.mjs read --url <FEISHU_URL> --range <sheetId!A1:C5>
  node scripts/bootstrap.mjs search-sheet --url <FEISHU_URL> --sheet <sheetId-or-title> --query <text>
  node scripts/bootstrap.mjs search-all --url <FEISHU_URL> --query <text> [--mode contains|exact|regex]
  node scripts/bootstrap.mjs write --url <FEISHU_URL> --range <sheetId!A1:B2> --values-file <file.json>`);
}

function ensureLocalDir() {
  fs.mkdirSync(LOCAL_DIR, { recursive: true });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function promptCredentials(existing = {}) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  try {
    const appId =
      existing.appId ||
      (await rl.question("Feishu App ID: ")).trim();
    const appSecret =
      existing.appSecret ||
      (await rl.question("Feishu App Secret: ")).trim();

    if (!appId || !appSecret) {
      throw new Error("App ID and App Secret are required.");
    }

    return { appId, appSecret };
  } finally {
    rl.close();
  }
}

function saveCredentials(credentials) {
  ensureLocalDir();
  fs.writeFileSync(CREDENTIALS_PATH, JSON.stringify(credentials, null, 2));
  console.log(`Saved credentials to ${CREDENTIALS_PATH}`);
}

function loadCredentials() {
  if (!fs.existsSync(CREDENTIALS_PATH)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(CREDENTIALS_PATH, "utf8"));
}

async function acquireInstallLock(timeoutMs = 120000) {
  ensureLocalDir();
  const startedAt = Date.now();

  while (true) {
    try {
      const fd = fs.openSync(INSTALL_LOCK_PATH, "wx");
      return fd;
    } catch (error) {
      if (error?.code !== "EEXIST") {
        throw error;
      }
      if (Date.now() - startedAt > timeoutMs) {
        throw new Error("Timed out while waiting for dependency installation lock.");
      }
      await sleep(1000);
    }
  }
}

function releaseInstallLock(fd) {
  try {
    fs.closeSync(fd);
  } catch {}
  try {
    fs.unlinkSync(INSTALL_LOCK_PATH);
  } catch {}
}

async function ensureDependenciesInstalled() {
  const sdkPath = path.join(SKILL_ROOT, "node_modules", "@larksuiteoapi", "node-sdk");
  if (fs.existsSync(sdkPath)) {
    return;
  }

  const lockFd = await acquireInstallLock();
  try {
    if (fs.existsSync(sdkPath)) {
      return;
    }

    console.log("Installing skill dependencies...");
    const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
    const result = spawnSync(npmCommand, ["install", "--omit=dev"], {
      cwd: SKILL_ROOT,
      stdio: "inherit",
      shell: false,
    });

    if (result.status !== 0) {
      throw new Error("Dependency installation failed.");
    }
  } finally {
    releaseInstallLock(lockFd);
  }
}

async function main() {
  const { command, options } = parseArgs(process.argv);
  if (!command) {
    printUsage();
    process.exit(1);
  }

  if (command === "setup") {
    const credentials = await promptCredentials({
      appId: typeof options["app-id"] === "string" ? options["app-id"] : "",
      appSecret: typeof options["app-secret"] === "string" ? options["app-secret"] : "",
    });
    saveCredentials(credentials);
    return;
  }

  const credentials = loadCredentials();
  if (!credentials?.appId || !credentials?.appSecret) {
    console.error(
      [
        "Feishu credentials are not configured for this skill yet.",
        "Please provide your Feishu App ID and App Secret for first-time setup.",
        "Then run:",
        'node scripts/bootstrap.mjs setup --app-id "<APP_ID>" --app-secret "<APP_SECRET>"',
      ].join("\n"),
    );
    process.exit(1);
  }

  await ensureDependenciesInstalled();
  const { runCli } = await import("./cli.mjs");
  await runCli({
    command,
    options,
    skillRoot: SKILL_ROOT,
    credentials,
  });
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
