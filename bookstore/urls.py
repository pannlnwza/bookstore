from django.urls import path

from . import views

app_name = 'bookstore'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('books/', views.book_list, name='book_list'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('cart/', views.ViewCart.as_view(), name='cart'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('add_to_cart/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('update_quantity/', views.update_quantity, name='update_quantity'),
    path('remove_cart/<int:cart_item_id>', views.remove_cart, name='remove_cart'),
    path('checkout/', views.place_order, name='proceed_to_payment'),
    path('stock/', views.StockManagementView.as_view(), name='stock_management'),
    path('add/', views.add_book, name='add_book'),
    path('edit-book/<int:book_id>/', views.EditBookView.as_view(), name='edit_book'),
    path('edit/<int:book_id>/', views.edit_book, name='edit'),
    path('delete-book/<int:book_id>/', views.delete_book, name='delete_book'),
    path('add-book/', views.AddView.as_view(), name='add'),
    path('update-stock/<int:book_id>/', views.update_stock, name='update_stock')

]
