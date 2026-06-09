from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import urllib.error

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")  # set in Vercel env vars
SHEET_ID = os.environ.get("SHEET_ID", "1tWnDNHzRd6L9CxBg0AIegE51gi4Scv_053gWlIWvjXE")
BANK_BIN = "970422"       # MB Bank BIN
ACCOUNT_NO = "1506200499"
ACCOUNT_NAME = "VU DUC MANH"
FUND_NAME = "Cafe + Đá"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ---------- Telegram helpers ----------

def tg_post(method, payload):
    url = f"{BASE_URL}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[tg_post error] {method}: {e}")
        return {}

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_post("sendMessage", payload)

def send_photo(chat_id, photo_url, caption=None):
    payload = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    return tg_post("sendPhoto", payload)

def answer_callback(callback_id, text=""):
    return tg_post("answerCallbackQuery", {"callback_query_id": callback_id, "text": text})

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_post("editMessageText", payload)

def delete_message(chat_id, message_id):
    return tg_post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

# ---------- Google Sheets (public append via Apps Script) ----------

def append_to_sheet(name, amount, user):
    """
    Gọi Google Apps Script Web App để ghi dữ liệu.
    Nếu chưa có Apps Script thì bỏ qua, chỉ log.
    """
    apps_script_url = os.environ.get("APPS_SCRIPT_URL", "")
    if not apps_script_url:
        print(f"[Sheet] No APPS_SCRIPT_URL set — skipping. Data: {name}, {amount}, {user}")
        return False
    try:
        params = urllib.parse.urlencode({"name": name, "amount": amount, "user": user})
        url = f"{apps_script_url}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramBot"})
        with urllib.request.urlopen(req, timeout=10) as r:
            result = r.read().decode()
            print(f"[Sheet] Response: {result}")
            return True
    except Exception as e:
        print(f"[Sheet error] {e}")
        return False

def query_history():
    """Gọi Apps Script lấy tổng quỹ tháng hiện tại.
    Trả None nếu chưa cấu hình APPS_SCRIPT_URL, dict {status:error} nếu lỗi."""
    apps_script_url = os.environ.get("APPS_SCRIPT_URL", "")
    if not apps_script_url:
        return None
    try:
        sep = "&" if "?" in apps_script_url else "?"
        url = f"{apps_script_url}{sep}action=history"
        req = urllib.request.Request(url, headers={"User-Agent": "TelegramBot"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[history error] {e}")
        return {"status": "error"}

# ---------- VietQR ----------

def make_vietqr_url(amount, description):
    desc_encoded = urllib.parse.quote(description)
    return (
        f"https://img.vietqr.io/image/{BANK_BIN}-{ACCOUNT_NO}-compact2.jpg"
        f"?amount={amount}&addInfo={desc_encoded}&accountName={urllib.parse.quote(ACCOUNT_NAME)}"
    )

# ---------- State management (in-memory, simple) ----------
# key: chat_id, value: {"step": "await_amount", "username": "..."}
USER_STATE = {}

# ---------- Main logic ----------

def handle_update(update):
    # Callback query (button press)
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        msg_id  = cq["message"]["message_id"]
        data    = cq.get("data", "")
        user    = cq["from"].get("username") or cq["from"].get("first_name", "Ẩn danh")

        answer_callback(cq["id"])

        if data == "dong_quy":
            USER_STATE[chat_id] = {"step": "await_amount", "username": user}
            edit_message(chat_id, msg_id,
                "💰 <b>Đóng quỹ Cafe + Đá</b>\n\n"
                "Nhập số tiền bạn muốn đóng (VNĐ):\n"
                "<i>Ví dụ: 20000</i>")
        return

    # Text message
    if "message" not in update:
        return

    msg     = update["message"]
    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "").strip()
    user    = msg["from"].get("username") or msg["from"].get("first_name", "Ẩn danh")

    # /start
    if text.startswith("/start"):
        USER_STATE.pop(chat_id, None)
        keyboard = {
            "inline_keyboard": [[
                {"text": "💵 Đóng quỹ Cafe + Đá", "callback_data": "dong_quy"}
            ]]
        }
        send_message(chat_id,
            f"👋 Xin chào <b>{user}</b>!\n\n"
            f"🫙 Quỹ <b>{FUND_NAME}</b> đang mở.\n"
            "Nhấn nút bên dưới để đóng quỹ:",
            reply_markup=keyboard)
        return

    # /xemquy - xem tổng quỹ
    if text.startswith("/xemquy"):
        send_message(chat_id,
            f"📊 Xem quỹ tại:\n"
            f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=0#gid=0")
        return

    # /history - tổng số tiền góp quỹ trong tháng hiện tại
    if text.startswith("/history"):
        data = query_history()
        if data is None:
            send_message(chat_id,
                "⚠️ Lịch sử quỹ chưa được bật.\n"
                "Cần cấu hình <code>APPS_SCRIPT_URL</code> (Google Apps Script) trước nhé.")
            return
        if data.get("status") == "error" or "total" not in data:
            send_message(chat_id, "⚠️ Tạm thời chưa đọc được dữ liệu quỹ. Thử lại sau nhé.")
            return
        total = int(data.get("total", 0))
        count = int(data.get("count", 0))
        month = data.get("month", "")
        send_message(chat_id,
            f"📊 <b>Lịch sử quỹ {FUND_NAME}</b>\n"
            f"🗓 Tháng <b>{month}</b>\n\n"
            f"💰 Tổng đã đóng: <b>{total:,}đ</b>\n"
            f"🧾 Số lượt đóng: <b>{count}</b>")
        return

    # /clear - xóa đoạn hội thoại gần đây
    if text.startswith("/clear"):
        USER_STATE.pop(chat_id, None)
        current_id = msg["message_id"]
        deleted = 0
        misses = 0
        # Telegram: chỉ xóa được tin < 48h; trong chat riêng bot xóa được cả tin của mình lẫn của user.
        for mid in range(current_id, max(0, current_id - 50), -1):
            if delete_message(chat_id, mid).get("ok"):
                deleted += 1
                misses = 0
            else:
                misses += 1
                if misses >= 12:   # đã ra ngoài vùng xóa được → dừng sớm cho nhanh
                    break
        send_message(chat_id,
            f"🧹 Đã dọn <b>{deleted}</b> tin nhắn gần đây.\n"
            "<i>(Telegram không cho xóa tin cũ hơn 48 giờ.)</i>\n\n"
            "Gõ /start để bắt đầu lại 👇")
        return

    # Đang chờ nhập số tiền
    state = USER_STATE.get(chat_id)
    if state and state.get("step") == "await_amount":
        # Xử lý số tiền
        clean = text.replace(",", "").replace(".", "").replace(" ", "").replace("đ", "").replace("vnd","").lower()
        if not clean.isdigit():
            send_message(chat_id, "⚠️ Vui lòng nhập <b>số tiền</b> hợp lệ.\nVí dụ: <code>20000</code>")
            return

        amount = int(clean)

        if amount < 2000:
            USER_STATE.pop(chat_id, None)
            keyboard = {
                "inline_keyboard": [[
                    {"text": "💵 Đóng quỹ lại", "callback_data": "dong_quy"}
                ]]
            }
            send_message(chat_id,
                "❌ <b>Số tiền đóng quỹ quá ít!</b>\n\n"
                "Vui lòng đưa tiền mặt trực tiếp 🙏",
                reply_markup=keyboard)
            return

        # Tạo QR
        description = f"Dong quy {FUND_NAME} - {user}"
        qr_url = make_vietqr_url(amount, description)

        send_message(chat_id,
            f"📲 <b>QR Chuyển khoản</b>\n\n"
            f"💵 Số tiền: <b>{amount:,}đ</b>\n"
            f"🏦 Ngân hàng: MB Bank\n"
            f"👤 Chủ TK: {ACCOUNT_NAME}\n"
            f"🔢 Số TK: <code>{ACCOUNT_NO}</code>\n"
            f"📝 Nội dung: <code>{description}</code>\n\n"
            "⏳ Quét QR bên dưới để chuyển khoản:")

        send_photo(chat_id, qr_url,
            "✅ Sau khi chuyển khoản thành công, nhấn <b>Xác nhận</b> bên dưới.")

        # Lưu state để chờ xác nhận
        USER_STATE[chat_id] = {
            "step": "await_confirm",
            "username": user,
            "amount": amount
        }

        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Tôi đã chuyển khoản thành công!", "callback_data": f"confirm_{amount}"}
            ]]
        }
        send_message(chat_id, "👆 Nhấn xác nhận sau khi chuyển:", reply_markup=keyboard)
        return

    # Xác nhận sau chuyển khoản (callback)
    # (handled above in callback_query section — but in case text slips through)
    send_message(chat_id,
        "Gõ /start để bắt đầu đóng quỹ nhé! 😊")


def handle_confirm_callback(update):
    """Handle confirm button - separate pass for confirm_ prefix"""
    if "callback_query" not in update:
        return False
    cq   = update["callback_query"]
    data = cq.get("data", "")
    if not data.startswith("confirm_"):
        return False

    chat_id = cq["message"]["chat"]["id"]
    user    = cq["from"].get("username") or cq["from"].get("first_name", "Ẩn danh")
    answer_callback(cq["id"])

    state = USER_STATE.get(chat_id, {})
    amount = state.get("amount") or int(data.replace("confirm_", ""))

    # Ghi sheet
    append_to_sheet(user, amount, user)

    USER_STATE.pop(chat_id, None)

    keyboard = {
        "inline_keyboard": [[
            {"text": "💵 Đóng quỹ tiếp", "callback_data": "dong_quy"}
        ]]
    }
    send_message(chat_id,
        f"🎉 <b>Xung quỹ thành công!</b>\n\n"
        f"👤 Người đóng: <b>{user}</b>\n"
        f"💰 Số tiền: <b>{amount:,}đ</b>\n"
        f"🫙 Quỹ: <b>{FUND_NAME}</b>\n\n"
        "Cảm ơn bạn đã đóng góp! ☕🧊",
        reply_markup=keyboard)
    return True


# ---------- Vercel handler ----------

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        try:
            update = json.loads(body)
            print(f"[Update] {json.dumps(update)[:300]}")

            # Try confirm callback first
            if not handle_confirm_callback(update):
                handle_update(update)

        except Exception as e:
            print(f"[Error] {e}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass
