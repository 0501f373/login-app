from django.urls import path
from .views import login_view, signup_view
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("ログイン成功！")

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('home/', home_view, name='home'),
]