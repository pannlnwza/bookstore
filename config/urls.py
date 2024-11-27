from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from bookstore import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('bookstore.urls')),
    path('account/signup/', views.signup, name='signup'),
    path('account/login/', views.login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='bookstore:home'), name='account_logout'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)