from django.shortcuts import render, redirect
from django.contrib.auth.models import User

def login_view(request):
    return render(request, 'accounts/login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'accounts/signup.html', {
                'error': 'パスワードが一致しません'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/signup.html', {
                'error': 'このユーザー名はすでに使われています'
            })

        User.objects.create_user(username=username, password=password)
        return redirect('login')

    return render(request, 'accounts/signup.html')