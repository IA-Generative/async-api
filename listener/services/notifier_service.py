# ---------------------------------
# Notification service exception
# ---------------------------------
class NotificationException(Exception):
    pass


# ---------------------------------
# Base Notifier
# ---------------------------------
class BaseNotifier:
    def accept(self, callback: dict) -> bool:  # noqa: ARG002
        return False

    async def notify(self, callback: dict, message: dict) -> None:
        pass


# ---------------------------------
# Notification service
# ---------------------------------
class NotificationService:
    def __init__(self, notifiers: list[BaseNotifier]) -> None:
        self.notifiers = notifiers

    def find_notifier_for_message(self, callback: dict) -> BaseNotifier | None:
        for notifier in self.notifiers:
            if notifier.accept(callback):
                return notifier
        return None

    async def notify(self, callback: dict, message: dict) -> None:
        notifier = self.find_notifier_for_message(callback)
        if notifier is None:
            raise NotificationException(f"No notifier found for callback {callback}")
        await notifier.notify(callback, message)
