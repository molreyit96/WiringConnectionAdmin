from django.db import connection


class SetCurrentUserMiddleware:
    """Publishes the authenticated username to PostgreSQL as ``app.current_user``.

    The DailyMob status audit trigger reads this session setting to record which
    application user caused a change. When the database is edited directly
    (psql / pgAdmin) the setting is empty and only the DB role is recorded, so
    manual changes are identifiable.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _set_user(self, username):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.current_user', %s, false)", [username])
        except Exception:
            pass

    def __call__(self, request):
        username = ""
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            username = user.get_username() or ""

        if username:
            self._set_user(username)

        try:
            return self.get_response(request)
        finally:
            if username:
                self._set_user("")
