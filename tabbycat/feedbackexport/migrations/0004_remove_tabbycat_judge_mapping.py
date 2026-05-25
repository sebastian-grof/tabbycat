from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feedbackexport', '0003_tournament_based_judge_activity_events'),
    ]

    operations = [
        migrations.DeleteModel(
            name='JudgeProfileLink',
        ),
        migrations.DeleteModel(
            name='JudgeProfile',
        ),
    ]
