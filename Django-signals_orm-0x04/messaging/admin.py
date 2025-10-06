from django.contrib import admin
from .models import Message, Notification


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "short_content", "timestamp")
    list_filter = ("sender", "receiver", "timestamp")
    search_fields = ("content", "sender__email", "receiver__email", "sender__username", "receiver__username")

    @admin.display(description="content")
    def short_content(self, obj):
        return (obj.content[:50] + "…") if len(obj.content) > 50 else obj.content


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at", "user")
    search_fields = ("message__content", "user__email", "user__username")
