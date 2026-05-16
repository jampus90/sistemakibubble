from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendas', '0003_add_tipo_to_produto'),
    ]

    operations = [
        migrations.AddField(
            model_name='venda',
            name='forma_pagamento',
            field=models.CharField(
                choices=[('cartao', 'Cartão'), ('pix', 'Pix'), ('dinheiro', 'Dinheiro')],
                default='cartao',
                max_length=10,
            ),
        ),
    ]
