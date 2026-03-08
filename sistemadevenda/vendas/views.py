from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from .models import Produto, Venda, ItemVenda

ESTOQUE_BAIXO = 5

def index(request):
    if request.user.is_authenticated:
        return redirect('pdv')
    return redirect('login')

def login(request):
    if request.user.is_authenticated:
        return redirect('pdv')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            RefreshToken.for_user(user)  # gera token JWT para uso futuro na API
            next_url = request.POST.get('next') or request.GET.get('next') or 'pdv'
            return redirect(next_url)
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    next_url = request.GET.get('next', '')
    return render(request, 'login.html', {'next': next_url})

def logout(request):
    auth_logout(request)
    return redirect('login')

def is_admin(user):
    return user.is_staff

@login_required(login_url='login')
@user_passes_test(is_admin, login_url='login')
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
        
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        return redirect('pdv')
    
    return render(request, 'register.html')


# ── Estoque ──────────────────────────────────────────────

@login_required(login_url='login')
def estoque_list(request):
    produtos = Produto.objects.all().order_by('nome')
    return render(request, 'estoque_list.html', {
        'produtos': produtos,
        'estoque_baixo': ESTOQUE_BAIXO,
    })


@login_required(login_url='login')
def estoque_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        preco = request.POST.get('preco_unitario', '')
        quantidade = request.POST.get('quantidade_estoque', 0)

        if not nome or not preco:
            return render(request, 'estoque_form.html', {'error': 'Nome e preço são obrigatórios.'})

        Produto.objects.create(nome=nome, preco_unitario=preco, quantidade_estoque=quantidade)
        return redirect('estoque_list')

    return render(request, 'estoque_form.html')


@login_required(login_url='login')
def estoque_edit(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == 'POST':
        produto.nome = request.POST.get('nome', '').strip()
        produto.preco_unitario = request.POST.get('preco_unitario', '')
        produto.quantidade_estoque = request.POST.get('quantidade_estoque', 0)
        produto.save()
        return redirect('estoque_list')

    return render(request, 'estoque_form.html', {'produto': produto})


@login_required(login_url='login')
def estoque_delete(request, pk):
    produto = get_object_or_404(Produto, pk=pk)

    if request.method == 'POST':
        produto.delete()
        return redirect('estoque_list')

    return render(request, 'estoque_confirm_delete.html', {'produto': produto})


# ── PDV ──────────────────────────────────────────────────

@login_required(login_url='login')
def pdv(request):
    produtos = Produto.objects.filter(quantidade_estoque__gt=0).order_by('nome')
    carrinho = request.session.get('carrinho', {})
    total = sum(
        Decimal(item['preco']) * item['quantidade']
        for item in carrinho.values()
    )
    return render(request, 'pdv.html', {
        'produtos': produtos,
        'carrinho': carrinho,
        'total': total,
    })


@login_required(login_url='login')
def pdv_adicionar(request):
    if request.method == 'POST':
        produto_id = str(request.POST.get('produto_id'))
        quantidade = int(request.POST.get('quantidade', 1))

        produto = get_object_or_404(Produto, pk=produto_id)

        if produto.quantidade_estoque == 0:
            return redirect('pdv')

        carrinho = request.session.get('carrinho', {})
        atual = carrinho.get(produto_id, {}).get('quantidade', 0)
        nova_quantidade = min(atual + quantidade, produto.quantidade_estoque)

        carrinho[produto_id] = {
            'nome': produto.nome,
            'preco': str(produto.preco_unitario),
            'quantidade': nova_quantidade,
        }
        request.session['carrinho'] = carrinho

    return redirect('pdv')


@login_required(login_url='login')
def pdv_remover(request, produto_id):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        carrinho.pop(str(produto_id), None)
        request.session['carrinho'] = carrinho
    return redirect('pdv')


@login_required(login_url='login')
def pdv_finalizar(request):
    if request.method == 'POST':
        carrinho = request.session.get('carrinho', {})
        if not carrinho:
            return redirect('pdv')

        total = sum(
            Decimal(item['preco']) * item['quantidade']
            for item in carrinho.values()
        )

        venda = Venda.objects.create(funcionario=request.user, total_venda=total)

        for produto_id, item in carrinho.items():
            produto = Produto.objects.get(pk=produto_id)
            ItemVenda.objects.create(
                venda=venda,
                produto=produto,
                quantidade=item['quantidade'],
                preco_na_hora=Decimal(item['preco']),
            )
            produto.quantidade_estoque -= item['quantidade']
            produto.save()

        request.session['carrinho'] = {}

    return redirect('pdv')


# ── Resumo ────────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def resumo(request):
    vendas = Venda.objects.all()

    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    if data_inicio:
        vendas = vendas.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        vendas = vendas.filter(data_hora__date__lte=data_fim)

    total_vendido = vendas.aggregate(total=Sum('total_venda'))['total'] or 0
    num_vendas = vendas.count()

    produtos_mais_vendidos = (
        ItemVenda.objects
        .filter(venda__in=vendas)
        .values('produto__nome')
        .annotate(total_qtd=Sum('quantidade'))
        .order_by('-total_qtd')[:10]
    )

    return render(request, 'resumo.html', {
        'total_vendido': total_vendido,
        'num_vendas': num_vendas,
        'produtos_mais_vendidos': produtos_mais_vendidos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    })
