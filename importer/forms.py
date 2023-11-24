from django import forms
from .models import Produto
from .models import Desconto, MOEDAS
from django.contrib.auth.models import User
from .models import ConfiguracaoEmail


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['sku', 'nome', 'da', 'usuario', 'classe' ]

class MoedaForm(forms.ModelForm):
     class Meta:
        model = MOEDAS
        fields = ['MOEDA', 'VALOR']

class DescontoForm(forms.ModelForm):
    usuario = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    data_inicial = forms.DateField(widget=forms.TextInput(attrs={'placeholder': 'Data Inicial'}), required=False)
    data_final = forms.DateField(widget=forms.TextInput(attrs={'placeholder': 'Data Final'}), required=False)
    valor = forms.DecimalField(max_digits=10, decimal_places=2)
    observacao = forms.CharField(max_length=255, required=False)

    class Meta:
        model = Desconto
        fields = ['usuario', 'data_inicial', 'data_final', 'valor', 'observacao']

class ConfiguracaoEmailForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoEmail
        fields = ['subject', 'message', 'from_email']