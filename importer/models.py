from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import render


class Dados(models.Model):
    SKU = models.CharField(max_length=100)
    QUANTIDADE = models.CharField(max_length=100)
    PRECO = models.CharField(max_length=100)
    DATA = models.DateTimeField()
    MOEDA = models.CharField(max_length=100, default='BRL')


class Produto(models.Model):
    CLASSES_CHOICES = (
        ('FISICA', 'Física'),
        ('DIGITAL', 'Online'),
    )
    sku = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=100)
    da = models.IntegerField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    classe = models.CharField(
        max_length=10, choices=CLASSES_CHOICES, default='FISICA')
    

    def __str__(self):
        return self.nome




class MOEDAS(models.Model):
    MOEDA = models.CharField(max_length=50)
    VALOR = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.nome

class PlanilhaFinal(models.Model):
    
    sku = models.CharField(max_length=50)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateTimeField()
    moeda = models.CharField(max_length=50, default='BRL')
    pedido = models.CharField(max_length=50, default= '')


class ConfiguracaoEmail(models.Model):
    subject = models.CharField(max_length=200)
    message = models.TextField()
    from_email = models.EmailField()


class ProdutoVendido(models.Model):
    sku = models.CharField(max_length=50)
    quantidade = models.IntegerField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)




class Desconto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    data_inicial = models.DateField()
    data_final = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField()

    def __str__(self):
        return f"Desconto de {self.valor} para {self.usuario.username} de {self.data_inicial} a {self.data_final}"
