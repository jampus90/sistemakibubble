from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Produto, Venda, ItemVenda


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(username='funcionario', password='senha123', is_staff=False):
    return User.objects.create_user(username=username, password=password, is_staff=is_staff)

def make_admin(username='admin', password='senha123'):
    return make_user(username=username, password=password, is_staff=True)

def make_produto(**kwargs):
    defaults = {'nome': 'Temaki', 'preco_unitario': 15.00, 'quantidade_estoque': 10}
    defaults.update(kwargs)
    return Produto.objects.create(**defaults)


# ── Autenticação ──────────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('login')

    def test_get_exibe_formulario(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_com_credenciais_validas(self):
        response = self.client.post(self.url, {
            'username': 'funcionario',
            'password': 'senha123',
        })
        self.assertRedirects(response, reverse('pdv'))

    def test_login_com_credenciais_invalidas(self):
        response = self.client.post(self.url, {
            'username': 'funcionario',
            'password': 'errada',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIn('error', response.context)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('logout')
        self.client.login(username='funcionario', password='senha123')

    def test_logout_redireciona_para_login(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('login'))

    def test_logout_encerra_sessao(self):
        self.client.post(self.url)
        response = self.client.get(reverse('pdv'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('pdv')}")

    def test_logout_sem_autenticacao_redireciona(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('login'))


class RegisterViewTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.url = reverse('register')

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_redireciona_nao_admin(self):
        make_user(username='comum')
        self.client.login(username='comum', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_admin_acessa_formulario(self):
        self.client.login(username='admin', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_admin_cria_usuario(self):
        self.client.login(username='admin', password='senha123')
        response = self.client.post(self.url, {
            'username': 'novo_func',
            'password': 'senha456',
            'email': 'novo@email.com',
        })
        self.assertRedirects(response, reverse('pdv'))
        self.assertTrue(User.objects.filter(username='novo_func').exists())

    def test_username_duplicado_exibe_erro(self):
        self.client.login(username='admin', password='senha123')
        self.client.post(self.url, {'username': 'duplicado', 'password': '123', 'email': ''})
        response = self.client.post(self.url, {'username': 'duplicado', 'password': '456', 'email': ''})
        self.assertIn('error', response.context)


# ── Estoque ───────────────────────────────────────────────────────────────────

class EstoqueListViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('estoque_list')

    def test_redireciona_nao_autenticado(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_lista_produtos(self):
        make_produto(nome='Temaki')
        make_produto(nome='Bubble Tea', preco_unitario=12.00, quantidade_estoque=3)
        self.client.login(username='funcionario', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temaki')
        self.assertContains(response, 'Bubble Tea')

    def test_alerta_estoque_baixo(self):
        make_produto(nome='Produto Baixo', quantidade_estoque=2)
        self.client.login(username='funcionario', password='senha123')
        response = self.client.get(self.url)
        self.assertContains(response, 'Estoque baixo')

    def test_botao_deletar_visivel_para_admin(self):
        make_produto()
        admin = make_admin(username='admin2')
        self.client.login(username='admin2', password='senha123')
        response = self.client.get(self.url)
        self.assertContains(response, 'Deletar')

    def test_botao_deletar_invisivel_para_nao_admin(self):
        make_produto()
        self.client.login(username='funcionario', password='senha123')
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Deletar')


class EstoqueCreateViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('estoque_create')
        self.client.login(username='funcionario', password='senha123')

    def test_get_exibe_formulario(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'estoque_form.html')

    def test_cria_produto(self):
        response = self.client.post(self.url, {
            'nome': 'Temaki Salmão',
            'preco_unitario': '18.50',
            'quantidade_estoque': '20',
        })
        self.assertRedirects(response, reverse('estoque_list'))
        self.assertTrue(Produto.objects.filter(nome='Temaki Salmão').exists())

    def test_campos_obrigatorios(self):
        response = self.client.post(self.url, {'nome': '', 'preco_unitario': ''})
        self.assertIn('error', response.context)
        self.assertEqual(Produto.objects.count(), 0)


class EstoqueEditViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto()
        self.url = reverse('estoque_edit', args=[self.produto.pk])
        self.client.login(username='funcionario', password='senha123')

    def test_get_preenchido_com_dados_atuais(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.produto.nome)

    def test_edita_produto(self):
        response = self.client.post(self.url, {
            'nome': 'Temaki Editado',
            'preco_unitario': '20.00',
            'quantidade_estoque': '5',
        })
        self.assertRedirects(response, reverse('estoque_list'))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.nome, 'Temaki Editado')

    def test_produto_inexistente_retorna_404(self):
        response = self.client.get(reverse('estoque_edit', args=[9999]))
        self.assertEqual(response.status_code, 404)


class EstoqueDeleteViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto()
        self.url = reverse('estoque_delete', args=[self.produto.pk])
        self.client.login(username='funcionario', password='senha123')

    def test_get_exibe_confirmacao(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'estoque_confirm_delete.html')
        self.assertContains(response, self.produto.nome)

    def test_post_deleta_produto(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('estoque_list'))
        self.assertFalse(Produto.objects.filter(pk=self.produto.pk).exists())

    def test_produto_inexistente_retorna_404(self):
        response = self.client.post(reverse('estoque_delete', args=[9999]))
        self.assertEqual(response.status_code, 404)


# ── PDV ───────────────────────────────────────────────────────────────────────

class PDVViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('pdv')
        self.client.login(username='funcionario', password='senha123')

    def test_redireciona_nao_autenticado(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_get_exibe_produtos_com_estoque(self):
        make_produto(nome='Temaki', quantidade_estoque=10)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Temaki')

    def test_produtos_sem_estoque_nao_aparecem(self):
        make_produto(nome='Esgotado', quantidade_estoque=0)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Esgotado')


class AdicionarAoCarrinhoTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto(quantidade_estoque=5)
        self.url = reverse('pdv_adicionar')
        self.client.login(username='funcionario', password='senha123')

    def test_adicionar_produto_ao_carrinho(self):
        response = self.client.post(self.url, {
            'produto_id': self.produto.pk,
            'quantidade': 2,
        })
        self.assertRedirects(response, reverse('pdv'))
        carrinho = self.client.session['carrinho']
        self.assertIn(str(self.produto.pk), carrinho)
        self.assertEqual(carrinho[str(self.produto.pk)]['quantidade'], 2)

    def test_adicionar_produto_sem_estoque_falha(self):
        produto_vazio = make_produto(nome='Vazio', quantidade_estoque=0)
        response = self.client.post(self.url, {
            'produto_id': produto_vazio.pk,
            'quantidade': 1,
        })
        self.assertRedirects(response, reverse('pdv'))
        carrinho = self.client.session.get('carrinho', {})
        self.assertNotIn(str(produto_vazio.pk), carrinho)

    def test_quantidade_maior_que_estoque_limita_ao_estoque(self):
        response = self.client.post(self.url, {
            'produto_id': self.produto.pk,
            'quantidade': 99,
        })
        self.assertRedirects(response, reverse('pdv'))
        carrinho = self.client.session['carrinho']
        self.assertEqual(carrinho[str(self.produto.pk)]['quantidade'], self.produto.quantidade_estoque)

    def test_adicionar_mesmo_produto_acumula_quantidade(self):
        self.client.post(self.url, {'produto_id': self.produto.pk, 'quantidade': 2})
        self.client.post(self.url, {'produto_id': self.produto.pk, 'quantidade': 2})
        carrinho = self.client.session['carrinho']
        self.assertEqual(carrinho[str(self.produto.pk)]['quantidade'], 4)


class RemoverDoCarrinhoTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto(quantidade_estoque=5)
        self.client.login(username='funcionario', password='senha123')
        # pré-popula o carrinho
        self.client.post(reverse('pdv_adicionar'), {'produto_id': self.produto.pk, 'quantidade': 2})

    def test_remover_produto_do_carrinho(self):
        url = reverse('pdv_remover', args=[self.produto.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('pdv'))
        carrinho = self.client.session.get('carrinho', {})
        self.assertNotIn(str(self.produto.pk), carrinho)


class FinalizarVendaTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto(preco_unitario='20.00', quantidade_estoque=10)
        self.url = reverse('pdv_finalizar')
        self.client.login(username='funcionario', password='senha123')
        # pré-popula o carrinho com 3 unidades
        self.client.post(reverse('pdv_adicionar'), {'produto_id': self.produto.pk, 'quantidade': 3})

    def test_finalizar_cria_venda_e_itens(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('pdv'))
        self.assertEqual(Venda.objects.count(), 1)
        self.assertEqual(ItemVenda.objects.count(), 1)

    def test_finalizar_calcula_total_correto(self):
        self.client.post(self.url)
        venda = Venda.objects.first()
        self.assertEqual(venda.total_venda, 60.00)  # 3 x R$20

    def test_finalizar_desconta_estoque(self):
        self.client.post(self.url)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 7)  # 10 - 3

    def test_finalizar_limpa_carrinho(self):
        self.client.post(self.url)
        carrinho = self.client.session.get('carrinho', {})
        self.assertEqual(carrinho, {})

    def test_finalizar_venda_vincula_funcionario(self):
        self.client.post(self.url)
        venda = Venda.objects.first()
        self.assertEqual(venda.funcionario, self.user)

    def test_carrinho_vazio_nao_cria_venda(self):
        # limpa o carrinho
        session = self.client.session
        session['carrinho'] = {}
        session.save()
        self.client.post(self.url)
        self.assertEqual(Venda.objects.count(), 0)


# ── Resumo ────────────────────────────────────────────────────────────────────

def make_venda(user, total='0.00', dias_atras=0):
    """Cria uma Venda diretamente e ajusta a data se necessário."""
    venda = Venda.objects.create(funcionario=user, total_venda=Decimal(total))
    if dias_atras:
        nova_data = timezone.now() - timedelta(days=dias_atras)
        Venda.objects.filter(pk=venda.pk).update(data_hora=nova_data)
        venda.refresh_from_db()
    return venda

def make_item_venda(venda, produto, quantidade, preco):
    return ItemVenda.objects.create(
        venda=venda,
        produto=produto,
        quantidade=quantidade,
        preco_na_hora=Decimal(preco),
    )


class ResumoViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('resumo')
        self.client.login(username='funcionario', password='senha123')

    def test_redireciona_nao_autenticado(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_get_exibe_resumo(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'resumo.html')

    def test_sem_vendas_exibe_zero(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['total_vendido'], 0)
        self.assertEqual(response.context['num_vendas'], 0)

    def test_total_vendido_com_vendas(self):
        make_venda(self.user, total='60.00')
        make_venda(self.user, total='40.00')
        response = self.client.get(self.url)
        self.assertEqual(response.context['total_vendido'], Decimal('100.00'))
        self.assertEqual(response.context['num_vendas'], 2)

    def test_produtos_mais_vendidos_ordenados_por_quantidade(self):
        p1 = make_produto(nome='Temaki', quantidade_estoque=20)
        p2 = make_produto(nome='Bubble Tea', quantidade_estoque=20)
        venda = make_venda(self.user, total='150.00')
        make_item_venda(venda, p1, quantidade=5, preco='15.00')
        make_item_venda(venda, p2, quantidade=2, preco='12.00')
        response = self.client.get(self.url)
        top = list(response.context['produtos_mais_vendidos'])
        self.assertEqual(top[0]['produto__nome'], 'Temaki')
        self.assertEqual(top[0]['total_qtd'], 5)
        self.assertEqual(top[1]['produto__nome'], 'Bubble Tea')

    def test_filtro_data_inicio_exclui_vendas_antigas(self):
        make_venda(self.user, total='30.00', dias_atras=10)  # fora do filtro
        make_venda(self.user, total='50.00', dias_atras=0)   # dentro do filtro
        hoje = timezone.now().date().isoformat()
        response = self.client.get(self.url, {'data_inicio': hoje})
        self.assertEqual(response.context['num_vendas'], 1)
        self.assertEqual(response.context['total_vendido'], Decimal('50.00'))

    def test_filtro_data_fim_exclui_vendas_futuras(self):
        make_venda(self.user, total='20.00', dias_atras=0)   # hoje
        make_venda(self.user, total='40.00', dias_atras=5)   # há 5 dias
        ontem = (timezone.now() - timedelta(days=1)).date().isoformat()
        response = self.client.get(self.url, {'data_fim': ontem})
        self.assertEqual(response.context['num_vendas'], 1)
        self.assertEqual(response.context['total_vendido'], Decimal('40.00'))

    def test_filtro_periodo_completo(self):
        make_venda(self.user, total='10.00', dias_atras=20)  # fora
        make_venda(self.user, total='25.00', dias_atras=5)   # dentro
        make_venda(self.user, total='35.00', dias_atras=3)   # dentro
        inicio = (timezone.now() - timedelta(days=7)).date().isoformat()
        fim = (timezone.now() - timedelta(days=1)).date().isoformat()
        response = self.client.get(self.url, {'data_inicio': inicio, 'data_fim': fim})
        self.assertEqual(response.context['num_vendas'], 2)
        self.assertEqual(response.context['total_vendido'], Decimal('60.00'))


# ── Senha ─────────────────────────────────────────────────────────────────────

class SenhaGeracaoTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.produto = make_produto(preco_unitario='10.00', quantidade_estoque=20)
        self.client.login(username='funcionario', password='senha123')

    def _finalizar(self, wpp=''):
        self.client.post(reverse('pdv_adicionar'), {'produto_id': self.produto.pk, 'quantidade': 1})
        return self.client.post(reverse('pdv_finalizar'), {'numero_wpp': wpp})

    def test_primeira_venda_do_dia_recebe_senha_1(self):
        self._finalizar()
        venda = Venda.objects.first()
        self.assertEqual(venda.senha, 1)

    def test_segunda_venda_recebe_senha_2(self):
        self._finalizar()
        self._finalizar()
        vendas = Venda.objects.order_by('senha')
        self.assertEqual(vendas[1].senha, 2)

    def test_senha_apos_999_volta_para_1(self):
        Venda.objects.create(funcionario=self.user, total_venda='0.00', senha=999)
        self._finalizar()
        nova_venda = Venda.objects.order_by('-id').first()
        self.assertEqual(nova_venda.senha, 1)

    def test_senha_reinicia_em_novo_dia(self):
        venda_ontem = Venda.objects.create(funcionario=self.user, total_venda='0.00', senha=50)
        Venda.objects.filter(pk=venda_ontem.pk).update(data_hora=timezone.now() - timedelta(days=1))
        self._finalizar()
        nova_venda = Venda.objects.order_by('-id').first()
        self.assertEqual(nova_venda.senha, 1)

    def test_venda_com_wpp_salva_numero(self):
        self._finalizar(wpp='5511999998888')
        venda = Venda.objects.first()
        self.assertEqual(venda.numero_wpp, '5511999998888')

    def test_venda_sem_wpp_salva_vazio(self):
        self._finalizar(wpp='')
        venda = Venda.objects.first()
        self.assertEqual(venda.numero_wpp, '')

    def test_senha_aparece_no_contexto_apos_finalizar(self):
        self._finalizar()
        # Senha deve estar na sessão para exibição no PDV
        self.assertEqual(self.client.session.get('ultima_senha'), 1)


# ── Pedidos ───────────────────────────────────────────────────────────────────

class PedidosViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.url = reverse('pedidos')
        self.client.login(username='funcionario', password='senha123')

    def test_redireciona_nao_autenticado(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_exibe_pedidos_pendentes_de_hoje(self):
        venda = make_venda(self.user, total='30.00')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(venda, response.context['pedidos'])

    def test_nao_exibe_pedidos_prontos(self):
        venda = make_venda(self.user, total='30.00')
        Venda.objects.filter(pk=venda.pk).update(status='pronto')
        response = self.client.get(self.url)
        self.assertNotIn(venda, response.context['pedidos'])

    def test_nao_exibe_pedidos_de_outros_dias(self):
        venda = make_venda(self.user, total='30.00', dias_atras=1)
        response = self.client.get(self.url)
        self.assertNotIn(venda, response.context['pedidos'])


class MarcarProntoTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.venda = make_venda(self.user, total='30.00')
        Venda.objects.filter(pk=self.venda.pk).update(senha=42, numero_wpp='5511999998888')
        self.venda.refresh_from_db()
        self.url = reverse('pedido_pronto', args=[self.venda.pk])
        self.client.login(username='funcionario', password='senha123')

    def test_marcar_pronto_atualiza_status(self):
        self.client.post(self.url)
        self.venda.refresh_from_db()
        self.assertEqual(self.venda.status, 'pronto')

    def test_marcar_pronto_redireciona_para_pedidos_com_wpp(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('pedidos'), response['Location'])
        self.assertIn('pronto_senha=42', response['Location'])
        self.assertIn('5511999998888', response['Location'])

    def test_marcar_pronto_sem_wpp_redireciona_para_pedidos(self):
        Venda.objects.filter(pk=self.venda.pk).update(numero_wpp='')
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('pedidos'))

    def test_pedido_inexistente_retorna_404(self):
        response = self.client.post(reverse('pedido_pronto', args=[9999]))
        self.assertEqual(response.status_code, 404)


# ── Navbar ────────────────────────────────────────────────────────────────────

class NavbarAdminButtonTest(TestCase):
    def setUp(self):
        self.url = reverse('estoque_list')

    def test_admin_ve_dropdown_admin(self):
        make_admin(username='admin_nav')
        self.client.login(username='admin_nav', password='senha123')
        response = self.client.get(self.url)
        self.assertContains(response, 'dropdown-toggle')
        self.assertContains(response, 'Registrar Usuário')

    def test_nao_admin_ve_link_desabilitado(self):
        make_user(username='func_nav')
        self.client.login(username='func_nav', password='senha123')
        response = self.client.get(self.url)
        self.assertContains(response, 'nav-link disabled')
        self.assertNotContains(response, 'Registrar Usuário')
