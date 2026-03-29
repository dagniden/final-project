# Эндпоинты API

## Процесс `1-BM`

### Список эндпоинтов

- `POST /books` — создать книгу
- `GET /books` — получить список книг, выполнить поиск и фильтрацию
- `GET /books/{id}` — получить карточку книги
- `PATCH /books/{id}` — изменить данные книги
- `DELETE /books/{id}` — удалить книгу

### Трассировка требований

| Юз кейс | Требование | Эндпоинт |
| --- | --- | --- |
| `1-BM-US-01` | Создать книгу | `POST /books` |
| `1-BM-US-02` | Просмотреть список книг | `GET /books` |
| `1-BM-US-03` | Просмотреть карточку книги | `GET /books/{id}` |
| `1-BM-US-04` | Изменить данные книги | `PATCH /books/{id}` |
| `1-BM-US-05` | Удалить книгу | `DELETE /books/{id}` |
| `1-BM-US-06` | Найти книгу по названию | `GET /books` |
| `1-BM-US-07` | Найти книги по автору | `GET /books` |
| `1-BM-US-08` | Найти книги по жанру | `GET /books` |
| `1-BM-US-09` | Проверить наличие книги | `GET /books`, `GET /books/{id}` |
| `1-BM-US-10` | Получить список книг по нескольким критериям | `GET /books` |
| `1-BM-US-11` | Проверить корректность введенных данных книги | `POST /books`, `PATCH /books/{id}` |
| `1-BM-US-12` | Ограничить доступ к управлению книгами | `POST /books`, `PATCH /books/{id}`, `DELETE /books/{id}` |

## Процесс `2-AM`

### Список эндпоинтов

- `POST /authors` — создать автора
- `GET /authors` — получить список авторов
- `GET /authors/{id}` — получить карточку автора
- `PATCH /authors/{id}` — изменить данные автора
- `DELETE /authors/{id}` — удалить автора

### Трассировка требований

| Юз кейс | Требование | Эндпоинт |
| --- | --- | --- |
| `2-AM-US-01` | Создать автора | `POST /authors` |
| `2-AM-US-02` | Просмотреть список авторов | `GET /authors` |
| `2-AM-US-03` | Просмотреть карточку автора | `GET /authors/{id}` |
| `2-AM-US-04` | Изменить данные автора | `PATCH /authors/{id}` |
| `2-AM-US-05` | Удалить автора | `DELETE /authors/{id}` |
| `2-AM-US-06` | Проверить корректность введенных данных автора | `POST /authors`, `PATCH /authors/{id}` |
| `2-AM-US-07` | Ограничить доступ к управлению авторами | `POST /authors`, `PATCH /authors/{id}`, `DELETE /authors/{id}` |

## Процесс `3-UM`

### Список эндпоинтов

- `POST /auth/register` — зарегистрировать пользователя
- `POST /auth/login` — авторизовать пользователя
- `GET /users/{id}` — получить информацию о пользователе
- `GET /users/me` — получить информацию о текущем пользователе
- `GET /users` — получить список пользователей
- `POST /users/me/telegram/link` — начать или завершить привязку Telegram
- `DELETE /users/me/telegram/link` — отвязать Telegram
- `GET /users/me/notifications/channels` — получить список подключенных каналов уведомлений

### Трассировка требований

| Юз кейс | Требование | Эндпоинт |
| --- | --- | --- |
| `3-UM-US-01` | Зарегистрировать пользователя | `POST /auth/register` |
| `3-UM-US-02` | Авторизовать пользователя | `POST /auth/login` |
| `3-UM-US-03` | Просмотреть информацию о пользователе | `GET /users/{id}`, `GET /users/me` |
| `3-UM-US-04` | Получить список пользователей | `GET /users` |
| `3-UM-US-05` | Проверить корректность введенных регистрационных данных | `POST /auth/register` |
| `3-UM-US-06` | Ограничить доступ к данным пользователей | `GET /users/{id}`, `GET /users/me`, `GET /users` |

## Процесс `4-BI`

### Список эндпоинтов

- `POST /issues` — оформить выдачу книги
- `GET /issues` — получить список выдач
- `GET /issues/{id}` — получить информацию о конкретной выдаче
- `PATCH /issues/{id}/return` — зафиксировать возврат книги
- `GET /books/{id}/availability` — проверить возможность выдачи книги
- `POST /issues/{id}/reminder/send` — вручную отправить напоминание о возврате книги
- `GET /notifications` — получить журнал отправленных уведомлений

### Трассировка требований

| Юз кейс | Требование | Эндпоинт |
| --- | --- | --- |
| `4-BI-US-01` | Оформить выдачу книги | `POST /issues` |
| `4-BI-US-02` | Просмотреть список выдач | `GET /issues` |
| `4-BI-US-03` | Просмотреть информацию о конкретной выдаче | `GET /issues/{id}` |
| `4-BI-US-04` | Отследить статус возврата книги | `GET /issues`, `GET /issues/{id}` |
| `4-BI-US-05` | Зафиксировать возврат книги | `PATCH /issues/{id}/return` |
| `4-BI-US-06` | Проверить возможность выдачи книги | `GET /books/{id}/availability` |
| `4-BI-US-07` | Ограничить доступ к операциям выдачи | `POST /issues`, `PATCH /issues/{id}/return` |
| `4-BI-US-08` | Отправить напоминание о возврате книги за 5 дней | `POST /issues/{id}/reminder/send`, фоновая задача отправки уведомлений |

## Процесс `5-AC`

### Список эндпоинтов

- `POST /auth/login` — выполнить аутентификацию и получить JWT-токен
- `GET /auth/me` — проверить подлинность токена и получить данные текущего пользователя

### Трассировка требований

| Юз кейс | Требование | Эндпоинт |
| --- | --- | --- |
| `5-AC-US-01` | Выполнить аутентификацию пользователя | `POST /auth/login` |
| `5-AC-US-02` | Проверить подлинность запроса | `GET /auth/me` |
| `5-AC-US-03` | Предоставить доступ к разрешенным операциям | `GET /auth/me`, `POST /users/me/telegram/link`, `DELETE /users/me/telegram/link`, `GET /users/me/notifications/channels`, `POST /issues/{id}/reminder/send`, `GET /notifications`, защищенные бизнес-эндпоинты |
| `5-AC-US-04` | Запретить доступ к защищенным операциям | `GET /auth/me`, `POST /users/me/telegram/link`, `DELETE /users/me/telegram/link`, `GET /users/me/notifications/channels`, `POST /issues/{id}/reminder/send`, `GET /notifications`, защищенные бизнес-эндпоинты |
| `5-AC-US-05` | Ограничить доступ к управлению книгами и авторами | `POST /books`, `PATCH /books/{id}`, `DELETE /books/{id}`, `POST /authors`, `PATCH /authors/{id}`, `DELETE /authors/{id}` |
| `5-AC-US-06` | Ограничить доступ к данным пользователей и операциям выдачи | `GET /users/{id}`, `GET /users`, `GET /users/me/notifications/channels`, `POST /users/me/telegram/link`, `DELETE /users/me/telegram/link`, `POST /issues`, `PATCH /issues/{id}/return`, `POST /issues/{id}/reminder/send`, `GET /notifications` |
