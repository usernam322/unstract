# Generated by Django 4.2.1 on 2024-02-28 11:29

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("workflow", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="workflow",
            name="settings",
        ),
    ]