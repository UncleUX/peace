# Generated migration for template field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('certifications', '0001_initial'),
        ('courses', '0012_learningpathtemplate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certification',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='courses.course'),
        ),
        migrations.AddField(
            model_name='certification',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='courses.learningpathtemplate'),
        ),
    ]
