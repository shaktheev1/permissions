# Generated by Django 3.0.4 on 2020-05-15 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0017_auto_20200510_0907'),
    ]

    operations = [
        migrations.AddField(
            model_name='element',
            name='permission_status',
            field=models.BooleanField(default=True),
        ),
    ]
