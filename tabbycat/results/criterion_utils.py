from django.db import transaction

from .models import CriterionPreset, CriterionPresetItem, CrossExamination, ScoreCriterion


def create_preset_from_tournament(name, description, tournament):
    """Create a global preset from one tournament's current criterion setup."""
    with transaction.atomic():
        preset = CriterionPreset.objects.create(name=name, description=description)

        items = []
        for section, speech_type in (
            (CriterionPresetItem.Section.SUBSTANTIVE, ScoreCriterion.SpeechType.SUBSTANTIVE),
            (CriterionPresetItem.Section.REPLY, ScoreCriterion.SpeechType.REPLY),
        ):
            criteria = ScoreCriterion.objects.filter(
                tournament=tournament,
                speech_type=speech_type,
            ).order_by('seq')
            for seq, criterion in enumerate(criteria, start=1):
                items.append(_preset_item_from_criterion(preset, section, seq, criterion))

        crosses = CrossExamination.objects.filter(tournament=tournament).order_by('seq')
        for seq, cross in enumerate(crosses, start=1):
            items.append(_preset_item_from_criterion(
                preset, CriterionPresetItem.Section.CROSS, seq, cross))

        CriterionPresetItem.objects.bulk_create(items)
        return preset


def apply_preset_to_tournament(preset, tournament):
    """Replace a tournament's criteria with a global preset."""
    items = list(preset.items.order_by('section', 'seq'))

    with transaction.atomic():
        ScoreCriterion.objects.filter(tournament=tournament).delete()
        CrossExamination.objects.filter(tournament=tournament).delete()

        score_seq = 1
        score_criteria = []
        for item in _items_for_section(items, CriterionPresetItem.Section.SUBSTANTIVE):
            score_criteria.append(_score_criterion_from_item(
                tournament, item, score_seq, ScoreCriterion.SpeechType.SUBSTANTIVE))
            score_seq += 1
        for item in _items_for_section(items, CriterionPresetItem.Section.REPLY):
            score_criteria.append(_score_criterion_from_item(
                tournament, item, score_seq, ScoreCriterion.SpeechType.REPLY))
            score_seq += 1

        crosses = [
            _cross_from_item(tournament, item, seq)
            for seq, item in enumerate(_items_for_section(items, CriterionPresetItem.Section.CROSS), start=1)
        ]

        ScoreCriterion.objects.bulk_create(score_criteria)
        CrossExamination.objects.bulk_create(crosses)


def save_tournament_criteria(tournament, substantive_entries, reply_entries, cross_entries):
    """Save edited tournament criteria from cleaned form entries."""
    with transaction.atomic():
        _save_score_criteria(tournament, substantive_entries, reply_entries)
        _save_cross_criteria(tournament, cross_entries)


def _preset_item_from_criterion(preset, section, seq, criterion):
    return CriterionPresetItem(
        preset=preset,
        section=section,
        seq=seq,
        name=criterion.name,
        weight=criterion.weight,
        min_score=criterion.min_score,
        max_score=criterion.max_score,
        step=criterion.step,
        required=criterion.required,
    )


def _score_criterion_from_item(tournament, item, seq, speech_type):
    return ScoreCriterion(
        tournament=tournament,
        name=item.name,
        seq=seq,
        weight=item.weight,
        min_score=item.min_score,
        max_score=item.max_score,
        step=item.step,
        required=item.required,
        speech_type=speech_type,
    )


def _cross_from_item(tournament, item, seq):
    return CrossExamination(
        tournament=tournament,
        seq=seq,
        name=item.name,
        weight=item.weight,
        min_score=item.min_score,
        max_score=item.max_score,
        step=item.step,
        required=item.required,
    )


def _items_for_section(items, section):
    return [item for item in items if item.section == section]


def _save_score_criteria(tournament, substantive_entries, reply_entries):
    active_ids = {
        entry['id'] for entry in substantive_entries + reply_entries
        if entry.get('id') is not None and not entry.get('delete')
    }
    delete_ids = {
        entry['id'] for entry in substantive_entries + reply_entries
        if entry.get('id') is not None and entry.get('delete')
    }

    ScoreCriterion.objects.filter(tournament=tournament, pk__in=delete_ids).delete()

    preserved = list(ScoreCriterion.objects.filter(tournament=tournament).exclude(
        speech_type__in=[ScoreCriterion.SpeechType.SUBSTANTIVE, ScoreCriterion.SpeechType.REPLY],
    ).order_by('seq', 'pk'))

    kept = list(ScoreCriterion.objects.filter(tournament=tournament, pk__in=active_ids)) + preserved
    for index, criterion in enumerate(kept, start=1):
        criterion.seq = -100000 - index
        criterion.save(update_fields=['seq'])

    seq = 1
    for entry in sorted(_active_entries(substantive_entries), key=_entry_order):
        criterion = _get_or_new_score_criterion(tournament, entry)
        _update_score_criterion(criterion, entry, seq, ScoreCriterion.SpeechType.SUBSTANTIVE)
        criterion.save()
        seq += 1

    for entry in sorted(_active_entries(reply_entries), key=_entry_order):
        criterion = _get_or_new_score_criterion(tournament, entry)
        _update_score_criterion(criterion, entry, seq, ScoreCriterion.SpeechType.REPLY)
        criterion.save()
        seq += 1

    for criterion in preserved:
        criterion.seq = seq
        criterion.save(update_fields=['seq'])
        seq += 1


def _save_cross_criteria(tournament, cross_entries):
    active_ids = {
        entry['id'] for entry in cross_entries
        if entry.get('id') is not None and not entry.get('delete')
    }
    delete_ids = {
        entry['id'] for entry in cross_entries
        if entry.get('id') is not None and entry.get('delete')
    }

    CrossExamination.objects.filter(tournament=tournament, pk__in=delete_ids).delete()

    kept = list(CrossExamination.objects.filter(tournament=tournament, pk__in=active_ids))
    for index, cross in enumerate(kept, start=1):
        cross.seq = -100000 - index
        cross.save(update_fields=['seq'])

    for seq, entry in enumerate(sorted(_active_entries(cross_entries), key=_entry_order), start=1):
        cross = _get_or_new_cross(tournament, entry)
        _update_cross(cross, entry, seq)
        cross.save()


def _active_entries(entries):
    return [entry for entry in entries if not entry.get('delete') and entry.get('name')]


def _entry_order(entry):
    return (entry.get('order') is None, entry.get('order') or 0, entry.get('id') or 0)


def _get_or_new_score_criterion(tournament, entry):
    if entry.get('id') is None:
        return ScoreCriterion(tournament=tournament)
    return ScoreCriterion.objects.get(tournament=tournament, pk=entry['id'])


def _get_or_new_cross(tournament, entry):
    if entry.get('id') is None:
        return CrossExamination(tournament=tournament)
    return CrossExamination.objects.get(tournament=tournament, pk=entry['id'])


def _update_score_criterion(criterion, entry, seq, speech_type):
    criterion.name = entry['name']
    criterion.seq = seq
    criterion.weight = entry['weight']
    criterion.min_score = entry['min_score']
    criterion.max_score = entry['max_score']
    criterion.step = entry['step']
    criterion.required = entry['required']
    criterion.speech_type = speech_type


def _update_cross(cross, entry, seq):
    cross.name = entry['name']
    cross.seq = seq
    cross.weight = entry['weight']
    cross.min_score = entry['min_score']
    cross.max_score = entry['max_score']
    cross.step = entry['step']
    cross.required = entry['required']
