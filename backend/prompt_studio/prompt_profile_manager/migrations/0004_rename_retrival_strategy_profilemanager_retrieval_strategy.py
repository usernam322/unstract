# Generated by Django 4.2.1 on 2024-02-08 09:47

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("prompt_profile_manager", "0003_merge_20240125_0530"),
    ]

    operations = [
        migrations.RenameField(
            model_name="profilemanager",
            old_name="retrival_strategy",
            new_name="retrieval_strategy",
        ),
    ]