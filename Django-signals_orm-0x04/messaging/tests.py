from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .models import Message, Notification, MessageHistory

User = get_user_model()


class NotificationSignalTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="pass12345")
        self.bob = User.objects.create_user(username="bob", email="bob@example.com", password="pass12345")

    def test_notification_created_on_new_message(self):
        self.assertEqual(Notification.objects.count(), 0)
        msg = Message.objects.create(sender=self.alice, receiver=self.bob, content="Hello Bob")
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.bob)
        self.assertEqual(notif.message, msg)
        self.assertFalse(notif.is_read)

    def test_no_duplicate_notification_on_update(self):
        msg = Message.objects.create(sender=self.alice, receiver=self.bob, content="First")
        self.assertEqual(Notification.objects.count(), 1)
        msg.content = "Edited"
        msg.save()  # should NOT create another
        self.assertEqual(Notification.objects.count(), 1)

    def test_unique_user_message_notification(self):
        msg = Message.objects.create(sender=self.alice, receiver=self.bob, content="Only one notif")
        self.assertEqual(Notification.objects.filter(user=self.bob, message=msg).count(), 1)
        with self.assertRaises(IntegrityError):
            Notification.objects.create(user=self.bob, message=msg)  # violates unique_together

class MessageEditHistoryTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="pass123")
        self.bob = User.objects.create_user(username="bob", email="bob@example.com", password="pass123")

    def test_message_edit_creates_history(self):
        msg = Message.objects.create(sender=self.alice, receiver=self.bob, content="Original")
        self.assertFalse(msg.edited)
        self.assertEqual(MessageHistory.objects.count(), 0)

        # update content
        msg.content = "Edited content"
        msg.save()

        # message should be marked edited
        msg.refresh_from_db()
        self.assertTrue(msg.edited)

        # history created
        histories = MessageHistory.objects.filter(message=msg)
        self.assertEqual(histories.count(), 1)
        hist = histories.first()
        self.assertEqual(hist.old_content, "Original")
        self.assertIsNotNone(hist.edited_at)
