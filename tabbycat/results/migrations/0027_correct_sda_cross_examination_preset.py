from django.db import migrations


def correct_sda_cross_examination(apps, schema_editor):
    CriterionPresetItem = apps.get_model('results', 'CriterionPresetItem')
    CriterionPresetItem.objects.using(schema_editor.connection.alias).filter(
        preset__name='SDA Default Criteria',
        preset__builtin=True,
        section='cross',
        seq=4,
        name='S2xN2',
    ).update(name='S1xN2')


def restore_sda_cross_examination(apps, schema_editor):
    CriterionPresetItem = apps.get_model('results', 'CriterionPresetItem')
    CriterionPresetItem.objects.using(schema_editor.connection.alias).filter(
        preset__name='SDA Default Criteria',
        preset__builtin=True,
        section='cross',
        seq=4,
        name='S1xN2',
    ).update(name='S2xN2')


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0026_alter_scorecriterion_options'),
    ]

    operations = [
        migrations.RunPython(correct_sda_cross_examination, restore_sda_cross_examination),
    ]
