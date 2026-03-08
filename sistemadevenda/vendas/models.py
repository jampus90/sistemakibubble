from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    nome = models.CharField(max_length=255)
    numero_wpp = models.CharField(max_length=20, blank=True, null=True, verbose_name="WhatsApp")

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=255)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

class Venda(models.Model):
    STATUS_PENDENTE = 'pendente'
    STATUS_PRONTO = 'pronto'
    STATUS_CHOICES = [
        (STATUS_PENDENTE, 'Pendente'),
        (STATUS_PRONTO, 'Pronto'),
    ]

    funcionario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='vendas')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    data_hora = models.DateTimeField(auto_now_add=True)
    total_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    senha = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDENTE)
    numero_wpp = models.CharField(max_length=20, blank=True, default='')

    def __str__(self):
        return f"Venda #{self.id} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"

class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')  
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)  
    quantidade = models.PositiveIntegerField()
    preco_na_hora = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantidade}x {self.produto.nome} (Venda #{self.venda.id})"