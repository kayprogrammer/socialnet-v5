from typing import Annotated, Optional
from uuid import UUID

from litestar import Controller, delete, get, post, put, Request
from litestar.params import Parameter
from app.api.routes.utils import (
    get_comment_object,
    get_post_object,
    get_reaction_focus_object,
    get_reactions_queryset,
    get_reply_object,
    is_secured,
)
from app.api.schemas.feed import (
    CommentInputSchema,
    CommentResponseSchema,
    CommentWithRepliesResponseSchema,
    CommentsResponseSchema,
    PostInputResponseSchema,
    PostInputSchema,
    PostResponseSchema,
    PostsResponseSchema,
    ReactionInputSchema,
    ReactionResponseSchema,
    ReactionsResponseSchema,
    ReplyResponseSchema,
)
from app.api.utils.file_processors import ALLOWED_IMAGE_TYPES
from app.api.utils.notification import send_notification_in_socket
from app.api.utils.paginators import Paginator
from app.api.utils.tools import set_dict_attr
from app.common.exception_handlers import ErrorCode

from app.api.schemas.base import ResponseSchema

from app.common.exception_handlers import RequestError
from app.db.models.accounts import User
from app.db.models.base import File
from app.db.models.feed import Post, Reaction
from app.db.models.profiles import Notification
from tortoise.functions import Count

paginator = Paginator()


class PostsView(Controller):
    path = "/posts"

    @get(
        summary="Retrieve Latest Posts",
        description="This endpoint retrieves a paginated response of latest posts",
    )
    async def retrieve_posts(self, page: int = 1) -> PostsResponseSchema:
        posts = (
            Post.all()
            .annotate(
                reactions_count=Count("reactions"), comments_count=Count("comments")
            )
            .prefetch_related("author", "author__avatar", "image")
            .order_by("-created_at")
        )
        paginated_data = await paginator.paginate_queryset(posts, page)
        return PostsResponseSchema(message="Posts fetched", data=paginated_data)

    @post(
        summary="Create Post",
        description=f"""
            This endpoint creates a new post
            ALLOWED FILE TYPES: {", ".join(ALLOWED_IMAGE_TYPES)}
        """,
        status_code=201,
    )
    async def create_post(
        self, data: PostInputSchema, user: User
    ) -> PostInputResponseSchema:
        data = data.model_dump()
        file_type = data.pop("file_type", None)
        image_upload_id = False
        if file_type:
            file = await File.create(resource_type=file_type)
            data["image"] = file
            image_upload_id = file.id

        data["author"] = user
        post = await Post.create(**data)
        post.image_upload_id = image_upload_id
        return PostInputResponseSchema(message="Post created", data=post)

    @get(
        "/{slug:str}",
        summary="Retrieve Single Post",
        description="This endpoint retrieves a single post",
    )
    async def retrieve_post(self, slug: str) -> PostResponseSchema:
        post = await get_post_object(slug, "detailed")
        return PostResponseSchema(message="Post Detail fetched", data=post)

    @put(
        "/{slug:str}",
        summary="Update a Post",
        description="This endpoint updates a post",
    )
    async def update_post(
        self, slug: str, data: PostInputSchema, user: User
    ) -> PostInputResponseSchema:
        post: Post = await get_post_object(slug, "detailed")
        if post.author_id != user.id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="This Post isn't yours",
            )

        data = data.model_dump()
        file_type = data.pop("file_type", None)
        image_upload_id = False
        if file_type:
            # Create or update image object
            file = post.image
            if not file.id:
                file = await File.objects().create(resource_type=file_type)
            else:
                file.resource_type = file_type
                await file.save()
            data["image"] = file
            image_upload_id = file.id

        post = set_dict_attr(data, post)
        post.image_upload_id = image_upload_id
        await post.save()
        return PostInputResponseSchema(message="Post updated", data=post)

    @delete(
        "/{slug:str}",
        summary="Delete a Post",
        description="This endpoint deletes a post",
        status_code=200,
    )
    async def delete_post(self, slug: str, user: User) -> ResponseSchema:
        post: Post = await get_post_object(slug)  # simple post object
        if post.author_id != user.id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="This Post isn't yours",
            )
        await post.delete()
        return ResponseSchema(message="Post deleted")


class ReactionsView(Controller):
    path = "/reactions"
    focus_query = Parameter(
        description="Specify the usage. Use any of the three: POST, COMMENT, REPLY"
    )
    slug_query = Parameter(description="Enter the slug of the post or comment or reply")

    @get(
        "/{focus:str}/{slug:str}",
        summary="Retrieve Latest Reactions of a Post, Comment, or Reply",
        description="""
            This endpoint retrieves paginated responses of reactions of post, comment, reply.
        """,
    )
    async def retrieve_reactions(
        self,
        focus: Annotated[str, focus_query],
        slug: Annotated[str, slug_query],
        reaction_type: Optional[str],
        page: int = 1,
    ) -> ReactionsResponseSchema:
        reactions = await get_reactions_queryset(focus, slug, reaction_type)
        paginated_data = await paginator.paginate_queryset(reactions, page)
        return ReactionsResponseSchema(message="Reactions fetched", data=paginated_data)

    @post(
        "/{focus:str}/{slug:str}",
        summary="Create Reaction",
        description="""
            This endpoint creates a new reaction
            rtype should be any of these:
            
            - LIKE    - LOVE
            - HAHA    - WOW
            - SAD     - ANGRY
        """,
        status_code=201,
    )
    async def create_reaction(
        self,
        request: Request,
        user: User,
        data: ReactionInputSchema,
        focus: Annotated[str, focus_query],
        slug: Annotated[str, slug_query],
    ) -> ReactionResponseSchema:
        obj = await get_reaction_focus_object(focus, slug)

        data = data.model_dump()
        data["user"] = user
        rtype = data.pop("rtype").value
        obj_field = focus.lower()  # Focus object field (e.g post, comment, reply)
        data[obj_field] = obj

        reaction = await Reaction.get_or_none(**data).select_related(
            "user", "user__avatar"
        )
        if reaction:
            reaction.rtype = rtype
            await reaction.save()
        else:
            data["rtype"] = rtype
            reaction = await Reaction.create(**data)

        # Create and Send Notification
        if (
            obj.author_id != user.id
        ):  # Send notification only when it's not the user reacting to his data
            ndata = {obj_field: obj}
            notification, created = await Notification.get_or_create(
                sender=user, ntype="REACTION", **ndata
            ).select_related(
                "sender",
                "sender__avatar",
                "post",
                "comment",
                "comment__post",
                "reply",
                "reply__comment",
                "reply__comment__post",
            )
            if created:
                await notification.receivers.add(obj.author)

                # Send to websocket
                await send_notification_in_socket(
                    is_secured(request),
                    request.headers["host"],
                    notification,
                )
        return ReactionResponseSchema(message="Reaction created", data=reaction)

    @delete(
        "/{id:uuid}",
        summary="Remove Reaction",
        description="""
            This endpoint deletes a reaction.
        """,
        status_code=200,
    )
    async def remove_reaction(
        self, request: Request, id: UUID, user: User
    ) -> ResponseSchema:
        reaction = await Reaction.get_or_none(id=id).select_related(
            "post", "comment", "reply"
        )
        if not reaction:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="Reaction does not exist",
                status_code=404,
            )
        if user.id != reaction.user_id:
            raise RequestError(
                err_code=ErrorCode.INVALID_OWNER,
                err_msg="Not yours to delete",
                status_code=401,
            )

        # Remove Reaction Notification
        targeted_obj = reaction.targeted_obj
        targeted_field = f"{targeted_obj.__class__.__name__.lower()}_id"  # (post_id, comment_id or reply_id)
        data = {
            "sender": user,
            "ntype": "REACTION",
            targeted_field: targeted_obj.id,
        }

        notification = await Notification.get_or_none(**data)
        if notification:
            # Send to websocket and delete notification
            await send_notification_in_socket(
                request.is_secure(), request.get_host(), notification, status="DELETED"
            )
            await notification.delete()

        await reaction.delete()
        return ResponseSchema(message="Reaction deleted")


# COMMENTS


# @router.get(
#     "/posts/{slug}/comments",
#     summary="Retrieve Post Comments",
#     description="""
#         This endpoint retrieves comments of a particular post.
#     """,
# )
# async def retrieve_comments(slug: str, page: int = 1) -> CommentsResponseSchema:
#     post = await get_post_object(slug)
#     comments = Comment.objects(Comment.author, Comment.author.avatar).where(
#         Comment.post == post.id
#     )
#     paginated_data = await paginator.paginate_queryset(comments, page)
#     return {"message": "Comments Fetched", "data": paginated_data}


# @router.post(
#     "/posts/{slug}/comments",
#     summary="Create Comment",
#     description="""
#         This endpoint creates a comment for a particular post.
#     """,
#     status_code=201,
# )
# async def create_comment(
#     request: Request,
#     slug: str,
#     data: CommentInputSchema,
#     user: User = Depends(get_current_user),
# ) -> CommentResponseSchema:
#     post = await get_post_object(slug)
#     comment = await Comment.objects().create(post=post, author=user, text=data.text)

#     # Create and Send Notification
#     if user.id != post.author:
#         notification = await Notification.objects().create(
#             sender=user.id,
#             ntype="COMMENT",
#             comment=comment.id,
#             receiver_ids=[post.author],
#         )
#         notification.sender = user
#         notification.comment = comment
#         # Send to websocket
#         await send_notification_in_socket(
#             is_secured(request), request.headers["host"], notification
#         )
#     return {"message": "Comment Created", "data": comment}


# @router.get(
#     "/comments/{slug}",
#     summary="Retrieve Comment with replies",
#     description="""
#         This endpoint retrieves a comment with replies.
#     """,
# )
# async def retrieve_comment_with_replies(
#     slug: str, page: int = 1
# ) -> CommentWithRepliesResponseSchema:
#     comment = await get_comment_object(slug)
#     replies = Reply.objects(Reply.author, Reply.author.avatar).where(
#         Reply.comment == comment.id
#     )
#     paginated_data = await paginator.paginate_queryset(replies, page)
#     data = {"comment": comment, "replies": paginated_data}
#     return {"message": "Comment and Replies Fetched", "data": data}


# @router.post(
#     "/comments/{slug}",
#     summary="Create Reply",
#     description="""
#         This endpoint creates a reply for a comment.
#     """,
#     status_code=201,
# )
# async def create_reply(
#     request: Request,
#     slug: str,
#     data: CommentInputSchema,
#     user: User = Depends(get_current_user),
# ) -> ReplyResponseSchema:
#     comment = await get_comment_object(slug)
#     reply = await Reply.objects().create(author=user, comment=comment, text=data.text)

#     # Create and Send Notification
#     if user.id != comment.author.id:
#         notification = await Notification.objects().create(
#             sender=user.id,
#             ntype="REPLY",
#             reply=reply.id,
#             receiver_ids=[comment.author.id],
#         )
#         notification.sender = user
#         notification.reply = reply
#         # Send to websocket
#         await send_notification_in_socket(
#             is_secured(request), request.headers["host"], notification
#         )
#     return {"message": "Reply Created", "data": reply}


# @router.put(
#     "/comments/{slug}",
#     summary="Update Comment",
#     description="""
#         This endpoint updates a particular comment.
#     """,
# )
# async def update_comment(
#     slug: str, data: CommentInputSchema, user: User = Depends(get_current_user)
# ) -> CommentResponseSchema:
#     comment = await get_comment_object(slug)
#     if comment.author.id != user.id:
#         raise RequestError(
#             err_code=ErrorCode.INVALID_OWNER,
#             err_msg="Not yours to edit",
#             status_code=401,
#         )
#     comment.text = data.text
#     await comment.save()
#     return {"message": "Comment Updated", "data": comment}


# @router.delete(
#     "/comments/{slug}",
#     summary="Delete Comment",
#     description="""
#         This endpoint deletes a comment.
#     """,
# )
# async def delete_comment(
#     request: Request, slug: str, user: User = Depends(get_current_user)
# ) -> ResponseSchema:
#     comment = await get_comment_object(slug)
#     if user.id != comment.author.id:
#         raise RequestError(
#             err_code=ErrorCode.INVALID_OWNER,
#             err_msg="Not yours to delete",
#             status_code=401,
#         )

#     # # Remove Comment Notification
#     notification = (
#         await Notification.objects()
#         .where(
#             Notification.sender == user.id,
#             Notification.ntype == "COMMENT",
#             Notification.comment == comment.id,
#         )
#         .first()
#     )
#     if notification:
#         # Send to websocket and delete notification
#         await send_notification_in_socket(
#             is_secured(request), request.headers["host"], notification, status="DELETED"
#         )

#     await comment.remove()  # deletes notification alongside (CASCADE)
#     return {"message": "Comment Deleted"}


# @router.get(
#     "/replies/{slug}",
#     summary="Retrieve Reply",
#     description="""
#         This endpoint retrieves a reply.
#     """,
# )
# async def retrieve_reply(slug: str) -> ReplyResponseSchema:
#     reply = await get_reply_object(slug)
#     return {"message": "Reply Fetched", "data": reply}


# @router.put(
#     "/replies/{slug}",
#     summary="Update Reply",
#     description="""
#         This endpoint updates a particular reply.
#     """,
# )
# async def update_reply(
#     slug: str, data: CommentInputSchema, user: User = Depends(get_current_user)
# ) -> ReplyResponseSchema:
#     reply = await get_reply_object(slug)
#     if reply.author.id != user.id:
#         raise RequestError(
#             err_code=ErrorCode.INVALID_OWNER,
#             err_msg="Not yours to edit",
#             status_code=401,
#         )
#     reply.text = data.text
#     await reply.save()
#     return {"message": "Reply Updated", "data": reply}


# @router.delete(
#     "/replies/{slug}",
#     summary="Delete reply",
#     description="""
#         This endpoint deletes a reply.
#     """,
# )
# async def delete_reply(
#     request: Request, slug: str, user: User = Depends(get_current_user)
# ) -> ResponseSchema:
#     reply = await get_reply_object(slug)
#     if user.id != reply.author.id:
#         raise RequestError(
#             err_code=ErrorCode.INVALID_OWNER,
#             err_msg="Not yours to delete",
#             status_code=401,
#         )

#     # Remove Reply Notification
#     notification = (
#         await Notification.objects()
#         .where(
#             Notification.sender == user,
#             Notification.ntype == "REPLY",
#             Notification.reply == reply.id,
#         )
#         .first()
#     )
#     if notification:
#         # Send to websocket and delete notification
#         await send_notification_in_socket(
#             is_secured(request), request.headers["host"], notification, status="DELETED"
#         )

#     await reply.remove()  # deletes notification alongside (CASCADE)
#     return {"message": "Reply Deleted"}

feed_handlers = [
    PostsView,
    ReactionsView,
]
