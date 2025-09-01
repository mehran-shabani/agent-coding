SYSTEM_PROMPT = (
    "تو یک ایجنت کدنویسی لوکال هستی؛ فقط در workspace تعیین‌شده کار کن؛ "
    "تغییرات را به صورت unified diff ارائه بده؛ پاسخ‌ها کوتاه و ایمن باشند."
)


def plan_prompt(goal: str) -> str:
    return (
        "با توجه به هدف زیر، فهرستی از گام‌های عملی کوتاه تولید کن.\n"
        f"هدف: {goal}\n"
        "خروجی: یک لیست بولتی از گام‌ها."
    )


def write_file_prompt(desc: str, path: str) -> str:
    return (
        "توضیح را به فایل اجرایی تبدیل کن؛ ساختار ساده و مینیمال باشد.\n"
        f"مسیر فایل: {path}\n"
        f"توضیح: {desc}"
    )


def edit_file_prompt(instruction: str, path: str, current_text: str) -> str:
    return (
        "فقط بخش‌های لازم تغییر کند؛ خروجی unified diff باشد.\n"
        f"مسیر فایل: {path}\n"
        f"متن فعلی:\n{current_text}\n"
        f"دستور ویرایش: {instruction}"
    )


def multi_patch_prompt(desc: str) -> str:
    return (
        "پچ چندفایلی با مسیر نسبی از ریشهٔ پروژه بده؛ هر فایل در hunk جدا باشد.\n"
        f"توضیح: {desc}"
    )
