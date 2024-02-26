from uuid import UUID

from litestar import Controller, Request, delete, get, patch, post, put
from app.api.routes.utils import (
    create_file,
    get_chat_object,
    get_message_object,
    usernames_to_add_and_remove_validations,
)
from app.api.schemas.chat import (
    ChatResponseSchema,
    ChatsResponseSchema,
    GroupChatCreateSchema,
    GroupChatInputResponseSchema,
    GroupChatInputSchema,
    MessageCreateResponseSchema,
    MessageCreateSchema,
    MessageUpdateSchema,
)
from app.api.utils.file_processors import ALLOWED_FILE_TYPES
from app.api.utils.paginators import Paginator
from app.api.utils.tools import set_dict_attr
from app.common.exception_handlers import ErrorCode

from app.api.schemas.base import ResponseSchema

from app.common.exception_handlers import RequestError
from app.db.models.accounts import User
from app.db.models.chat import Chat, Message
from tortoise.expressions import Q

paginator = Paginator()


class ChatsView(Controller):
    @get(
        summary="Retrieve User Chats",
        description="""
            This endpoint retrieves a paginated list of the current user chats
            Only chats with type "GROUP" have name, image and description.
        """,
    )
    async def retrieve_user_chats(
        self, user: User, page: int = 1
    ) -> ChatsResponseSchema:
        chats = (
            Chat.filter((Chat.owner == user.id) | (Chat.user_ids.any(user.id)))
            .select_related("owner", "owner__avatar", "image")
            .order_by("-updated_at")
        )
        paginator.page_size = 200
        paginated_data = await paginator.paginate_queryset(chats, page)
        return ChatsResponseSchema(message="Chats fetched", data=paginated_data)

    @post(
        "",
        summary="Send a message",
        description=f"""
            This endpoint sends a message.
            You must either send a text or a file or both.
            If there's no chat_id, then its a new chat and you must set username and leave chat_id
            If chat_id is available, then ignore username and set the correct chat_id
            The file_upload_data in the response is what is used for uploading the file to cloudinary from client
            ALLOWED FILE TYPES: {", ".join(ALLOWED_FILE_TYPES)}
        """,
        status_code=201,
    )
    async def send_message(
        self, data: MessageCreateSchema, user: User
    ) -> MessageCreateResponseSchema:
        chat_id = data.chat_id
        username = data.username

        # For sending
        chat = None
        if not chat_id:
            # Create a new chat dm with current user and recipient user
            recipient_user = await User.get_or_none(username=username)
            if not recipient_user:
                raise RequestError(
                    err_code=ErrorCode.INVALID_ENTRY,
                    err_msg="Invalid entry",
                    status_code=422,
                    data={"username": "No user with that username"},
                )

            chat = (
                await Chat.filter(ctype="DM")
                .filter(
                    Q(owner_id=user.id, users__id=recipient_user.id)
                    | Q(owner_id=recipient_user.id, users__id=user.id)
                )
                .get_or_none()
            )

            # Check if a chat already exists between both users
            if chat:
                raise RequestError(
                    err_code=ErrorCode.INVALID_ENTRY,
                    err_msg="Invalid entry",
                    status_code=422,
                    data={
                        "username": "A chat already exist between you and the recipient"
                    },
                )
            chat = await Chat.create(owner=user.id)
            await chat.users.add(recipient_user)
        else:
            # Get the chat with chat id and check if the current user is the owner or the recipient
            chat = await Chat.filter(
                Q(owner_id=user.id) | Q(users__id=user.id)
            ).get_or_none(id=chat_id)
            if not chat:
                raise RequestError(
                    err_code=ErrorCode.NON_EXISTENT,
                    err_msg="User has no chat with that ID",
                    status_code=404,
                )

        # Create Message
        file = await create_file(data.file_type)
        file_upload_id = file.id if file else None
        message = await Message.create(
            chat=chat.id, sender=user.id, text=data.text, file=file
        )
        message.sender = user
        message.file_upload_id = file_upload_id
        return MessageCreateResponseSchema(message="Message sent", data=message)

    @get(
        "/{chat_id:uuid}",
        summary="Retrieve messages from a Chat",
        description="""
            This endpoint retrieves all messages in a chat.
        """,
    )
    async def retrieve_messages(
        self, chat_id: UUID, user: User, page: int = 1
    ) -> ChatResponseSchema:
        chat = await get_chat_object(user, chat_id)
        paginator.page_size = 400
        paginated_data = await paginator.paginate_queryset(chat.messages, page)
        # Set latest message obj
        messages = paginated_data["items"]
        chat._latest_message_obj = messages[0] if len(messages) > 0 else None

        data = {"chat": chat, "messages": paginated_data, "users": chat.users}
        return ChatResponseSchema(message="Messages fetched", data=data)

    @patch(
        "/{chat_id}",
        summary="Update a Group Chat",
        description="""
            This endpoint updates a group chat.
        """,
    )
    async def update_group_chat(
        self, chat_id: UUID, data: GroupChatInputSchema, user: User
    ) -> GroupChatInputResponseSchema:
        chat = (
            await Chat.objects(Chat.image)
            .where(Chat.owner == user.id, Chat.ctype == "GROUP")
            .get(Chat.id == chat_id)
        )
        if not chat:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User owns no group chat with that ID",
                status_code=404,
            )

        data = data.model_dump(exclude_none=True)

        # Handle Users Upload or Remove
        usernames_to_add = data.pop("usernames_to_add", None)
        usernames_to_remove = data.pop("usernames_to_remove", None)
        chat = await usernames_to_add_and_remove_validations(
            chat, usernames_to_add, usernames_to_remove
        )

        # Handle File Upload
        file_type = data.pop("file_type", None)
        image_upload_id = False
        if file_type:
            file = chat.image
            if file.id:
                file.resource_type = file_type
                await file.save()
            else:
                file = await create_file(file_type)
                data["image"] = file.id
            image_upload_id = file.id
        chat = set_dict_attr(data, chat)
        await chat.save()
        chat.users = await User.objects(User.avatar).where(User.id.is_in(chat.user_ids))
        chat.image_upload_id = image_upload_id
        return GroupChatInputResponseSchema(message="Chat updated", data=chat)

    @delete(
        "/{chat_id:uuid}",
        summary="Delete a Group Chat",
        description="""
            This endpoint deletes a group chat.
        """,
    )
    async def delete_group_chat(self, chat_id: UUID, user: User) -> ResponseSchema:
        chat = (
            await Chat.objects()
            .where(Chat.owner == user.id, Chat.ctype == "GROUP")
            .get(Chat.id == chat_id)
        )
        if not chat:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="User owns no group chat with that ID",
                status_code=404,
            )
        await chat.delete()
        return ResponseSchema(message="Group Chat Deleted")


class MessagesView(Controller):
    path = "/messages"

    @put(
        "/{message_id:uuid}",
        summary="Update a message",
        description=f"""
            This endpoint updates a message.
            You must either send a text or a file or both.
            The file_upload_data in the response is what is used for uploading the file to cloudinary from client
            ALLOWED FILE TYPES: {", ".join(ALLOWED_FILE_TYPES)}
        """,
    )
    async def update_message(
        self, message_id: UUID, data: MessageUpdateSchema, user: User
    ) -> MessageCreateResponseSchema:
        message = await get_message_object(message_id, user)

        data = data.model_dump(exclude_none=True)
        # Handle File Upload
        file_upload_id = None
        file_type = data.pop("file_type", None)
        if file_type:
            file = message.file
            if file.id:
                file.resource_type = file_type
                await file.save()
            else:
                file = await create_file(file_type)
                data["file"] = file.id
            file_upload_id = file.id
        message = set_dict_attr(data, message)
        await message.save()
        message.file_upload_id = file_upload_id
        message.chat = message.chat.id
        return MessageCreateResponseSchema(message="Message updated", data=message)

    @delete(
        "/{message_id:uuid}",
        summary="Delete a message",
        description="""
            This endpoint deletes a message.

        """,
    )
    async def delete_message(
        self, request: Request, message_id: UUID, user: User
    ) -> ResponseSchema:
        message = await get_message_object(message_id, user)
        chat = message.chat
        chat_id = chat.id
        messages_count = await Message.count().where(Message.chat == chat_id)

        # Send socket message
        # await send_message_deletion_in_socket(
        #     is_secured(request), request.headers["host"], chat_id, message_id
        # )

        # Delete message and chat if its the last message in the dm being deleted
        if messages_count == 1 and chat.ctype == "DM":
            await chat.remove()  # Message deletes if chat gets deleted (CASCADE)
        else:
            # Set new latest message
            new_latest_message = (
                await Message.select(Message.id)
                .where(Message.chat == chat_id, Message.id != message.id)
                .order_by(Message.created_at, ascending=False)
                .first()
            )
            new_latest_message_id = (
                new_latest_message["id"] if new_latest_message else None
            )
            chat.latest_message_id = new_latest_message_id
            await chat.save()
            await message.remove()
        return ResponseSchema(message="Message deleted")


class GroupsView(Controller):
    path = "/groups/group"

    @post(
        summary="Create a group chat",
        description="""
            This endpoint creates a group chat.
            The users_entry field should be a list of usernames you want to add to the group.
            Note: You cannot add more than 99 users in a group (1 owner + 99 other users = 100 users total)
        """,
        status_code=201,
    )
    async def create_group_chat(
        data: GroupChatCreateSchema, user: User
    ) -> GroupChatInputResponseSchema:
        data = data.model_dump(exclude_none=True)
        data.update({"owner": user, "ctype": "GROUP"})

        # Handle Users Upload
        usernames_to_add = data.pop("usernames_to_add")
        users_to_add = await User.objects(User.avatar).where(
            User.username.is_in(usernames_to_add), User.id != user.id
        )
        if not users_to_add:
            raise RequestError(
                err_code=ErrorCode.INVALID_ENTRY,
                err_msg="Invalid Entry",
                data={"usernames_to_add": "Enter at least one valid username"},
                status_code=422,
            )

        # Handle File Upload
        file_type = data.pop("file_type", None)
        image_upload_id = None
        if file_type:
            file = await create_file(file_type)
            data["image"] = file.id
            image_upload_id = file.id

        # Create Chat
        data["user_ids"] = [user.id for user in users_to_add]
        chat = await Chat.objects().create(**data)
        chat.users = users_to_add
        chat.image_upload_id = image_upload_id
        return GroupChatInputResponseSchema(message="Chat created", data=chat)


chat_handlers = [ChatsView, MessagesView, GroupsView]