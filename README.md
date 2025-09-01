# 🚀 Local Coding Agent (LCA)

یک ابزار CLI قدرتمند برای کمک به کدنویسی با استفاده از هوش مصنوعی به صورت کاملاً محلی.

## 📋 ویژگی‌ها

- 🤖 اتصال به LLM (پیش‌فرض: GapGPT) برای کمک به کدنویسی
- 📁 مدیریت فایل‌ها و پوشه‌ها به صورت ایمن
- 🔧 اجرای دستورات شل با لاگ‌گیری کامل
- 📝 تولید و ویرایش فایل‌ها با استفاده از هوش مصنوعی
- 🔍 تحلیل پروژه و تولید نقشه کد
- ✅ مدیریت TODO برای پیگیری وظایف
- 🛡️ تأیید کاربر برای عملیات‌های حساس

## 🚀 نصب

```bash
# Clone the repository
git clone <repo-url>
cd local-coding-agent

# Install in development mode
pip install -e .
```

## ⚙️ پیکربندی

1. فایل `.env` را از روی `.env.example` بسازید:
```bash
cp .env.example .env
```

2. کلید API خود را در `.env` تنظیم کنید:
```
LLM_API_KEY=your-api-key-here
```

## 📚 استفاده

### دستورات پایه

```bash
# نمایش اطلاعات پیکربندی
lca whoami

# تحلیل پروژه
lca analyze

# پرسش از هوش مصنوعی
lca ask "سوال شما"

# برنامه‌ریزی یک کار
lca plan "هدف شما"

# مدیریت TODO
lca todo add "کار جدید"
lca todo list
lca todo done 1

# اجرای دستور شل
lca run "ls -la"

# تولید فایل جدید
lca write --path file.py --from "یک اسکریپت پایتون ساده بساز"

# ویرایش فایل موجود
lca edit --path file.py --inst "تابع main اضافه کن"

# حذف فایل
lca delete --path file.py

# دریافت و اعمال patch
lca patch --from "باگ در تابع X را رفع کن"
```

### راهنمای کامل

برای دیدن راهنمای کامل هر دستور:
```bash
lca --help
lca <command> --help
```

## 🔒 امنیت

- تمام عملیات حساس نیاز به تأیید کاربر دارند
- از فلگ `--yes` برای اجرای غیرتعاملی استفاده کنید
- کلید API هرگز در لاگ‌ها ذخیره نمی‌شود

## 📂 ساختار پروژه

```
.
├── pyproject.toml
├── README.md
├── .env.example
├── .gitignore
├── agent/
│   ├── cli.py         # رابط خط فرمان
│   ├── config.py      # پیکربندی
│   ├── llm.py         # ارتباط با LLM
│   ├── analyze.py     # تحلیل پروژه
│   ├── state.py       # مدیریت وضعیت
│   ├── prompts.py     # قالب‌های پرامپت
│   └── tools/
│       ├── fs.py      # ابزارهای فایل سیستم
│       ├── shell.py   # ابزارهای شل
│       └── patch.py   # ابزارهای پچ
└── .agent/
    ├── logs/          # لاگ‌های عملیات
    ├── reports/       # گزارش‌ها
    └── state.json     # وضعیت TODO
```

## 🤝 مشارکت

برای مشارکت در توسعه:
1. Fork کنید
2. شاخه جدید بسازید (`feature/your-feature`)
3. تغییرات را Commit کنید
4. Pull Request بفرستید

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.