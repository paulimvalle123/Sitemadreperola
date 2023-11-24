from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from .models import Dados, PlanilhaFinal
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import ProdutoForm
from .forms import Produto, MoedaForm
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.contrib.auth import logout
from io import BytesIO
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
import io
import pandas as pd
from datetime import datetime
from django.utils import timezone
from .forms import DescontoForm
from .models import Desconto
import base64
import pandas as pd
from datetime import datetime
from decimal import Decimal
from django.shortcuts import render
from .models import PlanilhaFinal, MOEDAS
from django.utils import timezone
from django.core.mail import send_mail
from datetime import datetime
from django.db.models import Q
from .forms import ConfiguracaoEmail
from .forms import ConfiguracaoEmailForm
from django.core.mail import send_mail, EmailMessage




def index(request):
    
    return render(request, 'index.html')


def import_csv(request):

    df_final = pd.DataFrame(columns=['SKU', 'QUANTIDADE', 'PRECO', 'DATA', 'MOEDA'])

    if request.method == 'POST':
        csv_file_metabook = request.FILES.get('csv_file_metabook')
        csv_file_amazon = request.FILES.get('csv_file_amazon')
        csv_file_bling = request.FILES.get('csv_file_bling')
        pedidos_duplicados = []

        if csv_file_metabook:
            if csv_file_metabook.name != 'METABOOK.csv':
                return render(request, 'import.html', {'erro': 'Nome do arquivo METABOOK incorreto'})

            df_metabook = pd.read_csv(csv_file_metabook, sep=';', usecols=[
                                      'Pedido','Sku', 'Quantidade', 'Valor com desconto', 'Data venda'])
            df_metabook['Data venda'] = df_metabook['Data venda'].apply(
                lambda x: datetime.strptime(x, '%d/%m/%Y %H:%M'))
            df_metabook['Moeda'] = 'BRL'
            # Renomear as colunas
            df_metabook.rename(columns={
                'Pedido': 'PEDIDO',
                'Sku': 'SKU',
                'Quantidade': 'QUANTIDADE',
                'Valor com desconto':'PRECO',
                'Data venda': 'DATA',
                'Moeda': 'MOEDA',
            }, inplace=True)
            df_metabook.drop_duplicates(subset=['PEDIDO', 'SKU'], keep='first', inplace=True)

            df_final = pd.concat([df_final, df_metabook], ignore_index=True)

        if csv_file_amazon:
            if csv_file_amazon.name != 'AMAZON.csv':
                return render(request, 'import.html', {'erro': 'Nome do arquivo AMAZON incorreto'})

            df_amazon = pd.read_csv(csv_file_amazon, sep=';', usecols=[
                                    'Código ASIN/ISBN', 'Unidades vendidas', 'Royalties', 'Data dos royalties', 'Moeda',])
            df_amazon['Data dos royalties'] = df_amazon['Data dos royalties'].apply(
                lambda x: datetime.strptime(x, '%d/%m/%Y %H:%M'))
            df_amazon['PEDIDO'] = ' '

            df_amazon.rename(columns={
                'Código ASIN/ISBN': 'SKU',
                'Unidades vendidas': 'QUANTIDADE',
                'Royalties': 'PRECO',
                'Data dos royalties': 'DATA',
                'Moeda': 'MOEDA',
            }, inplace=True)
            for index, row in df_amazon.iterrows():
                moeda = row['MOEDA']
                try:
        # Tente obter o valor de conversão da moeda no banco de dados
                    valor_conversao = MOEDAS.objects.get(MOEDA=moeda).VALOR
                except MOEDAS.DoesNotExist:
        # Trate o caso em que a moeda não existe no banco de dados
                    valor_conversao = 1  # Use 1.0 como valor padrão (sem conversão)
                

    # Aplique a conversão multiplicando o preço pelo valor de conversão
                preco = Decimal(row['PRECO'].replace(',', '.'))
                df_amazon.at[index, 'PRECO'] = preco * valor_conversao    

            df_final = pd.concat([df_final, df_amazon], ignore_index=True)

        if csv_file_bling:
            if csv_file_bling.name != 'BLING.csv':
                return render(request, 'import.html', {'erro': 'Nome do arquivo BLING incorreto'})

            df_bling = pd.read_csv(csv_file_bling, sep=';', usecols=[
                                   'N√∫mero', 'C√≥digo', 'Quantidade', 'Valor total', 'Data de emiss√£o'])
            df_bling['Data de emiss√£o'] = df_bling['Data de emiss√£o'].apply(
                lambda x: datetime.strptime(x, '%d/%m/%Y %H:%M'))
            df_bling['Moeda'] = 'BRL'
            df_bling.rename(columns={
                'N√∫mero':'PEDIDO',
                'C√≥digo': 'SKU',
                'Quantidade': 'QUANTIDADE',
                'Valor total': 'PRECO',
                'Data de emiss√£o': 'DATA',
                'Moeda': 'MOEDA',
            }, inplace=True)

            df_bling.drop_duplicates(subset=['PEDIDO', 'SKU'], keep='first', inplace=True)

            df_final = pd.concat([df_final, df_bling], ignore_index=True)

    

    # Converter o DataFrame agrupado em uma lista de dicionários
    planilha_final = df_final.to_dict(orient='records')

    for linha in planilha_final:
        sku = linha['SKU']
        moeda = linha['MOEDA']
        data_str = timezone.make_aware(linha['DATA'])
        quantidade = linha['QUANTIDADE']
        preco = Decimal(str(linha['PRECO']).replace(",", "."))
        pedido = linha['PEDIDO']

        # Utilizar o método to_pydatetime para converter a data para datetime.datetime
        data = pd.to_datetime(data_str)

        planilha_existente = PlanilhaFinal.objects.filter(
            sku=sku, data=data).first()
        if planilha_existente:
            # Se já existir, atualiza a quantidade, preço e mês
            planilha_existente.quantidade = quantidade
            planilha_existente.preco = preco
            planilha_existente.save()
        else:
            # Se não existir, cria uma nova entrada no banco de dados
            planilha = PlanilhaFinal(
                pedido=pedido, sku=sku, data=data, quantidade=quantidade, preco=preco, moeda=moeda,)
            planilha.save()

    planilha_final = PlanilhaFinal.objects.all()

    return render(request, 'import.html', {'planilha_final': planilha_final})



def limpar_planilhas(request):
    
    #PlanilhaFinal.objects.filter().delete()
    if request.method == 'POST':
        linhas_selecionados = request.POST.getlist('selecionar')

        # Excluir os usuários selecionados
        PlanilhaFinal.objects.filter(id__in=linhas_selecionados).delete()

    return redirect('import_csv')


def login_usuario(request):
    return render(request, 'login.html')


def fazer_login(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')

        # Faça a verificação do nome e senha no banco de dados
        user = authenticate(request, username=usuario, password=senha)

        # Exemplo de verificação simples
        if user is not None:
            # Login bem-sucedido, redirecione para a página inicial
            login(request, user)
            return redirect('produtos_vendidos')
        else:
            # Credenciais inválidas, redirecione para a página de login novamente com uma mensagem de erro
            messages.error(request, 'Usuário ou senha incorretos.')
            return redirect('login_usuario')

    return redirect('login_usuario')


def fazer_logout(request):
    logout(request)
    return redirect('login_usuario')


def cadastrar_usuario(request):

    if request.method == 'POST':
        nome = request.POST.get('nome')
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')
        email = request.POST.get('email')
        dados = request.POST.get('dados')

        if User.objects.filter(username=usuario).exists():
            return redirect('cadastrar_usuario')

        User.objects.create_user(
            username=usuario, password=senha, first_name=nome, email=email, last_name=dados)

        return redirect('cadastrar_usuario')

    return render(request, 'cadastrar_usuario.html')


def cadastrar_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = ProdutoForm()

    return render(request, 'cadastrar_produto.html', {'form': form})


def cadastrar_desconto(request):
   
    if request.method == 'POST':
        form = DescontoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_descontos')
    else:
        form = DescontoForm()

    return render(request, 'cadastrar_desconto.html', {'form': form})


def cadastrar_moeda(request):

    
    if request.method == 'POST':
        form = MoedaForm(request.POST)
        if form.is_valid():
            form.save()
            # Redireciona para a página de listagem de moedas
            return redirect('listar_moedas')
    else:
        form = MoedaForm()
    return render(request, 'cadastrar_moeda.html', {'form': form})


def listar_usuarios(request):
    usuarios = User.objects.all()

    if request.method == 'POST':
        # Obter a lista de IDs dos usuários selecionados
        ids_selecionados = request.POST.getlist('selecionar')

        # Excluir os usuários selecionados do banco de dados
        User.objects.filter(id__in=ids_selecionados).delete()

        # Redirecionar para a página de listar usuários novamente
        return redirect('listar_usuarios')

    return render(request, 'listar_usuarios.html', {'usuarios': usuarios})


def listar_produtos(request):
    produtos = Produto.objects.all()
    return render(request, 'listar_produtos.html', {'produtos': produtos})


def listar_descontos(request):
    descontos = Desconto.objects.all()
    return render(request, 'listar_descontos.html', {'descontos': descontos})


def listar_moedas(request):
    moedas = MOEDAS.objects.all()
    return render(request, 'listar_moedas.html', {'moedas': moedas})


def limpar_usuarios(request):
    if request.method == 'POST':
        usuarios_selecionados = request.POST.getlist('selecionar')

        # Excluir os usuários selecionados
        User.objects.filter(id__in=usuarios_selecionados).delete()

    return redirect('listar_usuarios')


def limpar_descontos(request, ):
    if request.method == 'POST':
        descontos_selecionados = request.POST.getlist('selecionar')
        Desconto.objects.filter(id__in=descontos_selecionados).delete()
        return redirect('listar_descontos')
    return render(request, 'listar_descontos.html')


def limpar_moedas(request, ):
    if request.method == 'POST':
        moedas_selecionadas = request.POST.getlist('selecionar')
        MOEDAS.objects.filter(id__in=moedas_selecionadas).delete()
        return redirect('listar_moedas')
    return render(request, 'listar_moedas.html')


def limpar_produtos(request):
    if request.method == 'POST':
        produtos_selecionados = request.POST.getlist('selecionar')

        # Excluir os usuários selecionados
        Produto.objects.filter(id__in=produtos_selecionados).delete()

        return redirect('listar_produtos')
    return render(request, 'listar_produtos.html')


def editar_produto(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)

    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('listar_produtos')
    else:
        form = ProdutoForm(instance=produto)

    return render(request, 'editar_produto.html', {'form': form})



def editar_moeda(request, moeda_id):
    moeda = get_object_or_404(MOEDAS, id=moeda_id)

    if request.method == 'POST':
        form = MoedaForm(request.POST, instance=moeda)
        if form.is_valid():
            form.save()
            return redirect('listar_moedas')
    else:
        form = MoedaForm(instance=moeda)

    return render(request, 'editar_moeda.html', {'form': form})



@login_required(login_url='fazer_login')
def produtos_vendidos(request):
    
    usuario_logado = request.user
    planilha_final = PlanilhaFinal.objects.all()
    is_admin = request.user.username == 'admin'
    usuarios_dropdown = User.objects.exclude(username='admin') if is_admin else None
    usuario_selecionado = None
    

    if is_admin and request.method == 'POST':
        usuario_id = request.POST.get('usuario_selecionado')
        if usuario_id:
            usuario_selecionado = get_object_or_404(User, id=usuario_id)
    else:
        usuario_selecionado = request.user

    data_inicial = request.POST.get('data_inicial')
    data_final = request.POST.get('data_final')
    produtos_cadastrados = Produto.objects.filter(usuario=usuario_selecionado) if usuario_selecionado else Produto.objects.filter(usuario=usuario_logado)


    # Converta as datas de início e fim em objetos datetime com informações de fuso horário
    if data_inicial and data_final:
        data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
        data_inicial = timezone.make_aware(data_inicial)
        data_final = datetime.strptime(data_final, '%Y-%m-%d')
        data_final = timezone.make_aware(data_final)
    else:
        data_inicial = timezone.make_aware(datetime(2020, 1, 1))
        data_final = timezone.make_aware(datetime(2020, 1, 15))


    produtos_fisicos = []
    produtos_digitais = []
    total_da_geral = 0
    da_receber = 0
    descontos = 0

    if is_admin:
        quantidade_vendida = 0
        total_vendido = 0
        preco = 0
        medio = 0
        da_medio = 0
        total_da = 0
        da = 0
        sku = None

    for produto in produtos_cadastrados:
        sku = produto.sku
        da = produto.da
        quantidade_vendida = 0
        total_vendido = 0
        medio = 0
        da_medio = 0
        total_da = 0

        desconto_mes_usuario = None

        if is_admin:
            try:
                desconto_mes_usuario = Desconto.objects.get(
                    usuario=usuario_selecionado,
                    data_inicial__lte=data_final,
                    data_final__gte=data_inicial
                )
            except Desconto.DoesNotExist:
                pass
        else:
            try:
                desconto_mes_usuario = Desconto.objects.get(
                    usuario=usuario_logado,
                    data_inicial__lte=data_final,
                    data_final__gte=data_inicial
                )
            except Desconto.DoesNotExist:
                pass

        for item in planilha_final:
            if sku == item.sku:
                data_venda = item.data
                
                if data_inicial <= data_venda <= data_final:
                    quantidade_vendida += item.quantidade
                    preco = item.preco
                    total_vendido += (item.preco)


        if quantidade_vendida > 0:
            medio = round(total_vendido / quantidade_vendida, 2)
            total_da = round(da * medio * quantidade_vendida / 100, 2)
            total_da_geral += total_da
            da_medio = round(medio * da / 100, 2)
        else:
            medio = 0
            da_medio = 0
            total_da = 0
            total_da_geral += total_da

        if desconto_mes_usuario:
            descontos = round(desconto_mes_usuario.valor, 2)
            da_receber = total_da_geral - descontos
        else:
            descontos = 0
            da_receber = total_da_geral

        if produto.classe == 'FISICA':
            produtos_fisicos.append(
                (produto, quantidade_vendida, medio, da_medio, total_da))
        elif produto.classe == 'DIGITAL':
            produtos_digitais.append(
                (produto, quantidade_vendida, medio, da_medio, total_da))

    context = {
        'user': usuario_logado,
        'produtos_fisicos': produtos_fisicos,
        'produtos_digitais': produtos_digitais,
        'da': da,
        'total_da': total_da,
        'total_da_geral': total_da_geral,
        'da_receber': da_receber,
        'descontos': descontos,
        'usuarios_dropdown': usuarios_dropdown,
        'usuario_selecionado': usuario_selecionado,
        'data_inicial': data_inicial,
        'data_final': data_final,
        
    }

    return render(request, 'produtos_vendidos.html', context)


@login_required(login_url='fazer_login')
def gerar_pdf_produtos_vendidos(request, usuario_selecionado):
    with open('static/madre3.jpg', 'rb') as img_file:
        imagem_bytes = img_file.read()
        imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
    with open('static/assinatura.png', 'rb') as img_file:
        imagem_bytes2 = img_file.read()
        imagem_base642 = base64.b64encode(imagem_bytes2).decode('utf-8')

    usuario_logado = usuario_selecionado
    planilha_final = PlanilhaFinal.objects.all()
    produtos_cadastrados = Produto.objects.filter(
        usuario=usuario_selecionado) if usuario_selecionado else Produto.objects.filter(usuario=usuario_logado)
    usuario_selecionado_nome = get_object_or_404(User, id=usuario_selecionado)

    # Criamos um dicionário com os números dos meses e seus respectivos nomes para o menu suspenso
    
    data_inicial = request.GET.get('data_inicial')
    data_final = request.GET.get('data_final')
    data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
    data_inicial = timezone.make_aware(data_inicial)
    data_final = datetime.strptime(data_final, '%Y-%m-%d')
    data_final = timezone.make_aware(data_final)




    try:
        # Tente obter o desconto correspondente ao mês selecionado e ao usuário logado
        desconto_mes_usuario = Desconto.objects.get(
                    usuario=usuario_selecionado,
                    data_inicial__lte=data_final,
                    data_final__gte=data_inicial
                )
    except Desconto.DoesNotExist:
        # Caso não exista desconto, atribua None
        desconto_mes_usuario = None

    produtos_fisicos = []
    produtos_digitais = []
    total_da_geral = 0
    da_receber = 0
    descontos = 0

    for produto in produtos_cadastrados:
        sku = produto.sku
        da = produto.da
        quantidade_vendida = 0
        total_vendido = 0
        medio = 0
        da_medio = 0
        total_da = 0

        descontos = Desconto.objects.filter(
                    usuario=usuario_selecionado,
                    data_inicial__lte=data_final,
                    data_final__gte=data_inicial
                )

        for item in planilha_final:
            if sku == item.sku:
                data_venda = item.data
                
                if data_inicial <= data_venda <= data_final:
                    quantidade_vendida += item.quantidade
                    preco = item.preco
                    total_vendido += (item.quantidade * item.preco)



        if quantidade_vendida > 0:
            medio = round(total_vendido / quantidade_vendida, 2)
            total_da = round(da*medio*quantidade_vendida/100, 2)
            total_da_geral += total_da
            da_medio = round(medio*da/100, 2)

        else:
            medio = 0
            da_medio = 0
            total_da = 0
            total_da_geral += total_da

        if desconto_mes_usuario:
            # Calcular o valor com desconto
            descontos = round(desconto_mes_usuario.valor, 2)
            da_receber = total_da_geral - descontos
        else:
            descontos = 0
            da_receber = total_da_geral

        if produto.classe == 'FISICA':
            produtos_fisicos.append(
                (produto, quantidade_vendida, medio, da_medio, total_da))
        elif produto.classe == 'DIGITAL':
            produtos_digitais.append(
                (produto, quantidade_vendida, medio, da_medio, total_da))

    context = {
        'user': usuario_logado,
        'produtos_fisicos': produtos_fisicos,
        'produtos_digitais': produtos_digitais,
        'da': da,
        'total_da': total_da,
        'total_da_geral': total_da_geral,
        'da_receber': da_receber,
        'descontos': descontos,
        'usuario_selecionado': usuario_selecionado,
        'usuario_selecionado_nome': usuario_selecionado_nome,
        'data_inicial': data_inicial,
        'data_final': data_final,
        'imagem_base64': imagem_base64,
        'imagem_base642': imagem_base642,

    }

    template = get_template('produtos_vendidos_pdf.html')
    html = template.render(context)
    response = io.BytesIO()

    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), response)

    if not pdf.err:
        response = HttpResponse(response.getvalue(),
                                content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="produtos_vendidos.pdf"'
        return response

    return HttpResponse("Erro ao gerar o PDF.", status=500)


def consolidado(request):
    usuarios = User.objects.all()
    usuarios = User.objects.exclude(username='admin')

    data_inicial = request.POST.get('data_inicial')
    data_final = request.POST.get('data_final')
        

    # Lista para armazenar as informações de produtos vendidos de todos os usuários
    produtos_vendidos = []
    
    if data_inicial and data_final:
        data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
        data_inicial = timezone.make_aware(data_inicial)
        data_final = datetime.strptime(data_final, '%Y-%m-%d')
        data_final = timezone.make_aware(data_final)
    else:
        data_inicial = timezone.make_aware(datetime(2020, 1, 1))
        data_final = timezone.make_aware(datetime(2020, 1, 15))

    for usuario in usuarios:
        planilha_final = PlanilhaFinal.objects.all()
        produtos_cadastrados = Produto.objects.filter(usuario=usuario)
        desconto_mes_usuario = None
        

        total_da_geral = 0
        da_receber = 0
        descontos = 0

        for produto in produtos_cadastrados:
            sku = produto.sku
            da = produto.da
            quantidade_vendida = 0
            total_vendido = 0
            medio = 0
            da_medio = 0
            total_da = 0

            try:
                desconto_mes_usuario = Desconto.objects.get(
                    usuario=usuario,
                    data_inicial__lte=data_final,
                    data_final__gte=data_inicial
                )
            except Desconto.DoesNotExist:
                pass




            for item in planilha_final:
                if sku == item.sku:
                    data_venda = item.data
                    

                    if data_inicial <= data_venda <= data_final:
                        quantidade_vendida += item.quantidade
                        preco = item.preco
                        total_vendido += (item.quantidade * item.preco)

            if quantidade_vendida > 0:
                medio = round(total_vendido / quantidade_vendida, 2)
                total_da = round(da * medio * quantidade_vendida / 100, 2)
                total_da_geral += total_da
                da_medio = round(medio * da / 100, 2)
            else:
                medio = 0
                da_medio = 0
                total_da = 0
                total_da_geral += total_da

            if desconto_mes_usuario:
                descontos = round(desconto_mes_usuario.valor, 2)
                da_receber = total_da_geral - descontos
            else:
                descontos = 0

        # Adiciona as informações na lista
        produtos_vendidos.append(
            (usuario, total_da_geral, descontos, da_receber))

    context = {
        'usuarios': usuarios,
        'produtos_vendidos': produtos_vendidos,
        'data_inicial': data_inicial,
        'data_final': data_final,
        
    }

    return render(request, 'consolidado.html', context)


def vendas_por_mes(request):
    meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3,
                                           'Março'), (4, 'Abril'), (5, 'Maio'), (6, 'Junho'),
        (7, 'Julho'), (8, 'Agosto'), (9, 'Setembro'), (10,
                                                       'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]

    if request.method == 'POST':
        mes_selecionado = request.POST.get('mes')
        planilha_final = PlanilhaFinal.objects.filter(mes=mes_selecionado)
    else:
        mes_selecionado = None
        planilha_final = PlanilhaFinal.objects.all()

    return render(request, 'produtos_vendidos.html', {'planilha_final': planilha_final, 'meses': meses, 'mes_selecionado': mes_selecionado})

def envia_email(request):
    users = User.objects.all()

    # Obtenha as configurações de email do banco de dados
    configuracao = ConfiguracaoEmail.objects.first()  # Assume que há apenas uma configuração

    if configuracao:
        # Use as configurações obtidas do banco de dados
        subject = configuracao.subject
        message = configuracao.message
        from_email = configuracao.from_email

        # Lista de destinatários
        recipient_list = [user.email for user in users]

        # Envie o email
        email = EmailMessage(subject, message, from_email, [], bcc=recipient_list)
        email.send()
                  

    return render(request, 'editar_email.html')



def editar_email(request):
    configuracao = ConfiguracaoEmail.objects.first()  # Assume que há apenas uma configuração

    if request.method == 'POST':
        form = ConfiguracaoEmailForm(request.POST, instance=configuracao)
        if form.is_valid():
            form.save()
            return redirect('editar_email')  # Redirecione para a página desejada após salvar
    else:
        form = ConfiguracaoEmailForm(instance=configuracao)

    return render(request, 'editar_email.html', {'form': form})