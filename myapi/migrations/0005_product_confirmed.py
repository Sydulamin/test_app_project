# Generated by Django 5.1.3 on 2025-02-24 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0004_category_delete_categories_remove_product_categories_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
