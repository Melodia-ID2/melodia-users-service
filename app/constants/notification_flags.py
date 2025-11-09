BIT_KEEP_HISTORY = 1 << 0
BIT_NOTIFICATIONS_NEW_RELEASES = 1 << 1
BIT_NOTIFICATIONS_FOLLOW_ACTIVITY = 1 << 2
BIT_NOTIFICATIONS_SHARED_CONTENT = 1 << 3
BIT_NOTIFICATIONS_NEW_FOLLOWERS = 1 << 4
BIT_NOTIFICATIONS_PLAYLIST_LIKES = 1 << 5

NOTIFICATION_BITS_MASK = (
    BIT_NOTIFICATIONS_NEW_RELEASES
    | BIT_NOTIFICATIONS_FOLLOW_ACTIVITY
    | BIT_NOTIFICATIONS_SHARED_CONTENT
    | BIT_NOTIFICATIONS_NEW_FOLLOWERS
    | BIT_NOTIFICATIONS_PLAYLIST_LIKES
)

DEFAULT_PREFERENCES = (
    BIT_KEEP_HISTORY
    | BIT_NOTIFICATIONS_NEW_RELEASES
    | BIT_NOTIFICATIONS_FOLLOW_ACTIVITY
    | BIT_NOTIFICATIONS_SHARED_CONTENT
    | BIT_NOTIFICATIONS_NEW_FOLLOWERS
    | BIT_NOTIFICATIONS_PLAYLIST_LIKES
)


class NotificationPreferences:
    def __init__(self, value: int):
        self.value = value

    def has(self, flag: int) -> bool:
        return (self.value & flag) != 0

    def set(self, flag: int, enabled: bool) -> None:
        if enabled:
            self.value |= flag
        else:
            self.value &= ~flag

    def as_dict(self) -> dict[str, bool]:
        return {
            "new_releases": self.has(BIT_NOTIFICATIONS_NEW_RELEASES),
            "follow_activity": self.has(BIT_NOTIFICATIONS_FOLLOW_ACTIVITY),
            "shared_content": self.has(BIT_NOTIFICATIONS_SHARED_CONTENT),
            "new_followers": self.has(BIT_NOTIFICATIONS_NEW_FOLLOWERS),
            "playlist_likes": self.has(BIT_NOTIFICATIONS_PLAYLIST_LIKES),
        }

    @staticmethod
    def from_dict(data: dict[str, bool]) -> int:
        value = 0
        if data.get("new_releases", False):
            value |= BIT_NOTIFICATIONS_NEW_RELEASES
        if data.get("follow_activity", False):
            value |= BIT_NOTIFICATIONS_FOLLOW_ACTIVITY
        if data.get("shared_content", False):
            value |= BIT_NOTIFICATIONS_SHARED_CONTENT
        if data.get("new_followers", False):
            value |= BIT_NOTIFICATIONS_NEW_FOLLOWERS
        if data.get("playlist_likes", False):
            value |= BIT_NOTIFICATIONS_PLAYLIST_LIKES
        return value
