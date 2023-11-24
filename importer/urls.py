from django.urls import path
from importer import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rota para a página inicial
    path('', views.index, name='index'),
    path('importer/import/', views.import_csv, name='import_csv'),
    path('envia_email/', views.envia_email, name='envia_email'),
    
    path('editar_email/', views.editar_email, name='editar_email'),       
    path('import/', views.import_csv, name='import_csv'),   
    
    path('login/', views.login_usuario, name='login_usuario'),    
    path('fazer-login/', views.fazer_login, name='fazer_login'),
    path('logout/', LogoutView.as_view(next_page='login_usuario'), name='logout'),


    path('cadastrar_usuario/', views.cadastrar_usuario, name='cadastrar_usuario'),       
    path('cadastrar_produto/', views.cadastrar_produto, name='cadastrar_produto'),
    path('cadastrar_desconto/', views.cadastrar_desconto, name='cadastrar_desconto'),
    path('cadastrar_moeda/', views.cadastrar_moeda, name='cadastrar_moeda'), 

   
    path('listar_usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('listar_produtos/', views.listar_produtos, name='listar_produtos'),
    path('listar_descontos/', views.listar_descontos, name='listar_descontos'),
    path('listar_moedas/', views.listar_moedas, name='listar_moedas'),  

    
    path('limpar_usuarios/', views.limpar_usuarios, name='limpar_usuarios'), 
    path('limpar_produtos/', views.limpar_produtos, name='limpar_produtos'),
    path('limpar_descontos/', views.limpar_descontos, name='limpar_descontos'),
    path('limpar_moedas/', views.limpar_moedas, name='limpar_moedas'),
    path('limpar_planilhas/', views.limpar_planilhas, name='limpar_planilhas'), 

    path('editar_produto/<int:produto_id>/', views.editar_produto, name='editar_produto'),    
    path('editar_moeda/<int:moeda_id>/', views.editar_moeda, name='editar_moeda'),



    path('produtos-vendidos/', views.produtos_vendidos, name='produtos_vendidos'),
    path('gerar_pdf_produtos_vendidos/<int:usuario_selecionado>/', views.gerar_pdf_produtos_vendidos, name='gerar_pdf_produtos_vendidos'),
    path('produtos_vendidos/', views.vendas_por_mes, name='vendas_por_mes'),  
    path('consolidado/', views.consolidado, name='consolidado'),

]
