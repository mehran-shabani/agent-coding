# 🚀 Local Coding Agent (LCA)

یک ایجنت کدنویسی لوکال قدرتمند برای مدیریت پروژه‌ها با رابط خط فرمان.

## ✨ ویژگی‌ها

- 🔧 **CLI قدرتمند**: رابط خط فرمان با Typer
- 🤖 **پشتیبانی از LLM**: اتصال به GapGPT و سایر مدل‌ها
- 📁 **مدیریت فایل**: عملیات ایمن روی فایل‌ها و پوشه‌ها
- 🔍 **تحلیل پروژه**: تولید نقشه کد و مستندات
- 📝 **مدیریت TODO**: سیستم وظایف داخلی
- 🛡️ **امنیت**: تأیید کاربر برای عملیات مخرب
- 📊 **گزارش‌گیری**: لاگ‌ها و گزارش‌های تفصیلی

## 🚀 نصب

```bash
# نصب از مخزن محلی
pip install -e .

# یا نصب مستقیم
pip install local-coding-agent
```

## ⚙️ پیکربندی

1. فایل `.env` را از `.env.example` کپی کنید:
```bash
cp .env.example .env
```

2. کلید API خود را تنظیم کنید:
```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.gapgpt.app/v1
LLM_MODEL=gpt-5o
```

## 📖 استفاده

### دستورات اصلی

```bash
# نمایش اطلاعات پیکربندی
lca whoami

# تحلیل پروژه و تولید CODEMAP.md
lca analyze

# پرسش از LLM
lca ask "چگونه می‌توانم این کد را بهبود دهم؟"

# برنامه‌ریزی و افزودن به TODO
lca plan "اضافه کردن سیستم احراز هویت"

# مدیریت TODO
lca todo add "رفع باگ در ماژول کاربر"
lca todo list
lca todo done 1

# اجرای فرمان شل
lca run "npm install"

# تولید فایل جدید
lca write --path src/main.py --from "تابع اصلی برنامه"

# ویرایش فایل
lca edit --path src/main.py --inst "اضافه کردن validation"

# حذف فایل (با تأیید)
lca delete --path temp.txt

# اعمال پچ
lca patch --from "رفع مشکل در تابع login"
```

### گزینه‌های پیشرفته

```bash
# تحلیل مسیر خاص
lca analyze ./src

# تولید فایل با بازنویسی
lca write --path file.txt --from "محتوای جدید" --overwrite

# ویرایش با اعمال خودکار
lca edit --path file.py --inst "تغییرات" --yes

# حذف بدون تأیید
lca delete --path file.txt --yes

# اعمال پچ بدون تأیید
lca patch --from "تغییرات" --apply
```

## 🏗️ ساختار پروژه

```
local-coding-agent/
├── agent/
│   ├── cli.py          # رابط خط فرمان
│   ├── config.py       # مدیریت پیکربندی
│   ├── llm.py          # ارتباط با LLM
│   ├── analyze.py      # تحلیل پروژه
│   ├── state.py        # مدیریت وضعیت
│   ├── prompts.py      # پرامپت‌های پایه
│   └── tools/
│       ├── fs.py       # عملیات فایل
│       ├── shell.py    # اجرای شل
│       └── patch.py    # مدیریت پچ
├── .agent/
│   ├── logs/           # لاگ‌ها
│   ├── reports/        # گزارش‌ها
│   └── state.json      # وضعیت
├── pyproject.toml
├── README.md
├── .env.example
└── .gitignore
```

## 🔧 توسعه

### نصب برای توسعه

```bash
git clone <repository>
cd local-coding-agent
pip install -e .[dev]
```

### اجرای تست‌ها

```bash
pytest
```

### فرمت‌بندی کد

```bash
black .
isort .
```

## 🛡️ امنیت

- تمام عملیات حذف و بازنویسی نیاز به تأیید کاربر دارند
- لاگ‌ها محتوای حساس را ثبت نمی‌کنند
- مسیرها به صورت Cross-Platform پشتیبانی می‌شوند
- اجرای غیرتعاملی فقط با فلگ مجاز است

## 📝 لاگ‌ها و گزارش‌ها

- لاگ‌ها در `.agent/logs/` ذخیره می‌شوند
- گزارش‌های تناقض در `.agent/reports/` قرار می‌گیرند
- وضعیت در `.agent/state.json` نگهداری می‌شود

## 🤝 مشارکت

1. شاخه جدید ایجاد کنید: `feature/local-coding-agent/<agent-id>`
2. تغییرات را commit کنید
3. Pull Request به شاخه `develop` ارسال کنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## 🆘 پشتیبانی

در صورت بروز مشکل یا سوال، لطفاً issue جدید ایجاد کنید.