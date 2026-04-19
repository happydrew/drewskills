import { FeishuSheetsError } from "./errors.mjs";

const CELL_REF_RE = /^([A-Z]+)(\d+)$/;

export function parseSpreadsheetUrl(rawUrl) {
  let url;
  try {
    url = new URL(rawUrl);
  } catch (error) {
    throw new FeishuSheetsError("Invalid spreadsheet URL", "INVALID_URL", 400, error);
  }

  const match = url.pathname.match(/\/sheets\/([^/?#]+)/);
  if (!match) {
    throw new FeishuSheetsError(
      "Could not find spreadsheet token in URL",
      "MISSING_SPREADSHEET_TOKEN",
      400,
    );
  }

  return {
    spreadsheetToken: match[1],
    sheetId: url.searchParams.get("sheet") ?? undefined,
    rawUrl,
  };
}

export function columnNumberToLabel(columnNumber) {
  if (!Number.isInteger(columnNumber) || columnNumber < 1) {
    throw new FeishuSheetsError("Column number must be a positive integer", "INVALID_COLUMN", 400);
  }
  let current = columnNumber;
  let label = "";
  while (current > 0) {
    const remainder = (current - 1) % 26;
    label = String.fromCharCode(65 + remainder) + label;
    current = Math.floor((current - 1) / 26);
  }
  return label;
}

export function columnLabelToNumber(label) {
  const normalized = label.trim().toUpperCase();
  if (!/^[A-Z]+$/.test(normalized)) {
    throw new FeishuSheetsError("Invalid column label", "INVALID_COLUMN_LABEL", 400);
  }
  let value = 0;
  for (const char of normalized) {
    value = value * 26 + (char.charCodeAt(0) - 64);
  }
  return value;
}

export function toCellRef(rowNumber, columnNumber) {
  return `${columnNumberToLabel(columnNumber)}${rowNumber}`;
}

export function parseCellRef(cellRef) {
  const match = cellRef.trim().toUpperCase().match(CELL_REF_RE);
  if (!match) {
    throw new FeishuSheetsError("Invalid cell reference", "INVALID_CELL_REF", 400);
  }
  return {
    column: columnLabelToNumber(match[1]),
    row: Number(match[2]),
  };
}

export function encodeRangeSpec(rangeSpec) {
  return encodeURIComponent(rangeSpec).replace(/!/g, "%21");
}

export function normalizeRangeSpec(sheetId, range) {
  if (!range) {
    throw new FeishuSheetsError("Range is required", "MISSING_RANGE", 400);
  }
  return range.includes("!") ? range : `${sheetId}!${range}`;
}

export function parseRangeSpec(rangeSpec) {
  const [sheetId, cellRange] = rangeSpec.split("!");
  if (!sheetId || !cellRange) {
    throw new FeishuSheetsError(
      "Range spec must be in the form sheetId!A1:B10",
      "INVALID_RANGE_SPEC",
      400,
    );
  }
  const [startRaw, endRaw] = cellRange.split(":");
  const start = parseCellRef(startRaw);
  const end = parseCellRef(endRaw ?? startRaw);

  return {
    sheetId,
    startColumn: Math.min(start.column, end.column),
    startRow: Math.min(start.row, end.row),
    endColumn: Math.max(start.column, end.column),
    endRow: Math.max(start.row, end.row),
  };
}

export function buildRangeSpec(sheetId, startRow, endRow, startColumn = 1, endColumn = startColumn) {
  return `${sheetId}!${toCellRef(startRow, startColumn)}:${toCellRef(endRow, endColumn)}`;
}

export function getCellDisplayText(value) {
  if (value == null) return "";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map((item) => getCellDisplayText(item)).join("");
  }
  if (typeof value === "object") {
    if (typeof value.text === "string") {
      return value.text;
    }
    return JSON.stringify(value);
  }
  return String(value);
}

export function isTextMatch(haystack, query, mode = "contains", caseSensitive = false) {
  const source = caseSensitive ? haystack : haystack.toLowerCase();
  const needle = caseSensitive ? query : query.toLowerCase();

  switch (mode) {
    case "exact":
      return source === needle;
    case "regex": {
      const regex = new RegExp(query, caseSensitive ? "" : "i");
      return regex.test(haystack);
    }
    case "contains":
    default:
      return source.includes(needle);
  }
}
