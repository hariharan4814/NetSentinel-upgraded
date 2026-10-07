from django.db import migrations


def seed_guard(apps, schema_editor):
    apps.get_model("experiments", "QueueGuard").objects.using(schema_editor.connection.alias).get_or_create(id=1)


class Migration(migrations.Migration):
    dependencies = [("experiments", "0002_queueguard")]
    operations = [migrations.RunPython(seed_guard, migrations.RunPython.noop)]
