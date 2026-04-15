import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse

from .models import Product
from django.contrib.auth.decorators import login_required
from .forms import ProductForm
from django.contrib.admin.views.decorators import staff_member_required


def validate_password_policy(password):
    errors = []

    if len(password) < 8:
        errors.append("パスワードは8文字以上で入力してください")

    if not re.search(r"[A-Za-z]", password):
        errors.append("パスワードにはアルファベットを含めてください")

    if not re.search(r"\d", password):
        errors.append("パスワードには数字を含めてください")

    return errors


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email:
            return render(request, "accounts/login.html", {
                "error": "メールアドレスを入力してください"
            })

        if not password:
            return render(request, "accounts/login.html", {
                "error": "パスワードを入力してください"
            })

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("product_search")

        return render(request, "accounts/login.html", {
            "error": "メールアドレスまたはパスワードが違います"
        })

    return render(request, "accounts/login.html")


def signup_view(request):
    if request.method == "POST":
        display_name = request.POST.get("display_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        errors = []

        if not display_name:
            errors.append("ユーザー名を入力してください")
        elif re.search(r"\s", display_name):
            errors.append("ユーザー名に空白は使用できません")

        if not email:
            errors.append("メールアドレスを入力してください")
        elif User.objects.filter(email__iexact=email).exists():
            errors.append("このメールアドレスはすでに登録されています")

        if not password:
            errors.append("パスワードを入力してください")

        if password != password_confirm:
            errors.append("パスワードが一致しません")

        errors.extend(validate_password_policy(password))

        if errors:
            return render(request, "accounts/signup.html", {
                "errors": errors,
                "display_name": display_name,
                "email": email,
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=display_name,
        )

        login(request, user)
        return redirect("home")

    return render(request, "accounts/signup.html")


def home_view(request):
    return HttpResponse("ログイン成功！")


def product_search(request):
    keyword = request.GET.get("keyword", "")
    category = request.GET.get("category", "")
    cart = request.session.get("cart", {})
    cart_count = len(cart)

    products = Product.objects.all()

    if keyword:
        products = products.filter(name__icontains=keyword)

    if category:
        products = products.filter(category=category)

    categories = Product.objects.values_list("category", flat=True).distinct()

    return render(request, "accounts/product_search.html", {
        "keyword": keyword,
        "category": category,
        "categories": categories,
        "products": products,
        "cart_count": cart_count,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity_range = range(1, product.stock + 1) if product.stock > 0 else []

    return render(request, "accounts/product_detail.html", {
        "product": product,
        "quantity_range": quantity_range,
    })


def add_to_cart(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get("quantity", 1))

        if product.stock == 0:
            return redirect("product_detail", product_id=product.id)

        if quantity > product.stock:
            quantity = product.stock

        cart = request.session.get("cart", {})

        if not isinstance(cart, dict):
            cart = {}

        product_id_str = str(product_id)
        if product_id_str in cart:
            cart[product_id_str] += quantity
        else:
            cart[product_id_str] = quantity

        request.session["cart"] = cart

        return redirect("cart")

    return redirect("product_search")


def cart_view(request):
    cart = request.session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        subtotal = product.price * quantity
        total_price += subtotal

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    return render(request, "accounts/cart.html", {
        "cart_items": cart_items,
        "total_price": total_price,
    })


def remove_from_cart(request, product_id):
    cart = request.session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    request.session["cart"] = cart
    return redirect("cart")


def update_cart(request, product_id):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        product_id_str = str(product_id)

        if not isinstance(cart, dict):
            cart = {}

        if product_id_str in cart:
            quantity = int(request.POST.get("quantity", 0))
            product = get_object_or_404(Product, id=product_id)

            if quantity <= 0:
                del cart[product_id_str]
                request.session["cart"] = cart
                return redirect("cart")

            if quantity > product.stock:
                cart_items = []
                total_price = 0

                for pid, qty in cart.items():
                    item_product = get_object_or_404(Product, id=pid)
                    subtotal = item_product.price * qty
                    total_price += subtotal

                    cart_items.append({
                        "product": item_product,
                        "quantity": qty,
                        "subtotal": subtotal,
                    })

                return render(request, "accounts/cart.html", {
                    "cart_items": cart_items,
                    "total_price": total_price,
                    "error": f"{product.name} の在庫が不足しています。在庫は {product.stock} 点です。",
                })

            cart[product_id_str] = quantity
            request.session["cart"] = cart

    return redirect("cart")

def order_confirm(request):
    if request.method != "POST":
        return redirect("cart")

    cart = request.session.get("cart", {})

    if not isinstance(cart, dict):
        cart = {}

    if not cart:
        return redirect("cart")

    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)

        if product.stock < quantity:
            for pid, qty in cart.items():
                item_product = get_object_or_404(Product, id=pid)
                subtotal = item_product.price * qty
                total_price += subtotal
                cart_items.append({
                    "product": item_product,
                    "quantity": qty,
                    "subtotal": subtotal,
                })

            return render(request, "accounts/cart.html", {
                "cart_items": cart_items,
                "total_price": total_price,
                "error": f"{product.name} の在庫が不足しています",
            })

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        product.stock -= quantity
        product.save()

    request.session["cart"] = {}

    return render(request, "accounts/order_complete.html")

from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    logout(request)
    return redirect('product_search')

from django.contrib.auth.decorators import login_required
from .forms import ProductForm


@staff_member_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("product_search")
    else:
        form = ProductForm()

    return render(request, "accounts/product_form.html", {
        "form": form,
        "page_title": "商品登録"
    })


@staff_member_required
def product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect("product_detail", product_id=product.id)
    else:
        form = ProductForm(instance=product)

    return render(request, "accounts/product_form.html", {
        "form": form,
        "page_title": "商品編集"
    })