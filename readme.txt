# Django News Portal

Полнофункциональный новостной портал на Django с системой аутентификации, группами и правами.

## Функциональность

- ✅ Аутентификация через email и социальные сети (Google - Временно не работает, Yandex)
- ✅ Система групп: common и authors
- ✅ Автоматическое добавление в группу common при регистрации
- ✅ Кнопка "Стать автором" для получения прав
- ✅ CRUD операции для новостей и статей
- ✅ Поиск и фильтрация новостей
- ✅ Постраничный вывод
- ✅ Кастомный фильтр цензуры

## Установка

1. Клонируйте репозиторий:

git clone https://github.com/ваш-username/django-news-portal.git
cd django-news-portal

2.Установите зависимости:
pip install -r requirements.txt

3.Выполните миграции:
python manage.py migrate

4.Создайте суперпользователя:
python manage.py createsuperuser

5.Запустите сервер:
python manage.py runserver