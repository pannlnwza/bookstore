
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book, Category, Order, OrderItem, Stock
from decimal import Decimal
from django.core.paginator import Paginator


def home(request):
    featured_books = Book.objects.select_related('stock').all()[:6]
    category = Category.objects.all()
    return render(request, 'bookstore/home.html', {
        'featured_books': featured_books,
        'category': category
    })


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def book_list(request):
    # Retrieve and validate query parameters
    genre_id = request.GET.get('genre')
    search_query = request.GET.get('search',
                                   '')  # Default to '' if not provided
    books = Book.objects.select_related('stock')

    # Validate genre_id to ensure it is numeric
    if genre_id and genre_id.isdigit():
        books = books.filter(category_id=int(genre_id))

    # Perform a default search for all books when entering the page for the first time
    books = books.filter(title__icontains=search_query)

    # Get all categories for filtering
    categories = Category.objects.all()
    paginator = Paginator(books, 12)

    # Get the current page number from the request
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        # If the page is not an integer, show the first page
        page_obj = paginator.get_page(1)
    except EmptyPage:
        # If the page is out of range, show the last page
        page_obj = paginator.get_page(paginator.num_pages)

    # Render the results with all necessary context
    return render(request, 'bookstore/book_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'current_genre': genre_id,
        'search_query': search_query,
        # Pass the search query for potential UI display
    })


def book_detail(request, book_id):
    book = get_object_or_404(Book.objects.select_related('stock'), id=book_id)
    related_books = Book.objects.filter(category=book.category).exclude(id=book_id)[:4]
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