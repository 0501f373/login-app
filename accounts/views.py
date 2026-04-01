from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')  # ログイン後の遷移先
        else:
            return render(request, 'accounts/login.html', {
                'error': 'ユーザー名またはパスワードが違います'
            })

    return render(request, 'accounts/login.html')