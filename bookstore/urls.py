from django.urls import path
from . import views

app_name = 'bookstore'

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('cart/', views.ViewCart.as_view(), name='cart'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('add_to_cart/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_quantity/', views.update_quantity, name='update_quantity'),
    path('remove_cart/<int:cart_item_id>', views.remove_cart, name='remove_cart')

]