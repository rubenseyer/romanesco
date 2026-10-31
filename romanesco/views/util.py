from flask import abort, g, request


def selected_user_ids(all_users: dict[int, str]) -> list[int]:
    try:
        user_ids = list(dict.fromkeys(
            int(user_id) for value in request.args.getlist('id') for user_id in value.split(',')
        )) or [g.user_id]
    except ValueError:
        abort(400)
    if any(user_id not in all_users for user_id in user_ids):
        abort(400)
    return user_ids
