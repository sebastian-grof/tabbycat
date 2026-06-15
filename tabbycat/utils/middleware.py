from django.core.cache import cache
from django.middleware.locale import LocaleMiddleware
from django.shortcuts import get_object_or_404

from tournaments.models import Round, Tournament


class SiteDefaultLocaleMiddleware(LocaleMiddleware):
    """Locale middleware that ignores the browser's ``Accept-Language`` header.

    Django's stock ``LocaleMiddleware`` resolves the active language as:
    language cookie -> ``Accept-Language`` header -> ``settings.LANGUAGE_CODE``.
    Because English is one of the supported ``LANGUAGES``, any visitor whose
    browser advertises English (the common default) gets the whole page in
    English, so the site default (Slovak) only ever applied to visitors whose
    browser languages matched nothing supported. That made e.g. private-URL
    ballots open in English "sometimes", depending on the judge's browser.

    By dropping the ``Accept-Language`` header before delegating to the parent
    middleware, language resolution becomes: language cookie ->
    ``settings.LANGUAGE_CODE``. Fresh visitors always get the site default,
    while an explicit choice made via the footer language switcher (which sets
    the ``LANGUAGE_COOKIE_NAME`` cookie) is still respected.
    """

    def process_request(self, request):
        request.META.pop('HTTP_ACCEPT_LANGUAGE', None)
        super().process_request(request)


class DebateMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'tournament_slug' in view_kwargs and request.path.split('/')[1] != 'api':
            cached_key = "%s_%s" % (view_kwargs['tournament_slug'], 'object')
            cached_tournament_object = cache.get(cached_key)

            if cached_tournament_object:
                request.tournament = cached_tournament_object
            else:
                request.tournament = get_object_or_404(
                    Tournament,
                    slug=view_kwargs['tournament_slug'])
                cache.set(cached_key, request.tournament, None)

            if 'round_seq' in view_kwargs:
                cached_key = "%s_%s_%s" % (view_kwargs['tournament_slug'],
                                           view_kwargs['round_seq'], 'object')
                cached_round_object = cache.get(cached_key)
                if cached_round_object:
                    request.round = cached_round_object
                else:
                    request.round = get_object_or_404(
                        Round,
                        tournament=request.tournament,
                        seq=view_kwargs['round_seq'])
                    cache.set(cached_key, request.round, None)

        return None
