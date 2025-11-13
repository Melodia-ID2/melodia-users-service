from typing import Any
from firebase_admin import messaging
from app.core.firebase import get_firebase_app


class FCMService:
    def __init__(self):
        self.app = None
    
    def _ensure_initialized(self):
        if self.app is None:
            self.app = get_firebase_app()
    
    def send_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
        image_url: str | None = None
    ) -> bool:
        self._ensure_initialized()
        
        try:
            notification = messaging.Notification(title=title, body=body, image=image_url)
            
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='melodia_notifications'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default', badge=1)
                    )
                )
            )
            
            response = messaging.send(message)
            print(f"Successfully sent notification: {response}")
            return True
            
        except messaging.UnregisteredError:
            print(f"Token is unregistered: {token}")
            return False
        except Exception as e:
            print(f"Error sending notification to {token}: {e}")
            return False
    
    def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str] | None = None,
        image_url: str | None = None
    ) -> dict[str, Any]:
        self._ensure_initialized()
        
        if not tokens:
            return {"success_count": 0, "failure_count": 0, "failed_tokens": []}
        
        if len(tokens) > 500:
            tokens = tokens[:500]
        
        try:
            notification = messaging.Notification(title=title, body=body, image=image_url)
            
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='melodia_notifications'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default', badge=1)
                    )
                )
            )
            
            response = messaging.send_each_for_multicast(message)
            
            failed_tokens = []
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(tokens[idx])
            
            print(f"Multicast sent. Success: {response.success_count}, Failed: {response.failure_count}")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "failed_tokens": failed_tokens
            }
            
        except Exception as e:
            print(f"Error sending multicast notification: {e}")
            return {
                "success_count": 0,
                "failure_count": len(tokens),
                "failed_tokens": tokens
            }

fcm_service = FCMService()