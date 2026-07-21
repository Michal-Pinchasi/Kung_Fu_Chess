# View Architecture Specification — Kung Fu Chess

## מטרה

לשמור על ממשק משתמש גרפי שמציג את מצב המשחק בלבד ומעביר פעולות משתמש
למנוע המקומי או לשרת. שכבת התצוגה אינה מכילה חוקי שחמט ואינה משנה את
הלוח ישירות.

## מבנה התצוגה

```text
view/ui/net_app.py
  ├─ RemoteGameClient          חיבור WebSocket ברקע
  ├─ RemoteEngine              מתאם לממשק GameEngine הקיים
  ├─ Controller + MouseHandler קלט עכבר
  └─ GameScene                 ציור פריים
       ├─ GameCanvas
       ├─ BoardRenderer
       ├─ PieceRenderer
       ├─ OverlayRenderer
       └─ MoveHistoryRenderer
```

## נקודת הכניסה

### משחק מקומי ישן

`view/ui/app.py` יוצר `GameEngine` ולוח מקומיים באותו תהליך. הוא נשאר
זמין לבדיקות ולמצב משחק מקומי ללא רשת.

### משחק רשת

`view/ui/net_app.py` הוא נקודת הכניסה ללקוח משחק רשת.

1. יוצר `RemoteGameClient` ומתחבר לשרת.
2. ממתין לקבלת צבע (`w` או `b`).
3. יוצר `RemoteEngine`.
4. בונה את אותם רכיבי ציור קיימים.
5. מריץ לולאת OpenCV עד לחיצה על `Q` או `Esc`.

## תפקיד הרכיבים

| קובץ | אחריות |
| --- | --- |
| `view/ui/net_app.py` | הרכבת חלון משחק רשת ולולאת הציור. |
| `network/client/remote_game_client.py` | קליטת snapshots ושליחת פקודות ברקע, ללא חסימת OpenCV. |
| `network/client/remote_engine.py` | API תואם ל-`GameEngine` עבור `Controller` ו-`GameScene`. |
| `input/controller.py` | פרוטוקול שתי לחיצות: בחירת מקור ואז יעד. |
| `view/ui/input/mouse_handler.py` | המרת אירועי OpenCV לקריאות ל־Controller. |
| `view/ui/scene/game_scene.py` | תיאום ציור כל רכיבי המסך מתוך `snapshot()`. |
| `view/ui/rendering/*` | ציור לוח, כלים, בחירה, ניקוד והיסטוריה. |

## זרימת תצוגה

```text
GameServer
    │ snapshot JSON
    ▼
RemoteGameClient
    │ GameSnapshot
    ▼
RemoteEngine.snapshot()
    ▼
GameScene.render()
    ▼
OpenCV window
```

הלקוח אינו מחשב חוקיות מהלכים ואינו מתקדם בזמן. השרת שולח את המצב
העדכני, והלקוח מצייר אותו.

## זרימת קלט

```text
לחיצה שמאלית
  → MouseHandler
  → Controller
  → RemoteEngine.request_move()
  → RemoteGameClient.send_command()
  → WebSocket server
```

- לחיצה שמאלית ראשונה בוחרת כלי של השחקן המקומי.
- לחיצה שמאלית שנייה מגדירה משבצת יעד ושולחת מהלך.
- לחיצה ימנית שולחת בקשת `Jump`.
- אימות סופי של בעלות וחוקיות הפעולה מתבצע בשרת בלבד.

## מצב בחירה

`selected_cell` הוא מצב ממשק מקומי בלבד. הוא נשמר ב־`Controller` של
אותו חלון כדי לסמן את המשבצת שנבחרה. הוא אינו חלק ממצב המשחק הסמכותי
בשרת ואינו נשלח לשחקן השני.

## הפרדת אחריות

| שכבה | אסור לה לעשות |
| --- | --- |
| Renderers | לשנות לוח או להחליט אם מהלך חוקי. |
| RemoteGameClient | לפרש חוקי משחק או לצייר. |
| RemoteEngine | לעדכן את זמן המשחק המקומית. |
| Server | לגשת לעכבר, ל־OpenCV או לנכסי תמונה. |

## הפעלת שני חלונות

`start_local_match.py` יוצר שלושה תהליכים:

```text
GameServer
Player 1 window (White)
Player 2 window (Black)
```

כל חלון הוא לקוח עצמאי ולכן ניתן ללחוץ ולשחק בו בנפרד, אך שניהם מקבלים
את אותו snapshot מהשרת.

## הרחבות עתידיות

- הודעת סטטוס חיבור/ניתוק בתוך החלון.
- צליל ואנימציות מבוססי Message Bus.
- מסך התחברות ובחירת חדר.
- מצב צפייה.
- תמיכה בדפדפן במקום OpenCV.
