# Generated by Django 5.1.4 on 2025-01-04 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Income',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exact_date', models.DateField()),
                ('amount', models.BigIntegerField()),
                ('type', models.CharField(choices=[('Cash', 'Cash'), ('Non-Cash', 'Non-Cash')], max_length=10)),
                ('category', models.CharField(max_length=100)),
            ],
        ),
    ]
