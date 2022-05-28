class Player:
    """
        A class that represents a player in a lobby.

        ...

        Attributes
        ----------
        username : str
            username of the player
        sid : str
            sid of the player
        user_obj : user
            user object (row from user_tbl)

        Methods
        -------
        add_points(points):
            Adds the given amount of points to the player's current points.
        is_guest():
            Returns true if the player is a guest, else false.
        """

    def __init__(self, username, sid, user_obj):
        self.username = username
        self.score = 0
        self.sid = sid
        self.user = user_obj

    def add_points(self, points):
        """Adds the given amount of points to the player's current points."""
        self.score += points

    def is_guest(self):
        """Returns true if the player is a guest, else false."""
        return "Guest" in self.username

    def __str__(self):
        """Returns a string representing the player."""
        return "Player '" + self.username + "' has score: '" + str(self.score) + "'"
