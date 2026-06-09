# 🤖 Bot Quỹ Cafe + Đá — Telegram Bot

## Cấu trúc project
```
IceCoffeeBot/
├── api/
│   └── webhook.py          # Main bot logic (Vercel serverless)
├── vercel.json             # Vercel config
├── requirements.txt        # Không cần thư viện ngoài
├── google_apps_script.js   # Script dán vào Google Sheet
├── setup_webhook.py        # Chạy 1 lần để đăng ký webhook
├── .env.example            # Mẫu biến môi trường
└── .gitignore
```

---

## 🚀 Hướng dẫn deploy (5 bước)

### Bước 1: Push lên GitHub
> Repo: https://github.com/ManhVuCode/IceCoffeeBot (đã tạo & push sẵn)

### Bước 2: Deploy lên Vercel
1. Vào https://vercel.com → **New Project**
2. Import repo GitHub vừa tạo
3. Vercel tự nhận cấu hình → nhấn **Deploy**

### Bước 3: Cài Google Apps Script (để ghi Sheet)
1. Mở Google Sheet của bạn
2. **Extensions > Apps Script**
3. Xóa code cũ, paste toàn bộ nội dung file `google_apps_script.js`
4. **Deploy > New Deployment**
   - Type: **Web App**
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Copy **URL** của Web App

### Bước 4: Thêm Environment Variables trên Vercel
Vào **Project Settings > Environment Variables**, thêm:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | `<token bot của bạn từ @BotFather>` |
| `APPS_SCRIPT_URL` | URL từ bước 3 |

> ⚠️ **Không bao giờ** dán token thật vào README/code. Token chỉ đặt trong Vercel Environment Variables hoặc file `.env` (đã `.gitignore`).

Sau đó **Redeploy** project.

### Bước 5: Đăng ký Webhook
```bash
python setup_webhook.py https://your-project.vercel.app
```
Thay `your-project.vercel.app` bằng domain Vercel thật của bạn.

---

## ✅ Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| `/start` | Hiện nút **Đóng quỹ Cafe + Đá** |
| Nhập số tiền | Bot hỏi số tiền cần đóng |
| < 2,000đ | Thông báo đưa tiền mặt |
| ≥ 2,000đ | Tạo QR VietQR MB Bank tự động |
| Xác nhận | Ghi vào Google Sheet |
| `/xemquy` | Link xem Google Sheet |

---

## 🔧 Tuỳ chỉnh
Sửa trong `api/webhook.py`:
- `FUND_NAME` — tên quỹ
- `ACCOUNT_NO` — số tài khoản
- `ACCOUNT_NAME` — tên chủ tài khoản
- `BANK_BIN` — BIN ngân hàng (MB Bank = 970422)
