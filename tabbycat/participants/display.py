"""Presentation helpers for participant status, kept separate from names."""

from django.utils.html import format_html
from django.utils.translation import gettext as _


def is_online(person):
    # Ballot/feedback authors can be base Person instances.
    if getattr(getattr(person, '_meta', None), 'model_name', None) == 'person':
        person = getattr(person, 'adjudicator', None)
    return bool(getattr(person, 'is_online', False))


def online_badge(person):
    if not is_online(person):
        return ''
    return format_html(
        '<span class="badge online-status" title="{}" aria-label="{}">{}</span>',
        _("Participating remotely"), _("Online adjudicator: participating remotely"), _("Online"),
    )


def name_with_online_status(person, name):
    badge = online_badge(person)
    return format_html('{} {}', name, badge) if badge else format_html('{}', name)


def name_with_online_status_text(person, name):
    return _("%(name)s (Online)") % {'name': name} if is_online(person) else name
