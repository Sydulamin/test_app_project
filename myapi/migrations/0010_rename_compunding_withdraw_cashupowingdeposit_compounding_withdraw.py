# Generated by Django 5.1.3 on 2025-02-27 07:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapi', '0009_rename_compunding_withdraw_cashupdeposit_compounding_withdraw'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cashupowingdeposit',
            old_name='compunding_withdraw',
            new_name='compounding_withdraw',
        ),
    ]
