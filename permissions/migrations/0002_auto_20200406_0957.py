# Generated by Django 3.0.4 on 2020-04-06 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='element',
            name='granted_on',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='followup',
            name='followedup_at',
            field=models.DateTimeField(null=True),
        ),
    ]
