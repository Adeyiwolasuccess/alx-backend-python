from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Conversation, ConversationParticipant, Message


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ("user_id", "email", "first_name", "last_name", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)

    # We removed username; use email instead
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone_number", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "role", "password1", "password2")}),
    )
    readonly_fields = ("created_at",)
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("conversation_id", "created_at")
    search_fields = ("conversation_id",)


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ("conversation", "user", "joined_at")
    search_fields = ("conversation__conversation_id", "user__email")
    list_select_related = ("conversation", "user")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("message_id", "conversation", "sender", "sent_at")
    search_fields = ("message_id", "sender__email", "conversation__conversation_id", "message_body")
    list_filter = ("sent_at",)
    list_select_related = ("conversation", "sender")
