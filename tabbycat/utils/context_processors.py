from django.conf import settings
from django.db.models import Case, Q, Value, When

from feedbackexport.permissions import can_view_feedback_export
from tournaments.models import Tournament
from users.permissions import has_assistant_access
from seasonbreaks.permissions import can_view_breaks
from xmlconverter.permissions import can_manage_converter_access, can_use_converter


def _visible_in_nav(user, tournament, current_tournament=None):
    """Whether the navbar's tournament switcher may list `tournament`.

    A tournament in a non-public homepage category is only shown to users who
    hold a role in it. Assistant access suffices: unlike the homepage's
    admin-only category listing, the navbar is how an assistant reaches their
    own assistant area.
    """
    category = tournament.homepage_category
    if category is None or category.public:
        return True
    if current_tournament is not None and tournament.pk == current_tournament.pk:
        return True  # already on one of its pages
    return has_assistant_access(user, tournament)


def _tournaments_visible_in_nav(user, tournaments, current_tournament=None):
    return [t for t in tournaments if _visible_in_nav(user, t, current_tournament)]


def debate_context(request):
    tournaments = Tournament.objects.filter(active=True).select_related('homepage_category')

    context = {
        'tabbycat_version': settings.TABBYCAT_VERSION or "",
        'tabbycat_codename': settings.TABBYCAT_CODENAME or "no codename",
        'all_tournaments': _tournaments_visible_in_nav(request.user, tournaments),
        'disable_sentry': getattr(settings, 'DISABLE_SENTRY', False),
        'on_local': getattr(settings, 'ON_LOCAL', False),
        'hmr': getattr(settings, 'USE_WEBPACK_SERVER', False),
        'can_view_feedback_export': can_view_feedback_export(request.user),
        'can_view_global_breaks': can_view_breaks(request.user),
        'can_use_converter': can_use_converter(request.user),
        'can_manage_converter_access': can_manage_converter_access(request.user),
    }

    if hasattr(request, 'tournament'):
        current_round = request.tournament.current_round

        # Put the current tournament first, include it even if inactive
        context['all_tournaments'] = _tournaments_visible_in_nav(
            request.user,
            Tournament.objects.filter(
                Q(active=True) | Q(pk=request.tournament.pk),
            ).select_related('homepage_category').annotate(
                is_current=Case(
                    When(pk=request.tournament.pk, then=Value(0)),
                    default=Value(1),
                ),
            ).order_by('is_current', 'seq'),
            current_tournament=request.tournament,
        )

        context.update({
            'tournament': request.tournament,
            'pref': request.tournament.preferences.by_name(),
            'current_round': current_round,
        })
        if hasattr(request, 'round'):
            context['round'] = request.round

    return context
