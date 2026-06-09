/**
 * Google Apps Script - Paste vào Extensions > Apps Script trong Google Sheet
 * Deploy > Manage deployments > Edit (✏️) > Version: New version > Deploy
 *   (hoặc New deployment > Web App; Execute as: Me; Who has access: Anyone)
 *
 * Hành động (query param):
 *   (mặc định)      ?name=...&amount=...&user=...  → ghi 1 dòng đóng quỹ (Thời gian là Date thật)
 *   ?action=history                                → tổng tiền + số lượt THÁNG HIỆN TẠI
 *   ?action=dump                                   → (chẩn đoán) trả 10 dòng cuối + kiểu dữ liệu
 */

const TZ = "Asia/Ho_Chi_Minh";

function doGet(e) {
  try {
    const sheet  = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    const action = ((e && e.parameter && e.parameter.action) || "add").toLowerCase();

    if (action === "history") return handleHistory(sheet);
    if (action === "dump")    return handleDump(sheet);

    // ----- Ghi một lần đóng quỹ -----
    const name   = e.parameter.name   || "Ẩn danh";
    const amount = parseInt(e.parameter.amount) || 0;
    const user   = e.parameter.user   || "unknown";
    const now    = new Date();

    ensureHeader(sheet);

    // Ghi Date THẬT (không phải chuỗi) để tránh Sheets hiểu nhầm dd/MM ↔ MM/dd theo locale.
    sheet.appendRow([now, name, amount, "@" + user]);

    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow, 1).setNumberFormat("dd/MM/yyyy HH:mm:ss"); // hiển thị giờ VN kiểu VN
    sheet.getRange(lastRow, 3).setNumberFormat("#,##0");

    return jsonOut({ status: "ok", row: lastRow });

  } catch (err) {
    return jsonOut({ status: "error", message: err.toString() });
  }
}

function ensureHeader(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(["Thời gian", "Tên Telegram", "Số tiền (VNĐ)", "Username"]);
    const h = sheet.getRange(1, 1, 1, 4);
    h.setFontWeight("bold");
    h.setBackground("#4CAF50");
    h.setFontColor("#FFFFFF");
  }
}

/** Trả "MM/yyyy" của 1 ô thời gian dù là Date hay chuỗi dd/MM/yyyy. */
function monthKeyOf(t) {
  if (t instanceof Date && !isNaN(t.getTime())) {
    return Utilities.formatDate(t, TZ, "MM/yyyy");
  }
  const s = String(t).trim();
  if (!s) return "";
  const datePart = s.split(" ")[0];      // dd/MM/yyyy
  const p = datePart.split("/");
  if (p.length === 3) {
    const mm = ("0" + p[1]).slice(-2);    // bảo đảm 2 chữ số
    return mm + "/" + p[2];
  }
  const d = new Date(s);                  // fallback
  if (!isNaN(d.getTime())) return Utilities.formatDate(d, TZ, "MM/yyyy");
  return "";
}

/** Tổng tiền + số lượt đóng quỹ của THÁNG HIỆN TẠI (giờ VN). */
function handleHistory(sheet) {
  const curMonth = Utilities.formatDate(new Date(), TZ, "MM/yyyy");
  const lastRow  = sheet.getLastRow();
  let total = 0, count = 0;

  if (lastRow >= 2) {
    const values = sheet.getRange(2, 1, lastRow - 1, 3).getValues(); // [Thời gian, Tên, Số tiền]
    for (let i = 0; i < values.length; i++) {
      if (monthKeyOf(values[i][0]) === curMonth) {
        total += parseInt(values[i][2]) || 0;
        count++;
      }
    }
  }
  return jsonOut({ status: "ok", month: curMonth, total: total, count: count });
}

/** Chẩn đoán: 10 dòng cuối kèm kiểu dữ liệu ô thời gian. */
function handleDump(sheet) {
  const lastRow = sheet.getLastRow();
  const n = Math.min(10, Math.max(0, lastRow - 1));
  const rows = [];
  if (n > 0) {
    const start = lastRow - n + 1;
    const vals  = sheet.getRange(start, 1, n, 4).getValues();
    for (let i = 0; i < vals.length; i++) {
      const t = vals[i][0];
      rows.push({
        time: String(t),
        timeType: (t instanceof Date) ? "Date" : typeof t,
        monthKey: monthKeyOf(t),
        name: vals[i][1],
        amount: vals[i][2],
        note: vals[i][3],
      });
    }
  }
  return jsonOut({
    status: "ok",
    sheetName: sheet.getName(),
    lastRow: lastRow,
    curMonth: Utilities.formatDate(new Date(), TZ, "MM/yyyy"),
    rows: rows,
  });
}

function jsonOut(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
