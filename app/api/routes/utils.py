from app.common.exception_handlers import ErrorCode, RequestError
from app.db.models.accounts import User
from app.db.models.base import File
from app.db.models.chat import Chat, Message
from app.db.models.profiles import Friend, Notification
from tortoise.expressions import Q
from tortoise.query_utils import Prefetch


async def get_requestee_and_friend_obj(user, username, status=None):
    # Get and validate username existence
    requestee = await User.get_or_none(username=username)
    if not requestee:
        raise RequestError(
            err_code=ErrorCode.NON_EXISTENT,
            err_msg="User does not exist!",
            status_code=404,
        )

    friend = Friend.filter(
        Q(requester_id=user.id, requestee_id=requestee.id)
        | Q(requester_id=requestee.id, requestee=user.id)
    )
    if status:
        friend = friend.filter(status=status)
    friend = await friend.get_or_none()
    return requestee, friend


def get_notifications_queryset(current_user):
    # Fetch current user notifications
    notifications = (
        Notification.filter(receivers__id=current_user.id)
        .select_related("sender", "sender__avatar", "post", "comment", "reply")
        .order_by("-created_at")
    )
    return notifications


# Update group chat users m2m
async def update_group_chat_users(instance, action, data):
    if not data:
        return
    if action == "add":
        await instance.users.add(*data)
    elif action == "remove":
        await instance.users.remove(*data)
    else:
        raise ValueError("Invalid Action")


# Create file object
async def create_file(file_type=None):
    file = None
    if file_type:
        file = await File.create(resource_type=file_type)
    return file


async def get_chats_queryset(user):
    chats = (
        Chat.filter(Q(owner=user) | Q(users__id=user.id))
        .select_related("owner", "owner__avatar", "image")
        .order_by("-updated_at")
        .prefetch_related(
            Prefetch(
                "messages",
                queryset=Message.all()
                .select_related("sender", "sender__avatar", "file")
                .order_by("-created_at")
                .limit(1),
                to_attr="latest_message",
            )
        )
        .distinct()
    )
    return chats


async def get_chat_object(user, chat_id):
    chat = (
        await Chat.filter(Q(owner=user) | Q(users__id=user.id))
        .select_related("owner", "owner__avatar", "image")
        .prefetch_related("users", "users__avatar")
        .get_or_none(id=chat_id)
    )
    if not chat:
        raise RequestError(
            err_code=ErrorCode.NON_EXISTENT,
            err_msg="User has no chat with that ID",
            status_code=404,
        )
    return chat


async def get_message_object(message_id, user):
    message = await Message.get_or_none(id=message_id, sender=user).select_related(
        "sender", "chat", "sender__avatar", "file"
    )
    if not message:
        raise RequestError(
            err_code=ErrorCode.NON_EXISTENT,
            err_msg="User has no message with that ID",
            status_code=404,
        )
    return message


async def usernames_to_add_and_remove_validations(
    chat, usernames_to_add=None, usernames_to_remove=None
):
    original_existing_user_ids = await chat.users.all().values_list("id", flat=True)
    expected_user_total = len(original_existing_user_ids)
    users_to_add = []
    if usernames_to_add:
        users_to_add = await User.filter(username__in=usernames_to_add).exclude(
            Q(id__in=original_existing_user_ids) | Q(id=chat.owner_id)
        )
        expected_user_total += len(users_to_add)
    users_to_remove = []
    if usernames_to_remove:
        if not original_existing_user_ids:
            raise RequestError(
                err_code=ErrorCode.INVALID_ENTRY,
                err_msg="Invalid Entry",
                status_code=422,
                data={"usernames_to_remove": "No users to remove"},
            )
        users_to_remove = await User.filter(
            username__in=usernames_to_remove, id__in=original_existing_user_ids
        ).exclude(id=chat.owner_id)
        expected_user_total -= len(users_to_remove)

    if expected_user_total > 99:
        raise RequestError(
            err_code=ErrorCode.INVALID_ENTRY,
            err_msg="Invalid Entry",
            status_code=422,
            data={"usernames_to_add": "99 users limit reached"},
        )

    if users_to_add:
        await update_group_chat_users(chat, "add", users_to_add)
    if users_to_remove:
        await update_group_chat_users(chat, "remove", users_to_remove)
    return chat
