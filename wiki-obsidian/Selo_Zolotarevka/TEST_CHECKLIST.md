# TEST_CHECKLIST

## Smoke
- [ ] Файл `wordpress/mu-plugins/zolotarevka-backend.php` загружается без PHP fatal.
- [ ] В админке появились CPT из P0 списка.
- [ ] Таксономии `content_section` и `sports_kind` доступны в нужных CPT.

## Роли и права
- [ ] Можно назначить роли: `school_editor`, `sports_editor`, `farm_editor`, `content_moderator`, `community_author`.
- [ ] `content_moderator` видит очередь комментариев на модерации.

## Модерация
- [ ] Новый комментарий без истории публикаций не публикуется сразу.
- [ ] POST формы `zolo_submit_news` создает запись `bulletin_board` со статусом `pending`.

## REST
- [ ] `GET /wp-json/zolo/v1/content/school_news` отдает JSON-список опубликованных записей.
- [ ] Невалидный `type` возвращает `400`.

## Безопасность
- [ ] Отсутствие/невалидный nonce на форме дает `403`.
- [ ] Пустые поля формы отклоняются с `400`.

---
**Связанные страницы:** [[BACKEND_PLAN|План бэкенда]], [[IMPLEMENTATION_NOTES|Заметки по реализации]], [[HANDOFF_FRONTEND_SECURITY|Передача фронтенд+security]]
