from django.conf import settings


def asset_version(request):
    """Expose ASSET_VERSION to every template.

    Django does not put settings into the template context, so the ?v= suffix
    on {% static %} tags would otherwise render as an empty query string and
    the 30-day cache would never be busted. Registered in
    settings.TEMPLATES['OPTIONS']['context_processors'].
    """
    return {'ASSET_VERSION': settings.ASSET_VERSION}
