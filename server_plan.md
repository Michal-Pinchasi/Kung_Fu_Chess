# Server Plan — Kung Fu Chess (Phase 1)

## מטרה

להריץ משחק Kung Fu Chess יחיד על המחשב המקומי, כאשר השרת הוא מקור האמת
היחיד עבור הלוח, חוקי המשחק, הזמן, הניקוד ותוצאת המשחק. שני לקוחות
גרפיים מתחברים אליו דרך WebSocket ומציגים את אותו מצב לוח.

## גבולות שלב 1

- שרת אחד, תהליך Python אחד.
- כתובת מקומית בלבד: `ws://localhost:8765`.
- שני שחקנים לכל היותר.
- החיבור הראשון מקבל לבן; השני מקבל שחור.
- אין צופים, חדרי משחק, התחברות מרחוק או מסד נתונים בשלב זה.

## רכיבים

| קובץ | אחריות |
| --- | --- |
| `network/websocket_server.py` | שרת ה-WebSocket, ניהול חיבורים, קצב העדכון ושידור snapshots. |
| `network/session_manager.py` | שיוך לבן/שחור והרשאת פקודות לפי הכלי שעל הלוח. |
| `network/command_parser.py` | פענוח פקודות רשת כגון `WPe2e4` ו-`WPe2J`. |
| `network/snapshot_serializer.py` | המרת `GameSnapshot` למבנה JSON לשידור. |
| `engin/game_engine.py` | מנוע חוקי המשחק, אנימציות, זמן, ניקוד ותוצאת המשחק. |
| `events/message_bus.py` | ערוץ Pub/Sub פנימי לאירועי משחק. |
| `events/game_events.py` | הגדרת אירועי מהלך, Jump, ניקוד וסיום משחק. |

## זרימת חיבור

```text
Client 1 ── connect ──> GameServer ──> assigned_color: w
Client 2 ── connect ──> GameServer ──> assigned_color: b
Client 3 ── connect ──> GameServer ──> error: game_full, then close
```

בעת ניתוק של לקוח, הצבע שלו משתחרר ויכול להינתן ללקוח הבא שמתחבר.

## פרוטוקול הודעות

### פקודות לקוח → שרת

| פעולה | פורמט | דוגמה |
| --- | --- | --- |
| מהלך | `<Color><Kind><From><To>` | `WPe2e4` |
| Jump | `<Color><Kind><Square>J` | `WPe2J` |

`Color` הוא `W` או `B`, וסוגי הכלים הם `K`, `Q`, `R`, `B`, `N`, `P`.
השרת אינו סומך על הצבע והסוג שנשלחו: הוא בודק מול הלוח החי שהכלי שייך
לשחקן המחובר ושמותר לו לבצע את הפעולה.

### הודעות שרת → לקוח

```json
{"type": "assigned_color", "color": "w"}
```

```json
{"type": "snapshot", "data": {"board_width": 8, "board_height": 8, "pieces": []}}
```

```json
{"type": "error", "reason": "not_your_piece"}
```

ה־snapshot כולל את הכלים, מיקומיהם, מצב האנימציה, היסטוריית המהלכים,
ניקוד ודגל סיום המשחק.

## לולאת המשחק

1. `GameServer` מתקדם כל `tick_ms` מילישניות (ברירת מחדל: 100).
2. הוא מפעיל `GameEngine.wait(tick_ms)`.
3. מנוע המשחק מסיים תנועות, לכידות, מנוחות ו־Jump לפי חוקי המשחק.
4. השרת ממיר את המצב ל־JSON ומשדר snapshot לכל הלקוחות המחוברים.

## Message Bus

המנוע מפרסם אירועים פנימיים, בלי תלות בשרת או בממשק:

- `MOVE_STARTED`
- `JUMP_STARTED`
- `MOVE_COMPLETED`
- `SCORE_CHANGED`
- `GAME_OVER`

בשלב 1 השרת נרשם ל־`GAME_OVER` כדי לשדר מצב מעודכן מיד. בעתיד ניתן
להירשם לאותם אירועים עבור סאונד, אנימציות, לוגים או שמירה למסד נתונים.

## הפעלה

הפעלה ידנית של השרת:

```powershell
python -m network.websocket_server
```

הפעלה מקומית של שרת ושני לקוחות:

```powershell
python start_local_match.py
```

או בלחיצה כפולה על `start_local_match.bat`.

## המשך אפשרי

- חדרי משחק ומזהה משחק.
- צופים.
- אימות משתמשים.
- שמירת משחקים ולוג מהלכים.
- שרת מרוחק עם TLS.
