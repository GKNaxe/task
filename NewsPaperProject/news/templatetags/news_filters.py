from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

CENSOR_WORDS = [
    'редиска', 'плохой', 'нехороший', 'брань', 'ругательство',
]


@register.filter(name='censor')
@stringfilter  # проверяет, что значение - строка
def censor(value):
    if not isinstance(value, str):
        raise ValueError(f"Фильтр 'censor' применяется только к строкам, получен: {type(value)}")

    result = value
    for word in CENSOR_WORDS:
        # Ищем слово в разных регистрах
        word_lower = word.lower()
        word_title = word.title()  # с заглавной буквы

        # Заменяем все вхождения слова (сохраняя регистр первой буквы)
        if word_lower in result.lower():
            # Создаём цензурированную версию слова
            censored = word[0] + '*' * (len(word) - 1)

            # Заменяем с учётом регистра
            result = result.replace(word_lower, censored)
            result = result.replace(word_title, censored)

    return result