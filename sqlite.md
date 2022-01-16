# sqlite tables
```sql
select name from sqlite_master where type='table' order by name;
```

# sqlite schema
```sql
select sql from sqlite_master where name='<table-name>';
```

# parse table fields
```sql
CREATE TABLE "transactions_transaction" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "pan" varchar(255) NOT NULL,
    "datetime" datetime NOT NULL,
    "amount" integer unsigned NOT NULL CHECK ("amount" >= 0),
    "currency" integer unsigned NOT NULL CHECK ("currency" >= 0),
    "receipt" text NOT NULL CHECK ((JSON_VALID("receipt") OR "receipt" IS NULL)),
    "status" varchar(255) NULL,
    "type" varchar(255) NOT NULL,
    "payment_system" varchar(255) NULL,
    "shift_id" integer NULL REFERENCES "transactions_shift" ("id") DEFERRABLE INITIALLY DEFERRED,
    "business" varchar(255) NOT NULL,
    "company_id" integer NULL REFERENCES "companies_company" ("id") DEFERRABLE INITIALLY DEFERRED,
    "extra" text NOT NULL CHECK ((JSON_VALID("extra") OR "extra" IS NULL))
)
```

# инфа
```sql
/* Ошибка с папкой заготовок: The specified path was not found */
/* Разделитель изменен на ; */
/* Подключение к D:\Projects\Work\repositories\JoinPAY\beta\retailbud\db.sqlite3 с помощью SQLite, с именем пользователя , используя пароль: No… */
PRAGMA busy_timeout=30000;
SELECT DATETIME();
SELECT sqlite_version();
/* Соединено. Идентификатор процесса: 8528 */
SELECT * FROM pragma_database_list;
/* Открытие сеанса «Unnamed» */
/* #1634496361: Access violation at address 0000005073300000 in module 'heidisql.exe'. Execution of address 0000005073300000 Message CharCode:13 Msg:256 */
/* Подключение к D:\Projects\Work\repositories\JoinPAY\beta\retailbud\db.sqlite3 с помощью SQLite, с именем пользователя , используя пароль: No… */
PRAGMA busy_timeout=30000;
SELECT DATETIME();
SELECT sqlite_version();
/* Соединено. Идентификатор процесса: 8528 */
SELECT * FROM pragma_database_list;
/* Открытие сеанса «JoinPAY local» */
/* Открытие сеанса «JoinPAY local» */
/* Открытие сеанса «JoinPAY local» */
/* Открытие сеанса «JoinPAY local» */
/* Подключение к D:\Projects\Work\repositories\JoinPAY\beta\retailbud\db.sqlite3 закрыто в 2021-10-06 14:15:14 */
/* Открытие сеанса «JoinPAY local» */
SELECT * FROM "db".sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';
```
