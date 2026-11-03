from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    message = "No tienes acceso a este recurso."

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None)
        if owner is None:
            owner = _resolve_owner(obj)
        return owner == request.user


def _resolve_owner(obj):
    for path in (
        ("session", "user"),
        ("routine", "user"),
        ("program", "user"),
    ):
        current = obj
        for attribute in path:
            current = getattr(current, attribute, None)
            if current is None:
                break
        else:
            return current
    return None
