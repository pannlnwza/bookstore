from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Book, Category, Order, OrderItem, Stock, Cart, CartItem
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from bookstore.forms import SignUpForm
from django.core.paginator import Paginator
from django.views import generic

def home(request):
    featured_books = Book.objects.select_related('stock').all()[:6]
    category = Category.objects.all()
    return render(request, 'bookstore/home.html', {
        'featured_books': featured_books,
        'category': category
    })


def book_list(request):
    genre_id = request.GET.get('genre')
    search_query = request.GET.get('search')
    books = Book.objects.select_related('stock')
    if genre_id:
        books = books.filter(genre_id=genre_id)
    if search_query:
        books = books.filter(title__icontains=search_query)
    category = Category.objects.all()
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'bookstore/book_list.html', {
        'page_obj': page_obj,
        'categories': category,
        'current_genre': genre_id,
        'search_query': search_query
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

        if quantity > book.stock.quantity_in_stock:
            messages.error(request, f'Only {book.stock.quantity_in_stock} items in stock.')
            return redirect('bookstore:book_detail', book_id=book_id)

        # Get the user's cart, or create one if it doesn't exist
        cart, created = Cart.objects.get_or_create(user=request.user)

        # Try to get the cart item or create it if it doesn't exist
        cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)

        # If the item already exists in the cart, update the quantity
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            # Set the price_at_time field when the item is first added
            cart_item.price_at_time = Decimal(book.price_including_tax.replace('£', '').strip())
            cart_item.save()

        messages.success(request, f'Added {book.title} to your cart')
    return redirect('bookstore:book_detail', book_id=book_id)

def update_quantity(request):
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        new_quantity = int(request.POST.get('quantity'))

        # Fetch the cart item
        cart_item = get_object_or_404(CartItem, id=cart_item_id)

        # Check if the quantity is valid and does not exceed available stock
        if new_quantity > cart_item.book.stock.quantity_in_stock:
            messages.error(request, f'Only {cart_item.book.stock.quantity_in_stock} items in stock.')
        else:
            cart_item.quantity = new_quantity

            # Optionally update the price_at_time if the price changes (if needed)
            cart_item.price_at_time = Decimal(cart_item.book.price_including_tax.replace('£', '').strip())

            cart_item.save()
            messages.success(request, f'Updated quantity of {cart_item.book.title} to {new_quantity}.')

    return redirect('bookstore:view_cart')

class ViewCart(generic.TemplateView, LoginRequiredMixin):
    template_name = 'bookstore/cart.html'

    def get_context_data(self, **kwargs):
        cart = Cart.objects.filter(user=self.request.user).first()

        cart_items = []
        total = Decimal('0.00')

        if cart:
            for item in cart.items.all():
                cart_items.append({
                    'book': item.book,
                    'quantity': item.quantity,
                    'subtotal': item.subtotal
                })
                total += item.subtotal

        context = super().get_context_data(**kwargs)
        context['cart_items'] = cart_items
        context['total'] = total
        return context
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  # Logs the user in
            return redirect('bookstore:home')  # Redirect to home or another page
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'account/login.html')


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Hash the password
            user.save()
            auth_login(request, user)  # Log the user in
            return redirect('bookstore:home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, 'account/signup.html', {'form': form})

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

