from app.schemas.base import ApiBaseModel


class NotificationPreferencesResponse(ApiBaseModel):
    new_releases: bool
    followed_activity: bool
    social_activity: bool
