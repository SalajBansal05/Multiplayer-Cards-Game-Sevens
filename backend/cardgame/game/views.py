import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .room_manager import room_manager


@csrf_exempt
@require_POST
def create_room(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse(
            {"error": "Invalid request body."},
            status=400
        )

    token = data.get("token")

    if not token:
        return JsonResponse(
            {"error": "Player identity is missing."},
            status=400
        )

    existing_room = room_manager.token_in_any_room(token)

    if existing_room is not None:
        return JsonResponse(
            {
                "error": "You are already in a game.",
                "room_id": existing_room.room_id
            },
            status=409
        )

    room = room_manager.create_room(token)

    return JsonResponse({
        "room_id": room.room_id
    })