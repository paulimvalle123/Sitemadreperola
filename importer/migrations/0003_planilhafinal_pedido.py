# Generated by Django 4.2.3 on 2023-10-25 02:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0002_configuracaoemail'),
    ]

    operations = [
        migrations.AddField(
            model_name='planilhafinal',
            name='pedido',
            field=models.CharField(default='', max_length=50),
        ),
    ]
