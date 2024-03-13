from typing import Optional
from litestar import Controller, Response, get, post, put, patch
from app.api.routes.utils import (
    get_notifications_queryset,
    get_requestee_and_friend_obj,
)
from app.core.security import verify_password
from app.db.models.accounts import City, User
from app.api.schemas.base import ResponseSchema
from app.api.schemas.profiles import (
    AcceptFriendRequestSchema,
    CitiesResponseSchema,
    DeleteUserSchema,
    NotificationsResponseSchema,
    ProfileResponseSchema,
    ProfileUpdateResponseSchema,
    ProfileUpdateSchema,
    ProfilesResponseSchema,
    ReadNotificationSchema,
    SendFriendRequestSchema,
)
from app.api.utils.file_processors import ALLOWED_IMAGE_TYPES
from app.api.utils.paginators import Paginator
from app.api.utils.tools import set_dict_attr
from app.common.exception_handlers import ErrorCode, RequestError
from tortoise.expressions import Q, Case, When, F
import re

from app.db.models.base import File
from app.db.models.profiles import Friend, Notification

paginator = Paginator()


def get_users_queryset(current_user):
    users = User.all().select_related("avatar", "city", "city__region")
    if current_user:
        users = users.exclude(id=current_user.id)
        city = current_user.city
        if city:
            # Order by city, region, or country similar with that of the current user
            region = city.region
            country = city.country
            order_by_val = (
                Q(city__region=region.id) if region else Q(city__country=country.id)
            )

            users = users.annotate(
                ordering_field=Case(
                    When(order_by_val, then=True),
                    default=False,  # Use False as a default value if the condition doesn't match
                )
            ).annotate(
                has_city=Case(
                    When(city=city.id, then=True),
                    default=False,
                )
            )
            # Order the users by the 'ordering_field' and "has_city" field in descending order
            users = users.order_by("-has_city", "-ordering_field")
    return users


class RetrieveUsersView(Controller):
    @get(
        summary="Retrieve Users",
        description="This endpoint retrieves a paginated list of users",
    )
    async def retrieve_users(
        self, client: Optional[User], page: int = 1
    ) -> ProfilesResponseSchema:
        users = get_users_queryset(client)
        paginated_data = await paginator.paginate_queryset(users, page)
        return ProfilesResponseSchema(message="Users fetched", data=paginated_data)


class RetrieveCitiesView(Controller):
    path = "/cities"

    @get(
        summary="Retrieve Cities based on query params",
        description="This endpoint retrieves the first 10 cities that matches the query params",
    )
    async def retrieve_cities(self, name: Optional[str]) -> CitiesResponseSchema:
        cities = []
        message = "Cities Fetched"
        if name:
            name = re.sub(r"[^\w\s]", "", name)  # Remove special chars
            cities = (
                await City.filter(name__icontains=name)
                .select_related("region", "country")
                .limit(10)
            )
        if not cities:
            message = "No match found"
        return CitiesResponseSchema(message=message, data=cities)


class UserProfileView(Controller):
    path = "/profile"

    @get(
        "/{username:str}",
        summary="Retrieve user's profile",
        description="This endpoint retrieves a particular user profile",
    )
    async def retrieve_user_profile(self, username: str) -> ProfileResponseSchema:
        user = await User.get_or_none(username=username).select_related(
            "avatar", "city"
        )
        if not user:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="No user with that username",
                status_code=404,
            )
        return ProfileResponseSchema(message="User details fetched", data=user)

    @patch(
        summary="Update user's profile",
        description=f"""
            This endpoint updates a particular user profile
            ALLOWED FILE TYPES: {", ".join(ALLOWED_IMAGE_TYPES)}
        """,
    )
    async def update_profile(
        self, data: ProfileUpdateSchema, user: User
    ) -> ProfileUpdateResponseSchema:
        data = data.model_dump(exclude_none=True)
        # Validate City ID Entry
        city_id = data.pop("city_id", None)
        city = None
        if city_id:
            city = await City.get_or_none(id=city_id)
            if not city:
                raise RequestError(
                    err_code=ErrorCode.INVALID_ENTRY,
                    err_msg="Invalid Entry",
                    data={"city_id": "No city with that ID"},
                    status_code=422,
                )
            data["city"] = city

        # Handle file upload
        image_upload_id = False
        file_type = data.pop("file_type", None)
        if file_type:
            # Create or update file object
            avatar = user.avatar
            if avatar:
                avatar.resource_type = file_type
                await avatar.save()
            else:
                avatar = await File.create(resource_type=file_type)
            image_upload_id = avatar.id
            data["avatar"] = avatar

        # Set attributes from data to user object
        user = set_dict_attr(data, user)
        user.image_upload_id = image_upload_id
        await user.save()
        return ProfileUpdateResponseSchema(message="User updated", data=user)

    @post(
        summary="Delete user's account",
        description="This endpoint deletes a particular user's account (irreversible)",
        status_code=200,
    )
    async def delete_user(self, data: DeleteUserSchema, user: User) -> ResponseSchema:
        # Check if password is valid
        if not verify_password(data.password, user.password):
            raise RequestError(
                err_code=ErrorCode.INVALID_CREDENTIALS,
                err_msg="Invalid Entry",
                status_code=422,
                data={"password": "Incorrect password"},
            )

        # Delete user
        await user.delete()
        return ResponseSchema(message="User deleted")


# FRIENDS
class FriendsView(Controller):
    path = "/friends"

    @get(
        summary="Retrieve Friends",
        description="This endpoint retrieves friends of a user",
    )
    async def retrieve_friends(
        self, user: User, page: int = 1
    ) -> ProfilesResponseSchema:
        friend_ids = await (
            Friend.filter(
                status="ACCEPTED",
            )
            .filter(Q(requester_id=user.id) | Q(requestee_id=user.id))
            .select_related("requester", "requestee")
            .annotate(
                friend_id=Case(
                    When(requester_id=user.id, then=F("requestee_id")),
                    When(requestee_id=user.id, then=F("requester_id")),
                )
            )
            .values_list("friend_id", flat=True)
        )
        friends = User.filter(id__in=friend_ids).select_related("avatar", "city")

        # Return paginated data
        paginator.page_size = 20
        paginated_data = await paginator.paginate_queryset(friends, page)
        return ProfilesResponseSchema(message="Friends fetched", data=paginated_data)

    @get(
        "/requests",
        summary="Retrieve Friend Requests",
        description="This endpoint retrieves friend requests of a user",
    )
    async def retrieve_friend_requests(
        self, user: User, page: int = 1
    ) -> ProfilesResponseSchema:
        pending_friend_ids = await Friend.filter(
            requestee_id=user.id, status="PENDING"
        ).values_list("requester_id", flat=True)
        friends = User.filter(id__in=pending_friend_ids).select_related(
            "avatar", "city"
        )

        # Return paginated data
        paginator.page_size = 20
        paginated_data = await paginator.paginate_queryset(friends, page)
        return ProfilesResponseSchema(
            message="Friend Requests fetched", data=paginated_data
        )

    @post(
        "/requests",
        summary="Send Or Delete Friend Request",
        description="This endpoint sends or delete friend requests",
    )
    async def send_or_delete_friend_request(
        self, data: SendFriendRequestSchema, user: User
    ) -> ResponseSchema:
        requestee, friend = await get_requestee_and_friend_obj(user, data.username)
        message = "Friend Request sent"
        status_code = 201
        if requestee == user:
            raise RequestError(
                err_code=ErrorCode.NOT_ALLOWED,
                err_msg="You can't send yourself a friend request nor delete a friend request sent to you.",
                status_code=403,
            )
        if friend:
            status_code = 200
            message = "Friend Request removed"
            if friend.status == "ACCEPTED":
                message = "This user is already your friend"
            elif user.id != friend.requester_id:
                raise RequestError(
                    err_code=ErrorCode.NOT_ALLOWED,
                    err_msg="The user already sent you a friend request!",
                    status_code=403,
                )
            else:
                await friend.delete()
        else:
            await Friend.create(requester_id=user.id, requestee_id=requestee.id)

        return Response(
            ResponseSchema(status="success", message=message), status_code=status_code
        )

    @put(
        "/requests",
        summary="Accept Or Reject a Friend Request",
        description="""
            This endpoint accepts or reject a friend request
            accepted choices:
            - If true, then it was accepted
            - If false, then it was rejected
        """,
    )
    async def accept_or_reject_friend_request(
        self, data: AcceptFriendRequestSchema, user: User
    ) -> ResponseSchema:
        _, friend = await get_requestee_and_friend_obj(user, data.username, "PENDING")
        if not friend:
            raise RequestError(
                err_code=ErrorCode.NON_EXISTENT,
                err_msg="No friend request exist between you and that user",
                status_code=404,
            )
        if friend.requester == user.id:
            raise RequestError(
                err_code=ErrorCode.NOT_ALLOWED,
                err_msg="You cannot accept or reject a friend request you sent ",
                status_code=403,
            )

        # Update or delete friend request based on status
        accepted = data.accepted
        if accepted:
            msg = "Accepted"
            friend.status = "ACCEPTED"
            await friend.save()
        else:
            msg = "Rejected"
            await friend.delete()
        return ResponseSchema(message=f"Friend Request {msg}")


class NotificationsView(Controller):
    path = "/notifications"

    @get(
        summary="Retrieve Auth User Notifications",
        description="""
            This endpoint retrieves a paginated list of auth user's notifications
            Note:
                - Use post slug to navigate to the post.
                - Use comment slug to navigate to the comment.
                - Use reply slug to navigate to the reply.
        """,
    )
    async def retrieve_user_notifications(
        self, user: User, page: int = 1
    ) -> NotificationsResponseSchema:
        notifications = get_notifications_queryset(user)

        # Return paginated data and set is_read to every item
        paginated_data = await paginator.paginate_queryset(notifications, page)
        return NotificationsResponseSchema(
            message="Notifications fetched", data=paginated_data
        )

    @post(
        summary="Read Notification",
        description="""
            This endpoint reads a notification
        """,
        status_code=200,
    )
    async def read_notification(
        self, data: ReadNotificationSchema, user: User
    ) -> ResponseSchema:
        id = data.id
        mark_all_as_read = data.mark_all_as_read
        resp_message = "Notifications read"
        if mark_all_as_read:
            # Mark all notifications as read
            notifications = await Notification.filter(receivers__id=user.id)
            await user.notifications_read.add(*notifications)
        elif id:
            # Mark single notification as read
            notification = await Notification.filter(receivers__id=user.id).get_or_none(
                id=id
            )
            if not notification:
                raise RequestError(
                    err_code=ErrorCode.NON_EXISTENT,
                    err_msg="User has no notification with that ID",
                    status_code=404,
                )
            await notification.read_by.add(user)
            resp_message = "Notification read"
        return ResponseSchema(message=resp_message)


profiles_handlers = [
    RetrieveUsersView,
    RetrieveCitiesView,
    UserProfileView,
    FriendsView,
    NotificationsView,
]
