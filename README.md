# Kung Fu Chess

## משחק מקומי לשני שחקנים

התקינו פעם אחת את התלויות:

`python -m pip install -r requirements.txt`

לאחר מכן לחצו פעמיים על `start_local_match.bat` (או הריצו `python start_local_match.py`).
ייפתחו שני חלונות. בכל חלון נרשמים או מתחברים דרך מסך OpenCV שבתוך המשחק:

- `Tab` עובר בין שם המשתמש לסיסמה.
- `R` מחליף בין כניסה להרשמה.
- `Enter` שולח את הפרטים.

סיסמאות נשמרות ב-SQLite כ-hash מומלח PBKDF2 בלבד. כל שחקן מתחיל ב-1200 נקודות ELO,
והדירוג והסטטיסטיקה מתעדכנים אוטומטית בסיום המשחק. אפשר לשנות את ההגדרות ב-`config/multiplayer_settings.json`
או דרך משתני הסביבה `KUNG_FU_CHESS_STARTING_RATING`, `KUNG_FU_CHESS_ELO_K_FACTOR`,
`KUNG_FU_CHESS_ELO_DIVISOR`, `KUNG_FU_CHESS_ELO_BASE` ו-`KUNG_FU_CHESS_DB_PATH`.

השחקן הראשון שנכנס הוא לבן והשני שחור. לחיצה שמאלית בוחרת כלי ויעד; ליחצה ימנית מפעילה Jump.
יוצאים מכל חלון עם `Q` או `Esc`.
