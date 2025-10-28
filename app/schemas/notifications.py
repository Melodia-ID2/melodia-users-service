from app.schemas.base import ApiBaseModel


class NotificationPreferencesResponse(ApiBaseModel):
    new_releases: bool
    followed_activity: bool
    social_activity: bool


class NotificationPreferencesUpdate(ApiBaseModel):
    new_releases: bool | None = None
    followed_activity: bool | None = None
    social_activity: bool | None = None
