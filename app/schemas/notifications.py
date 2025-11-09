from app.schemas.base import ApiBaseModel


class NotificationPreferencesResponse(ApiBaseModel):
    new_releases: bool
    follow_activity: bool
    shared_content: bool
    new_followers: bool
    playlist_likes: bool


class NotificationPreferencesUpdate(ApiBaseModel):
    new_releases: bool
    follow_activity: bool
    shared_content: bool
    new_followers: bool
    playlist_likes: bool
