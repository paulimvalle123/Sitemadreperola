# Generated by Django 4.2.3 on 2023-10-23 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('importer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('from_email', models.EmailField(max_length=254)),
            ],
        ),
    ]