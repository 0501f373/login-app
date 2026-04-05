import re

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login


def validate_password_policy(password):
    errors = []

    if len(password) < 8 or len(password) > 12:
        errors.append("パスワードは8〜12文字で入力してください")

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

        # username に email を入れているので authenticate は username=email でOK
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

        # 表示用ユーザー名チェック
        if not display_name:
            errors.append("ユーザー名を入力してください")

        # 前後の空白は trim 済み。中に空白が残る場合はバリデーション
        elif re.search(r"\s", display_name):
            errors.append("ユーザー名に空白は使用できません")

        # メールアドレスチェック
        if not email:
            errors.append("メールアドレスを入力してください")

        elif User.objects.filter(email__iexact=email).exists():
            errors.append("このメールアドレスはすでに登録されています")

        # パスワード一致チェック
        if not password:
            errors.append("パスワードを入力してください")

        if password != password_confirm:
            errors.append("パスワードが一致しません")

        # パスワードポリシー
        errors.extend(validate_password_policy(password))

        if errors:
            return render(request, "accounts/signup.html", {
                "errors": errors,
                "display_name": display_name,
                "email": email,
            })

        # username は内部用として email を保存
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=display_name,
        )

        login(request, user)
        return redirect("home")

    return render(request, "accounts/signup.html")