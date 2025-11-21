from django.db import migrations
class Migration(migrations.Migration):
    atomic = False
    dependencies = []
    operations = [
        migrations.RunSQL(
            "CREATE UNIQUE INDEX IF NOT EXISTS auth_user_email_ci_uq ON auth_user (LOWER(email));",
            "DROP INDEX IF EXISTS auth_user_email_ci_uq;",
        )
    ]
