from django.db import migrations, models

import utils.fields
from users.permissions import Permission

# The value of Permission.ACCESS_ASSISTANT, hardcoded so this data migration
# stays stable even if the enum member is later renamed.
ACCESS_ASSISTANT = 'access.assistant'


def grant_access_to_existing_groups(apps, schema_editor):
    """Before this change every authenticated user could reach the assistant
    area. Grant the new permission to all existing roles so nobody who already
    has a role loses access; only users without any role are now excluded."""
    Group = apps.get_model('users', 'Group')
    for group in Group.objects.all():
        if ACCESS_ASSISTANT not in group.permissions:
            group.permissions = list(group.permissions) + [ACCESS_ASSISTANT]
            group.save(update_fields=['permissions'])


def revoke_access_from_groups(apps, schema_editor):
    Group = apps.get_model('users', 'Group')
    for group in Group.objects.all():
        if ACCESS_ASSISTANT in group.permissions:
            group.permissions = [p for p in group.permissions if p != ACCESS_ASSISTANT]
            group.save(update_fields=['permissions'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    # The permission fields draw their choices from the Permission enum, which
    # now has a new member. Bind the choices to the live enum (rather than a
    # frozen literal) so future permission additions don't each need a
    # choices-only migration.
    operations = [
        migrations.AlterField(
            model_name='group',
            name='permissions',
            field=utils.fields.ChoiceArrayField(
                base_field=models.CharField(choices=Permission.choices, max_length=50),
                blank=True, default=list, size=None, verbose_name='permissions'),
        ),
        migrations.AlterField(
            model_name='userpermission',
            name='permission',
            field=models.CharField(choices=Permission.choices, max_length=50, verbose_name='permission'),
        ),
        migrations.RunPython(grant_access_to_existing_groups, revoke_access_from_groups),
    ]
