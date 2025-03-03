# Generated by Django 5.1.3 on 2025-02-28 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0015_remove_purchase_discount_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, default=0.0, editable=False, max_digits=10, null=True),
        ),
    ]
