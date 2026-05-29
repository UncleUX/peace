# Generated migration for adding certification fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),  # Remplacer par la dernière migration
    ]

    operations = [
        migrations.AddField(
            model_name='learningpathtemplate',
            name='certification_required',
            field=models.BooleanField(
                default=False,
                verbose_name="Certification requise",
                help_text="Activer la certification automatique pour ce parcours"
            ),
        ),
        migrations.AddField(
            model_name='learningpathtemplate',
            name='certification_threshold',
            field=models.IntegerField(
                default=80,
                verbose_name="Seuil de certification (%)",
                help_text="Pourcentage minimum requis pour la certification"
            ),
        ),
        migrations.AddField(
            model_name='learningpathtemplate',
            name='auto_generate_certification',
            field=models.BooleanField(
                default=False,
                verbose_name="Génération automatique",
                help_text="Générer automatiquement la certification lorsque le seuil est atteint"
            ),
        ),
        migrations.AddField(
            model_name='learningpathtemplate',
            name='certification_level',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('beginner', 'Débutant'),
                    ('intermediate', 'Intermédiaire'),
                    ('advanced', 'Avancé'),
                ],
                default='beginner',
                verbose_name="Niveau de certification",
                help_text="Niveau de la certification délivrée"
            ),
        ),
        migrations.AddField(
            model_name='learningpathtemplate',
            name='certificate_template_name',
            field=models.CharField(
                max_length=100,
                blank=True,
                default='default',
                verbose_name="Template de certificat",
                help_text="Nom du template utilisé pour générer le certificat PDF"
            ),
        ),
    ]
