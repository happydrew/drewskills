import lark from "@larksuiteoapi/node-sdk";

import { FeishuSheetsError } from "./errors.mjs";
import {
  buildRangeSpec,
  encodeRangeSpec,
  getCellDisplayText,
  isTextMatch,
  normalizeRangeSpec,
  parseRangeSpec,
  toCellRef,
} from "./utils.mjs";

const DEFAULT_READ_OPTIONS = {
  valueRenderOption: "UnformattedValue",
  dateTimeRenderOption: "FormattedString",
};

function unwrapRequestResult(response) {
  const payload = response?.data ?? response;
  if (payload?.code !== undefined && payload.code !== 0) {
    throw new FeishuSheetsError(
      payload.msg ?? "Feishu API request failed",
      payload.code,
      undefined,
      payload.data,
    );
  }
  return payload?.data ?? payload;
}

function toError(error) {
  if (error instanceof FeishuSheetsError) {
    return error;
  }
  if (error?.response?.data) {
    return new FeishuSheetsError(
      error.response.data.msg ?? error.message ?? "Feishu API request failed",
      error.response.data.code,
      error.response.status,
      error.response.data.data,
    );
  }
  return new FeishuSheetsError(error instanceof Error ? error.message : String(error));
}

export class FeishuSheetsToolkit {
  constructor(credentials) {
    this.client = new lark.Client({
      appId: credentials.appId,
      appSecret: credentials.appSecret,
    });
  }

  async getSpreadsheetInfo(spreadsheetToken) {
    try {
      const response = await this.client.sheets.spreadsheet.get({
        path: { spreadsheet_token: spreadsheetToken },
      });
      const spreadsheet = response.data?.spreadsheet;
      if (!spreadsheet?.token || !spreadsheet.title || !spreadsheet.url) {
        throw new FeishuSheetsError("Spreadsheet metadata is incomplete");
      }
      return {
        ownerId: spreadsheet.owner_id,
        title: spreadsheet.title,
        token: spreadsheet.token,
        url: spreadsheet.url,
      };
    } catch (error) {
      throw toError(error);
    }
  }

  async listWorksheets(spreadsheetToken) {
    try {
      const response = await this.client.sheets.spreadsheetSheet.query({
        path: { spreadsheet_token: spreadsheetToken },
      });
      return (response.data?.sheets ?? []).map((sheet) => ({
        sheetId: sheet.sheet_id ?? "",
        title: sheet.title ?? "",
        index: sheet.index ?? 0,
        hidden: sheet.hidden ?? false,
        rowCount: sheet.grid_properties?.row_count ?? 0,
        columnCount: sheet.grid_properties?.column_count ?? 0,
        frozenRowCount: sheet.grid_properties?.frozen_row_count,
        frozenColumnCount: sheet.grid_properties?.frozen_column_count,
        merges: sheet.merges,
        resourceType: sheet.resource_type,
      }));
    } catch (error) {
      throw toError(error);
    }
  }

  async readRange(spreadsheetToken, rangeSpec, options = {}) {
    const merged = { ...DEFAULT_READ_OPTIONS, ...options };
    try {
      const response = await this.client.request({
        method: "GET",
        url: `/open-apis/sheets/v2/spreadsheets/${spreadsheetToken}/values/${encodeRangeSpec(rangeSpec)}`,
        params: {
          valueRenderOption: merged.valueRenderOption,
          dateTimeRenderOption: merged.dateTimeRenderOption,
        },
      });
      const data = unwrapRequestResult(response);
      const valueRange = data.valueRange;
      return {
        range: valueRange.range,
        majorDimension: valueRange.majorDimension,
        values: valueRange.values ?? [],
        revision: data.revision ?? valueRange.revision,
        spreadsheetToken: data.spreadsheetToken ?? spreadsheetToken,
      };
    } catch (error) {
      throw toError(error);
    }
  }

  async readMultipleRanges(spreadsheetToken, rangeSpecs, options = {}) {
    return {
      ranges: await Promise.all(
        rangeSpecs.map((rangeSpec) => this.readRange(spreadsheetToken, rangeSpec, options)),
      ),
    };
  }

  async writeRange(spreadsheetToken, rangeSpec, values, options = {}) {
    try {
      const response = await this.client.request({
        method: "PUT",
        url: `/open-apis/sheets/v2/spreadsheets/${spreadsheetToken}/values`,
        params: {
          valueInputOption: options.valueInputOption ?? "RAW",
        },
        data: {
          valueRange: {
            range: rangeSpec,
            values,
          },
        },
      });
      const data = unwrapRequestResult(response);
      return {
        updatedRange: data.updatedRange,
        updatedRows: data.updatedRows,
        updatedColumns: data.updatedColumns,
        updatedCells: data.updatedCells,
        revision: data.revision,
        spreadsheetToken,
      };
    } catch (error) {
      throw toError(error);
    }
  }

  async searchSheet(spreadsheetToken, sheetId, sheetTitle, sheetRowCount, sheetColumnCount, options) {
    return this.#searchWorksheets(
      spreadsheetToken,
      [{ sheetId, title: sheetTitle, rowCount: sheetRowCount, columnCount: sheetColumnCount }],
      options,
    );
  }

  async searchAllSheets(spreadsheetToken, options) {
    const worksheets = await this.listWorksheets(spreadsheetToken);
    return this.#searchWorksheets(
      spreadsheetToken,
      worksheets.map((sheet) => ({
        sheetId: sheet.sheetId,
        title: sheet.title,
        rowCount: sheet.rowCount,
        columnCount: sheet.columnCount,
      })),
      options,
    );
  }

  async #searchWorksheets(spreadsheetToken, sheets, options) {
    const mode = options.mode ?? "contains";
    const caseSensitive = options.caseSensitive ?? false;
    const maxResults = options.maxResults ?? 200;
    const chunkRows = options.chunkRows ?? 500;
    const matches = [];

    for (const sheet of sheets) {
      const searchRange = options.range
        ? normalizeRangeSpec(sheet.sheetId, options.range)
        : buildRangeSpec(sheet.sheetId, 1, sheet.rowCount, 1, sheet.columnCount);
      const parsedRange = parseRangeSpec(searchRange);

      for (let chunkStart = parsedRange.startRow; chunkStart <= parsedRange.endRow; chunkStart += chunkRows) {
        const chunkEnd = Math.min(chunkStart + chunkRows - 1, parsedRange.endRow);
        const chunkRange = buildRangeSpec(
          sheet.sheetId,
          chunkStart,
          chunkEnd,
          parsedRange.startColumn,
          parsedRange.endColumn,
        );
        const read = await this.readRange(spreadsheetToken, chunkRange);

        for (let rowOffset = 0; rowOffset < read.values.length; rowOffset += 1) {
          const row = read.values[rowOffset] ?? [];
          for (let colOffset = 0; colOffset < row.length; colOffset += 1) {
            const rawValue = row[colOffset];
            const value = getCellDisplayText(rawValue);
            if (!value) continue;
            if (!isTextMatch(value, options.query, mode, caseSensitive)) continue;

            const rowIndex = chunkStart + rowOffset;
            const columnIndex = parsedRange.startColumn + colOffset;
            matches.push({
              sheetId: sheet.sheetId,
              sheetTitle: sheet.title,
              range: chunkRange,
              cell: toCellRef(rowIndex, columnIndex),
              rowIndex,
              columnIndex,
              value,
              rawValue,
            });

            if (matches.length >= maxResults) {
              return {
                spreadsheetToken,
                query: options.query,
                mode,
                caseSensitive,
                totalMatches: matches.length,
                truncated: true,
                matches,
              };
            }
          }
        }
      }
    }

    return {
      spreadsheetToken,
      query: options.query,
      mode,
      caseSensitive,
      totalMatches: matches.length,
      truncated: false,
      matches,
    };
  }
}
