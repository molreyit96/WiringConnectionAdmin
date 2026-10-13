from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0018_alter_dailymobdocs_created_date_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyMobStatusAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dailymob_id', models.BigIntegerField(db_index=True)),
                ('old_status', models.IntegerField(blank=True, null=True)),
                ('new_status', models.IntegerField(blank=True, null=True)),
                ('operation', models.CharField(blank=True, max_length=10, null=True)),
                ('changed_at', models.DateTimeField(blank=True, null=True)),
                ('db_user', models.CharField(blank=True, max_length=100, null=True)),
                ('session_user', models.CharField(blank=True, max_length=100, null=True)),
                ('app_user', models.CharField(blank=True, max_length=100, null=True)),
                ('txid', models.BigIntegerField(blank=True, null=True)),
                ('row_snapshot', models.JSONField(blank=True, null=True)),
            ],
            options={
                'db_table': 'mobile_dailymobstatusaudit',
                'ordering': ['-changed_at'],
            },
        ),
    ]
