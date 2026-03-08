from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    # PDV
    path('pdv/', views.pdv, name='pdv'),
    path('pdv/adicionar/', views.pdv_adicionar, name='pdv_adicionar'),
    path('pdv/remover/<int:produto_id>/', views.pdv_remover, name='pdv_remover'),
    path('pdv/finalizar/', views.pdv_finalizar, name='pdv_finalizar'),
    # Pedidos
    path('pedidos/', views.pedidos, name='pedidos'),
    path('pedidos/<int:pk>/pronto/', views.pedido_pronto, name='pedido_pronto'),
    # Resumo
    path('resumo/', views.resumo, name='resumo'),
    # Estoque
    path('estoque/', views.estoque_list, name='estoque_list'),
    path('estoque/novo/', views.estoque_create, name='estoque_create'),
    path('estoque/<int:pk>/editar/', views.estoque_edit, name='estoque_edit'),
    path('estoque/<int:pk>/deletar/', views.estoque_delete, name='estoque_delete'),
]