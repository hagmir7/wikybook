# Generated by Django 5.0.7 on 2024-09-16 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pdf', '0007_alter_author_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
    ]