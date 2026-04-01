from django.urls import path
from .views import login_view

urlpatterns = [
    path('login/', login_view, name='login'),
]
from django.urls import path
from .views import login_view
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("ログイン成功！")

urlpatterns = [
    path('login/', login_view, name='login'),
    path('', home_view, name='home'),
]