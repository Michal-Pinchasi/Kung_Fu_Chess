"""Rendering-only component for the room and matchmaking menu."""


class RoomScreenRenderer:
    QUICK_BOX = (350, 470, 250, 70)
    CREATE_BOX = (610, 470, 250, 70)
    JOIN_BOX = (870, 470, 250, 70)

    @property
    def action_boxes(self):
        return {"quick": self.QUICK_BOX, "create": self.CREATE_BOX, "join": self.JOIN_BOX}

    def draw(self, frame, username, rating, status):
        frame.draw_rect(280, 190, 740, 430, color=(20, 20, 20, 255), alpha=0.88)
        frame.put_text(f"Welcome {username}", 450, 285, 1.0,
                       color=(40, 215, 255, 255), thickness=2)
        frame.put_text(f"ELO: {rating}", 560, 345, 0.8, thickness=2)
        frame.put_text(status, 365, 430, 0.65, thickness=2)
        for box in self.action_boxes.values():
            frame.draw_rect(*box, color=(40, 215, 255, 255), thickness=2)
        frame.put_text("QUICK PLAY", 380, 515, 0.62, thickness=2)
        frame.put_text("CREATE ROOM", 630, 515, 0.62, thickness=2)
        frame.put_text("JOIN ROOM", 900, 515, 0.62, thickness=2)
        frame.put_text("P/ENTER: quick   C: create   J: join   L: leave", 400, 570, 0.5)
        frame.put_text("ESC: exit", 580, 610, 0.5)
