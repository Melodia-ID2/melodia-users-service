BIT_KEEP_HISTORY = 1 << 0
BIT_NOTIFICATIONS_NEW_RELEASES = 1 << 1
BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY = 1 << 2
BIT_NOTIFICATIONS_SOCIAL_ACTIVITY = 1 << 3

DEFAULT_PREFERENCES = (
    BIT_KEEP_HISTORY |
    BIT_NOTIFICATIONS_NEW_RELEASES |
    BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY |
    BIT_NOTIFICATIONS_SOCIAL_ACTIVITY
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
            "followed_activity": self.has(BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY),
            "social_activity": self.has(BIT_NOTIFICATIONS_SOCIAL_ACTIVITY),
        }

    @staticmethod
    def from_dict(data: dict[str, bool]) -> int:
        value = 0
        if data.get("new_releases", False):
            value |= BIT_NOTIFICATIONS_NEW_RELEASES
        if data.get("followed_activity", False):
            value |= BIT_NOTIFICATIONS_FOLLOWED_ACTIVITY
        if data.get("social_activity", False):
            value |= BIT_NOTIFICATIONS_SOCIAL_ACTIVITY
        return value
