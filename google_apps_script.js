/**
 * Google Apps Script - Paste vào Extensions > Apps Script trong Google Sheet
 * Sau đó Deploy > New Deployment > Web App
 *   - Execute as: Me
 *   - Who has access: Anyone
 * Copy URL và paste vào APPS_SCRIPT_URL (Vercel Environment Variables).
 *
 * Hỗ trợ 2 hành động (qua query param):
 *   (mặc định)        ?name=...&amount=...&user=...  → ghi 1 dòng đóng quỹ (kèm thời gian)
 *   ?action=history                                  → trả tổng tiền + số lượt của THÁNG HIỆN TẠI
 */

const TZ = "Asia/Ho_Chi_Minh";

function doGet(e) {
  try {
    const sheet  = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    const action = ((e && e.parameter && e.parameter.action) || "add").toLowerCase();

    if (action === "history") {
      return handleHistory(sheet);
    }

    // ----- Ghi một lần đóng quỹ -----
    const name   = e.parameter.name   || "Ẩn danh";
    const amount = parseInt(e.parameter.amount) || 0;
    const user   = e.parameter.user   || "unknown";
    const now    = new Date();

    ensureHeader(sheet);

    sheet.appendRow([
      Utilities.formatDate(now, TZ, "dd/MM/yyyy HH:mm:ss"),  // Thời gian đóng quỹ (giờ VN)
      name,
      amount,
      "@" + user
    ]);

    const lastRow = sheet.getLastRow();
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

/** Tổng tiền + số lượt đóng quỹ của THÁNG HIỆN TẠI (theo giờ VN). */
function handleHistory(sheet) {
  const curMonth = Utilities.formatDate(new Date(), TZ, "MM/yyyy"); // vd "06/2026"
  const lastRow  = sheet.getLastRow();
  let total = 0, count = 0;

  if (lastRow >= 2) {
    const values = sheet.getRange(2, 1, lastRow - 1, 3).getValues(); // [Thời gian, Tên, Số tiền]
    for (let i = 0; i < values.length; i++) {
      const t   = values[i][0];
      const amt = parseInt(values[i][2]) || 0;

      let mmYYYY = "";
      if (t instanceof Date) {
        mmYYYY = Utilities.formatDate(t, TZ, "MM/yyyy");
      } else {
        const datePart = String(t).split(" ")[0]; // dd/MM/yyyy
        const parts = datePart.split("/");
        if (parts.length === 3) mmYYYY = parts[1] + "/" + parts[2];
      }

      if (mmYYYY === curMonth) { total += amt; count++; }
    }
  }

  return jsonOut({ status: "ok", month: curMonth, total: total, count: count });
}

function jsonOut(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
