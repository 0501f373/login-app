import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse

from .models import Product


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
            return redirect("home")

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

    products = Product.objects.all()

    if keyword:
        products = products.filter(name__icontains=keyword)

    if category:
        products = products.filter(category__icontains=category)

    return render(request, "accounts/product_search.html", {
        "keyword": keyword,
        "category": category,
        "products": products,
    })

from django.shortcuts import get_object_or_404

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, "accounts/product_detail.html", {
        "product": product,
    })