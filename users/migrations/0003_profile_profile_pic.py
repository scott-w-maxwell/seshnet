# Generated by Django 4.0.4 on 2022-04-26 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_profile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='profile_pic',
            field=models.ImageField(blank=True, default='default.png', upload_to='profile_pics'),
        ),
    ]
