# Generated by Django 4.2.1 on 2024-02-16 06:50

import json
from typing import Any

from account.models import EncryptionSecret
from connector.models import ConnectorInstance
from cryptography.fernet import Fernet
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("connector", "0001_initial"),
        ("account", "0005_encryptionsecret"),
    ]

    def EncryptCredentials(apps: Any, schema_editor: Any) -> None:
        encryption_secret: EncryptionSecret = EncryptionSecret.objects.get()
        f: Fernet = Fernet(encryption_secret.key.encode("utf-8"))
        queryset = ConnectorInstance.objects.all()

        for obj in queryset:  # type: ignore
            # Access attributes of the object

            if hasattr(obj, "connector_metadata"):
                json_string: str = json.dumps(obj.connector_metadata)
                obj.connector_metadata_b = f.encrypt(
                    json_string.encode("utf-8")
                )
                obj.save()

    operations = [
        migrations.AddField(
            model_name="connectorinstance",
            name="connector_metadata_b",
            field=models.BinaryField(null=True),
        ),
        migrations.RunPython(
            EncryptCredentials, reverse_code=migrations.RunPython.noop
        ),
    ]