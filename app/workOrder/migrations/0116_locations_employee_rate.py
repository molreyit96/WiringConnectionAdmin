from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workOrder', '0115_employee_is_read_only'),
    ]

    operations = [
        migrations.AddField(
            model_name='locations',
            name='employee_rate',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
