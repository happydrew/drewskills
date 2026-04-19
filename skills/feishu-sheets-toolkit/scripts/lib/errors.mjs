export class FeishuSheetsError extends Error {
  constructor(message, code, status, details) {
    super(message);
    this.name = "FeishuSheetsError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}
