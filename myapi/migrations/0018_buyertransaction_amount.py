# Generated by Django 5.1.3 on 2025-03-03 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0017_buyerotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='buyertransaction',
            name='amount',
            field=models.CharField(default=0, max_length=15),
        ),
    ]
