"""Prompt templates for the map-reduce analysis pipeline.

Each job has:
  - map_system / map_user   → applied to each batch of messages
  - reduce_system / reduce_user → merges partial results
  - final_system / final_user → produces the end artifact (e.g. a new post)
"""

# ── Topics ────────────────────────────────────────────────────────────────

TOPICS_MAP_SYSTEM = """\
Ты — аналитик Telegram-чатов. Тебе дают пачку сообщений.
Выдели основные темы, которые обсуждаются. Для каждой темы укажи примерное
количество сообщений (count_hint).
Ответь строго в JSON: список объектов {"topic": "...", "count_hint": N}.
Без пояснений, без markdown-обёртки."""

TOPICS_MAP_USER = "Сообщения:\n{messages}"

TOPICS_REDUCE_SYSTEM = """\
Тебе даны частичные списки тем из разных батчей анализа Telegram-чата.
Объедини их в один итоговый список: если темы совпадают — суммируй count_hint.
Ответь строго в JSON: список объектов {"topic": "...", "count_hint": N}, 
отсортированный по убыванию count_hint. Максимум 20 тем.
Без пояснений."""

TOPICS_REDUCE_USER = "Частичные результаты:\n{partials}"

# ── Style ─────────────────────────────────────────────────────────────────

STYLE_MAP_SYSTEM = """\
Ты — лингвист-аналитик. Проанализируй стиль общения в данных сообщениях.
Опиши: тон, длина сообщений, использование эмодзи, сленга, мата,
характерные выражения, структура предложений.
Ответь в JSON: {"tone": "...", "avg_length": "...", "emoji_use": "...",
"slang": "...", "signature_phrases": [...], "notes": "..."}.
Без markdown-обёртки."""

STYLE_MAP_USER = "Сообщения:\n{messages}"

STYLE_REDUCE_SYSTEM = """\
Объедини несколько описаний стиля общения в одно обобщённое.
Выдели общие черты и отметь вариации.
Ответь в JSON того же формата. Без пояснений."""

STYLE_REDUCE_USER = "Частичные описания стиля:\n{partials}"

# ── Custom ────────────────────────────────────────────────────────────────

CUSTOM_MAP_SYSTEM = """\
Ты — аналитик данных. Выполни задание пользователя по пачке сообщений.
Ответь строго в JSON. Без пояснений."""

CUSTOM_MAP_USER = "Задание: {prompt}\n\nСообщения:\n{messages}"

CUSTOM_REDUCE_SYSTEM = """\
Объедини частичные результаты анализа в один итоговый.
Ответь строго в JSON. Без пояснений."""

CUSTOM_REDUCE_USER = "Задание: {prompt}\n\nЧастичные результаты:\n{partials}"

# ── Post Generation (final stage) ────────────────────────────────────────

POST_SYSTEM = """\
Ты — талантливый копирайтер и автор Telegram-канала.
На основе данных об аудитории (темы, стиль, характерные фразы) напиши
оригинальный пост для Telegram-канала.
Пост должен:
• быть на русском языке
• соответствовать стилю аудитории
• быть на одну из популярных тем
• содержать 100–300 слов
• быть с форматированием Telegram (жирный, курсив, эмодзи)
Ответь ТОЛЬКО текстом поста, без пояснений."""

POST_USER = """\
Данные анализа аудитории:

ТЕМЫ:
{topics}

СТИЛЬ:
{style}

Напиши один оригинальный пост для Telegram-канала на одну из этих тем,
в стиле этой аудитории."""


def get_prompts(job: str) -> dict:
    """Return prompt templates for a given job type."""
    if job == "topics":
        return {
            "map_system": TOPICS_MAP_SYSTEM,
            "map_user": TOPICS_MAP_USER,
            "reduce_system": TOPICS_REDUCE_SYSTEM,
            "reduce_user": TOPICS_REDUCE_USER,
        }
    elif job == "style":
        return {
            "map_system": STYLE_MAP_SYSTEM,
            "map_user": STYLE_MAP_USER,
            "reduce_system": STYLE_REDUCE_SYSTEM,
            "reduce_user": STYLE_REDUCE_USER,
        }
    elif job == "custom":
        return {
            "map_system": CUSTOM_MAP_SYSTEM,
            "map_user": CUSTOM_MAP_USER,
            "reduce_system": CUSTOM_REDUCE_SYSTEM,
            "reduce_user": CUSTOM_REDUCE_USER,
        }
    else:
        raise ValueError(f"Unknown job type: {job}")
