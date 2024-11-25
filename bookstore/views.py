# views.py
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book, Genre, Order, OrderItem, Stock
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages


def home(request):
    featured_books = Book.objects.select_related('stock').all()[:6]
    genres = Genre.objects.all()
    return render(request, 'bookstore/home.html', {
        'featured_books': featured_books,
        'genres': genres
    })


def book_list(request):
    genre_id = request.GET.get('genre')
    search_query = request.GET.get('search')

    books = Book.objects.select_related('stock')

    if genre_id:
        books = books.filter(genre_id=genre_id)
    if search_query:
        books = books.filter(title__icontains=search_query)

    genres = Genre.objects.all()
    return render(request, 'bookstore/book_list.html', {
        'books': books,
        'genres': genres,
        'current_genre': genre_id,
        'search_query': search_query
    })


def book_detail(request, book_id):
    book = get_object_or_404(Book.objects.select_related('stock'), id=book_id)
    related_books = Book.objects.filter(genre=book.genre).exclude(id=book_id)[:4]
    return render(request, 'bookstore/book_detail.html', {
        'book': book,
        'related_books': related_books
    })


def add_to_cart(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        quantity = int(request.POST.get('quantity', 1))

        # Check if the quantity is available in stock
        if quantity > book.stock.quantity_in_stock:
            messages.error(request, f'Only {book.stock.quantity_in_stock} items in stock.')
            return redirect('book_detail', book_id=book_id)

        # Add the book to the cart
        cart = request.session.get('cart', {})
        cart[str(book_id)] = cart.get(str(book_id), 0) + quantity
        request.session['cart'] = cart

        messages.success(request, f'Added {book.title} to your cart')
    return redirect('bookstore:book_detail', book_id=book_id)
def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')

    for book_id, quantity in cart.items():
        book = Book.objects.get(id=book_id)
        subtotal = book.price * quantity
        cart_items.append({
            'book': book,
            'quantity': quantity,
            'subtotal': subtotal
        })
        total += subtotal

    return render(request, 'bookstore/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('bookstore:home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'account/login.html')


def signup(request):
    if request.method == 'POST':
        # Handle user registration logic here
        pass  # Replace with actual sign-up logic
    return render(request, 'account/signup.html')


@login_required
def order_list(request):
    orders = Order.objects.filter(
        user__email=request.user.email
    ).order_by('-order_date')

    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'bookstore/orders/order_list.html', {
        'page_obj': page_obj
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('customer', 'payment')
        .prefetch_related('order_items__book'),
        id=order_id,
        customer__email=request.user.email
    )

    return render(request, 'bookstore/orders/order_detail.html', {
        'order': order
    })

