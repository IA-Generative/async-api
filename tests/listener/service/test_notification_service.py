from unittest.mock import Mock

import pytest

from listener.services.notifier_service import BaseNotifier, NotificationException, NotificationService


@pytest.fixture
def notification_service() -> NotificationService:
    async def notify(callback: dict, message: dict) -> None:
        pass

    a_notifier: BaseNotifier = Mock()
    a_notifier.accept.side_effect = lambda n: n["message_type"] == "a"
    a_notifier.notify.side_effect = notify

    b_notifier: BaseNotifier = Mock()
    b_notifier.accept.side_effect = lambda n: n["message_type"] == "b"
    b_notifier.notify.side_effect = notify

    return NotificationService([a_notifier, b_notifier])


@pytest.mark.asyncio
async def test_notify_a(notification_service: NotificationService) -> None:
    callback: dict = {"message_type": "a"}
    await notification_service.notify(callback=callback, message={})
    notification_service.notifiers[0].notify.assert_called()
    notification_service.notifiers[1].notify.assert_not_called()


@pytest.mark.asyncio
async def test_notify_b(notification_service: NotificationService) -> None:
    callback: dict = {"message_type": "b"}
    await notification_service.notify(callback=callback, message={})
    notification_service.notifiers[0].notify.assert_not_called()
    notification_service.notifiers[1].notify.assert_called()


@pytest.mark.asyncio
async def test_notify_failure(notification_service: NotificationService) -> None:
    callback: dict = {"message_type": "c"}
    with pytest.raises(NotificationException):
        await notification_service.notify(callback=callback, message={})
