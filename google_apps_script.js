/**
 * Google Apps Script - Paste vào Tools > Script Editor trong Google Sheet
 * Sau đó Deploy > New Deployment > Web App
 * - Execute as: Me
 * - Who has access: Anyone
 * Copy URL và paste vào APPS_SCRIPT_URL trong Vercel Environment Variables
 */

function doGet(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    const name   = e.parameter.name   || "Ẩn danh";
    const amount = parseInt(e.parameter.amount) || 0;
    const user   = e.parameter.user   || "unknown";
    const now    = new Date();
    
    // Thêm header nếu sheet trống
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Thời gian", "Tên Telegram", "Số tiền (VNĐ)", "Ghi chú"]);
      // Format header
      const headerRange = sheet.getRange(1, 1, 1, 4);
      headerRange.setFontWeight("bold");
      headerRange.setBackground("#4CAF50");
      headerRange.setFontColor("#FFFFFF");
    }
    
    // Ghi dữ liệu
    sheet.appendRow([
      Utilities.formatDate(now, "Asia/Ho_Chi_Minh", "dd/MM/yyyy HH:mm:ss"),
      name,
      amount,
      "Đóng quỹ Cafe + Đá"
    ]);
    
    // Format cột số tiền
    const lastRow = sheet.getLastRow();
    sheet.getRange(lastRow, 3).setNumberFormat("#,##0");
    
    return ContentService
      .createTextOutput(JSON.stringify({status: "ok", row: lastRow}))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch(err) {
    return ContentService
      .createTextOutput(JSON.stringify({status: "error", message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
