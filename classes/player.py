class Player:
    def __init__(self, username, sid, user_obj):
        self.username = username
        self.score = 0
        self.sid = sid
        self.user = user_obj

    def add_points(self, points):
        self.score += points

    def __str__(self):
        return "Player '" + self.username + "' has score: '" + str(self.score) + "'"

    def is_guest(self):
        return "Guest" in self.username
