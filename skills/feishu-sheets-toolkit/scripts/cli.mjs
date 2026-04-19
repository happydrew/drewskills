import fs from "node:fs";

import { FeishuSheetsToolkit } from "./lib/feishu-sheets-toolkit.mjs";
import { FeishuSheetsError } from "./lib/errors.mjs";
import { parseSpreadsheetUrl } from "./lib/utils.mjs";

function printJson(value) {
  console.log(JSON.stringify(value, null, 2));
}

function loadWriteValues(values, valuesFile) {
  if (typeof valuesFile === "string") {
    return JSON.parse(fs.readFileSync(valuesFile, "utf8"));
  }
  if (typeof values === "string") {
    return JSON.parse(values);
  }
  throw new FeishuSheetsError(
    "Write command requires either --values or --values-file",
    "MISSING_WRITE_VALUES",
    400,
  );
}

function requiredString(value, message) {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  throw new FeishuSheetsError(message, "INVALID_ARGUMENT", 400);
}

export async function runCli({ command, options, credentials }) {
  const toolkit = new FeishuSheetsToolkit(credentials);

  switch (command) {
    case "info": {
      const url = requiredString(options.url, "--url is required");
      const { spreadsheetToken } = parseSpreadsheetUrl(url);
      printJson(await toolkit.getSpreadsheetInfo(spreadsheetToken));
      return;
    }
    case "sheets": {
      const url = requiredString(options.url, "--url is required");
      const { spreadsheetToken } = parseSpreadsheetUrl(url);
      printJson(await toolkit.listWorksheets(spreadsheetToken));
      return;
    }
    case "read": {
      const url = requiredString(options.url, "--url is required");
      const range = requiredString(options.range, "--range is required");
      const { spreadsheetToken } = parseSpreadsheetUrl(url);
      printJson(await toolkit.readRange(spreadsheetToken, range));
      return;
    }
    case "search-sheet": {
      const url = requiredString(options.url, "--url is required");
      const sheetArg = requiredString(options.sheet, "--sheet is required");
      const query = requiredString(options.query, "--query is required");
      const { spreadsheetToken } = parseSpreadsheetUrl(url);
      const worksheets = await toolkit.listWorksheets(spreadsheetToken);
      const worksheet = worksheets.find(
        (item) => item.sheetId === sheetArg || item.title === sheetArg,
      );
      if (!worksheet) {
        throw new FeishuSheetsError(`Worksheet not found: ${sheetArg}`, "SHEET_NOT_FOUND", 404);
      }
      printJson(
        await toolkit.searchSheet(
          spreadsheetToken,
          worksheet.sheetId,
          worksheet.title,
          worksheet.rowCount,
          worksheet.columnCount,
          {
            query,
            mode: typeof options.mode === "string" ? options.mode : undefined,
          },
        ),
      );
      return;
    }
    case "search-all": {
      const url = requiredString(options.url, "--url is required");
      const query = requiredString(options.query, "--query is required");
      const { spreadsheetToken } = parseSpreadsheetUrl(url);
      printJson(
        await toolkit.searchAllSheets(spreadsheetToken, {
          query,
          mode: typeof options.mode === "string" ? options.mode : undefined,
        }),
      );
      return;
    }
    case "write": {
      const url = requiredString(options.url, "--url is required");
      const range = requiredString(options.range, "--range is required");
      const { spreadsheetToken } = parseSpreadsheetUrl(url);
      printJson(
        await toolkit.writeRange(
          spreadsheetToken,
          range,
          loadWriteValues(options.values, options["values-file"]),
        ),
      );
      return;
    }
    default:
      throw new FeishuSheetsError(`Unknown command: ${command}`, "UNKNOWN_COMMAND", 400);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runCli({
    command: process.argv[2],
    options: {},
    credentials: null,
  }).catch((error) => {
    const normalized =
      error instanceof FeishuSheetsError
        ? error
        : new FeishuSheetsError(error instanceof Error ? error.message : String(error));
    console.error(
      JSON.stringify(
        {
          error: normalized.name,
          message: normalized.message,
          code: normalized.code,
          status: normalized.status,
          details: normalized.details,
        },
        null,
        2,
      ),
    );
    process.exit(1);
  });
}
