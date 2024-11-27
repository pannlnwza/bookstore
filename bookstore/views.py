from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Avg, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Book, Genre, Order, OrderItem, Stock, Cart, CartItem, Payment, Customer, Review, Favorite
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from bookstore.forms import SignUpForm, ReviewForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import generic
from django.db import IntegrityError



class HomeView(generic.TemplateView):
    template_name = 'bookstore/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_books'] = Book.objects.select_related('stock').all()[:10]
        context['top_books'] = Book.objects.select_related('genre').order_by('-sales_count')[:10]
        context['genre'] = Genre.objects.all()
        return context


def book_list(request):
    # Retrieve and validate query parameters
    selected_genres = request.GET.getlist('genres')  # Multi-select genres
    search_query = request.GET.get('search', '')  # Search term
    max_price = request.GET.get('max_price')  # Max price filter
    sort_by = request.GET.get('sort_by', 'popularity')  # Sorting option with default

    # Retrieve books with necessary related data
    books = Book.objects.select_related('genre').prefetch_related('stock')

    # Filter by genre
    if selected_genres:
        books = books.filter(genre__name__in=selected_genres)

    # Perform search for books matching the query
    if search_query:
        books = books.filter(title__icontains=search_query)

    # Filter by max price
    if max_price:
        try:
            max_price = float(max_price)
            books = books.filter(price__lte=max_price)
        except ValueError:
            pass  # Invalid price input, ignore filter

    # Apply sorting based on the selected option
    if sort_by == 'popularity':
        books = books.annotate(total_sales=Sum('order_items__quantity')).order_by('-total_sales')
    elif sort_by == 'rating':
        books = books.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'reviews':
        books = books.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'price_asc':
        books = books.order_by('price')
    elif sort_by == 'price_desc':
        books = books.order_by('-price')

    # Separate books into in-stock and out-of-stock
    in_stock_books = books.filter(stock__quantity_in_stock__gt=0)
    out_of_stock_books = books.filter(stock__quantity_in_stock=0)

    # Combine in-stock and out-of-stock books, ensuring in-stock appears first
    books = in_stock_books | out_of_stock_books

    # Retrieve all genres for filtering
    genres = Genre.objects.all()

    # Paginate the books
    paginator = Paginator(books, 12)  # 12 books per page
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)

    # Render the results with all necessary context
    return render(request, 'bookstore/book_list.html', {
        'page_obj': page_obj,
        'genres': genres,
        'selected_genres': selected_genres,
        'search_query': search_query,
        'max_price': max_price,
        'sort_by': sort_by,
    })


def book_detail(request, book_id):
    book = get_object_or_404(Book.objects.select_related('stock'), id=book_id)
    related_books = Book.objects.filter(genre=book.genre).exclude(id=book_id)[:4]
    reviews = book.reviews.select_related('customer').all()

    # Check if the user has purchased this book
    is_favorited = False
    user_has_purchased = False
    if request.user.is_authenticated:
        customer = Customer.objects.filter(user=request.user).first()
        if customer:
            user_has_purchased = OrderItem.objects.filter(order__customer=customer, book=book).exists()
            is_favorited = Favorite.objects.filter(user=request.user, book=book).exists()

    return render(request, 'bookstore/book_detail.html', {
        'book': book,
        'related_books': related_books,
        'reviews': reviews,
        'user_has_purchased': user_has_purchased,
        'is_favorited': is_favorited
    })


@login_required
def place_order(request):
    if request.method == 'POST':
        try:
            # Get user's cart and cart items
            cart = get_object_or_404(Cart, user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)

            if not cart_items.exists():
                messages.error(request, "Your cart is empty.")
                return redirect('bookstore:cart')

            # Validate stock availability
            for cart_item in cart_items:
                stock = Stock.objects.get(book=cart_item.book)
                if cart_item.quantity > stock.quantity_in_stock:
                    messages.error(request, f"Insufficient stock for {cart_item.book.title}.")
                    return redirect('bookstore:cart')

            # Collect form data
            full_name = request.POST.get('full_name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            payment_method = request.POST.get('payment_method')

            if not all([full_name, address, payment_method]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('bookstore:cart')

            customer = Customer.objects.create(
                user=request.user,
                first_name=full_name.split()[0],
                last_name=" ".join(full_name.split()[1:]),
                email=request.user.email,
                phone_number=phone,
            )


            with transaction.atomic():
                order = Order.objects.create(
                    customer=customer,
                    total_amount=cart.total,
                    address=address
                )

                # Create order items and update stock
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        book=cart_item.book,
                        quantity=cart_item.quantity,
                        price_at_time=cart_item.price_at_time
                    )

                    # Deduct stock
                    stock = Stock.objects.get(book=cart_item.book)
                    stock.quantity_in_stock -= cart_item.quantity
                    stock.save()

                # Create payment
                Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    amount=cart.total
                )

                # Clear the cart
                cart_items.delete()
                cart.delete()

            # Notify the user
            messages.success(request, f"Order #{order.id} placed successfully!")
            print(order.id)
            return redirect('bookstore:order_detail', order_id=order.id)

        except Cart.DoesNotExist:
            messages.error(request, "No active cart found.")
            return redirect('bookstore:cart')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('bookstore:cart')

    return redirect('bookstore:cart')

@login_required
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
            cart_item.price_at_time = book.price
            cart_item.save()

        messages.success(request, f'Added {book.title} to your cart')
    return redirect('bookstore:book_detail', book_id=book_id)

def update_quantity(request):
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')  # Get the cart item ID
        new_quantity = int(request.POST.get('quantity'))  # Get the new quantity

        cart_item = get_object_or_404(CartItem, id=cart_item_id)

        # Check if the quantity is valid and does not exceed available stock
        if new_quantity > cart_item.book.stock.quantity_in_stock:
            messages.error(request, f'Only {cart_item.book.stock.quantity_in_stock} items in stock.')
        else:
            cart_item.quantity = new_quantity

            # Optionally update the price_at_time if the price changes (if needed)
            cart_item.price_at_time = Decimal(cart_item.book.price)

            cart_item.save()
            messages.success(request, f'Updated quantity of {cart_item.book.title} to {new_quantity}.')

    return redirect('bookstore:cart')

def remove_cart(request, cart_item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=cart_item_id)
        cart_item.delete()
        messages.success(request, f'Removed')
    return redirect('bookstore:cart')


class ViewCart(generic.TemplateView, LoginRequiredMixin):
    template_name = 'bookstore/cart.html'

    def get_context_data(self, **kwargs):
        # Ensure the user is authenticated
        if self.request.user.is_authenticated:
            # Retrieve the user's cart
            cart = Cart.objects.filter(user=self.request.user).first()

            cart_items = []
            total = Decimal('0.00')

            if cart:
                # Loop through each cart item and accumulate the total
                for item in cart.cartitem_set.all():
                    cart_items.append({
                        'id': item.id,
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

class OrderListView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'bookstore/orders/order_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Annotate orders with item count
        orders = (
            Order.objects.filter(customer__user=self.request.user)
            .annotate(item_count=Count('order_items'))  # Annotate with count of OrderItems
            .order_by('-order_date')
        )

        # Return empty page if no orders
        if not orders.exists():
            context['page_obj'] = None
            return context

        # Filter by Order ID
        order_id = self.request.GET.get('order_id', '').strip()
        if order_id:
            orders = orders.filter(id=order_id)

        # Filter by Date Range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            orders = orders.filter(order_date__gte=start_date)

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            orders = orders.filter(order_date__lte=end_date)

        # Filter by number of items (min_items and max_items)
        min_items = self.request.GET.get('min_items')
        max_items = self.request.GET.get('max_items')

        if min_items:
            orders = orders.filter(item_count__gte=int(min_items))

        if max_items:
            orders = orders.filter(item_count__lte=int(max_items))

        # Handle pagination
        paginator = Paginator(orders, 5)  # Show 5 orders per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Pass context
        context['page_obj'] = page_obj

        # Add query string for pagination links
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_string'] = query_params.urlencode()

        return context



class OrderDetailView(LoginRequiredMixin, generic.TemplateView):
    model = Order
    template_name = 'bookstore/orders/order_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = context['order_id']
        order = get_object_or_404(Order, id=order_id)
        context['order'] = order
        return context


class StockManagementView(generic.TemplateView):
    template_name = 'bookstore/stock_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        books_list = Book.objects.all()

        search_query = self.request.GET.get('search', '')
        if search_query:
            books_list = books_list.filter(title__icontains=search_query)

        selected_genres = self.request.GET.getlist('genres')
        if selected_genres:
            books_list = books_list.filter(genre__name__in=selected_genres)

        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            books_list = books_list.filter(price__gte=float(min_price))
        if max_price:
            books_list = books_list.filter(price__lte=float(max_price))
        min_stock = self.request.GET.get('min_stock')
        max_stock = self.request.GET.get('max_stock')
        if min_stock:
            books_list = books_list.filter(stock__quantity_in_stock__gte=int(min_stock))
        if max_stock:
            books_list = books_list.filter(stock__quantity_in_stock__lte=int(max_stock))

        paginator = Paginator(books_list, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['genres'] = Genre.objects.all()
        context['search'] = search_query
        context['selected_genres'] = selected_genres
        context['min_price'] = min_price
        context['max_price'] = max_price
        context['min_stock'] = min_stock
        context['max_stock'] = max_stock
        context['page_obj'] = page_obj

        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You are not authorized to view this page.")
            return redirect('bookstore:home')
        return super().dispatch(request, *args, **kwargs)

class AddView(generic.TemplateView):
    template_name = 'bookstore/add_book.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You are not authorized to view this page.")
            return redirect('bookstore:home')
        return super().dispatch(request, *args, **kwargs)


@login_required
def add_book(request):
    if request.user.is_staff:
        if request.method == 'POST':
            title = request.POST.get('title')
            genre_id = request.POST.get('genre')
            price = request.POST.get('price')
            product_description = request.POST.get('product_description')
            universal_product_code = request.POST.get('universal_product_code')
            image_url = request.POST.get('image_url')
            image = request.FILES.get('image')

            genre = Genre.objects.get(id=genre_id)

            book = Book(
                title=title,
                genre=genre,
                price=price,
                product_description=product_description,
                universal_product_code=universal_product_code,
                image_url=image_url,
            )

            if image:
                book.image = image

            book.save()
            messages.success(request, f"Book {book.title} has been added successfully!")
            return redirect('bookstore:stock_management')

    messages.error(request, "You are not authorized to view this page.")
    return redirect('bookstore:home')

class EditBookView(generic.TemplateView):
    template_name = 'bookstore/edit_book.html'

    def get_context_data(self, **kwargs):
        book_id = self.kwargs.get('book_id')
        book = get_object_or_404(Book, id=book_id)
        genres = Genre.objects.all()  # Fetch all genres for the dropdown
        context = super().get_context_data(**kwargs)
        context['book'] = book
        context['genres'] = genres
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You are not authorized to view this page.")
            return redirect('bookstore:home')
        return super().dispatch(request, *args, **kwargs)


def edit_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if request.user.is_staff:
        if request.method == 'POST':
            # Get form data
            book.universal_product_code = request.POST.get('universal_product_code', book.universal_product_code)
            book.title = request.POST.get('title', book.title)
            book.price = request.POST.get('price', book.price)
            book.product_description = request.POST.get('product_description', book.product_description)
            book.genre_id = request.POST.get('genre', book.genre_id)

            # Handle file upload
            image = request.FILES.get('image')
            if image:
                book.image = image

            # Handle the image URL if provided
            image_url_from_form = request.POST.get('image_url')
            if image_url_from_form:
                book.image_url = image_url_from_form

            book.save()

            messages.success(request, f"Book '{book.title}' updated successfully.")
            return redirect('bookstore:stock_management')
    else:
        messages.error(request, "You are not authorized to do this action.")
        return redirect('bookstore:home')

@login_required
def delete_book(request, book_id):
    if request.user.is_staff:
        book = get_object_or_404(Book, id=book_id)
        book.delete()

        messages.success(request, f"Book '{book.title}' deleted successfully.")
        return redirect('bookstore:stock_management')

    messages.error(request, "You are not authorized to view this page.")
    return redirect('bookstore:home')


@login_required
def add_review(request, book_id):
    try:
        book = get_object_or_404(Book, id=book_id)

        # Validate that the user has purchased the book
        has_ordered_book = OrderItem.objects.filter(
            order__customer__user=request.user,
            book=book
        ).exists()

        if not has_ordered_book:
            messages.error(request, "You can only review books you have purchased.")
            return redirect('bookstore:book_detail', book_id=book_id)

        # Check if a review already exists
        existing_review = Review.objects.filter(
            customer__user=request.user,
            book=book
        ).first()

        if request.method == 'POST':
            form = ReviewForm(request.POST, instance=existing_review)  # Edit if exists
            if form.is_valid():
                review = form.save(commit=False)
                review.customer = Customer.objects.get(user=request.user)
                review.book = book
                review.save()
                messages.success(request, "Your review has been submitted.")
                return redirect('bookstore:book_detail', book_id=book_id)
            else:
                messages.error(request, "There was an error with your review. Please try again.")
        else:
            form = ReviewForm(instance=existing_review)  # Pre-fill if exists

    except IntegrityError as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('bookstore:book_detail', book_id=book_id)

    # Fallback render for form errors or GET requests
    return render(request, 'bookstore/book_detail.html', {
        'form': form,
        'book': book,
        'reviews': book.reviews.all(),
    })


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, customer__user=request.user)
    review.delete()
    messages.success(request, "Your review has been deleted.")
    return redirect('bookstore:book_detail', book_id=review.book.id)


def update_stock(request, book_id):
    if request.user.is_staff:
        if request.method == 'POST':
            book = get_object_or_404(Book, id=book_id)
            stock, create = Stock.objects.get_or_create(book=book)
            new_quantity = request.POST.get('quantity_in_stock')

            if new_quantity is not None:
                try:
                    stock.quantity_in_stock = int(new_quantity)
                    stock.save()
                    messages.success(request, f"Stock for {book.title} updated successfully!")
                except ValueError:
                    messages.error(request, "Invalid quantity. Please enter a valid number.")
            else:
                messages.error(request, "No quantity provided.")

            return redirect('bookstore:stock_management')

        return redirect('bookstore:stock_management')
    messages.error(request, "You are not authorized to view this page.")
    return redirect('bookstore:home')


class MyReviewsView(LoginRequiredMixin, generic.ListView):
    model = Review
    template_name = 'bookstore/my_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10  # Add pagination if needed

    def get_queryset(self):
        # Filter reviews for the logged-in user
        return Review.objects.filter(customer__user=self.request.user).select_related('book').order_by('-created_at')


@login_required
def add_to_favorites(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, book=book)

    if created:
        messages.success(request, f"'{book.title}' has been added to your favorites.")
    else:
        messages.info(request, f"'{book.title}' is already in your favorites.")

    return redirect('bookstore:book_detail', book_id=book_id)


@login_required
def remove_from_favorites(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    favorite = Favorite.objects.filter(user=request.user, book=book).first()

    if favorite:
        favorite.delete()
        messages.success(request, f"'{book.title}' has been removed from your favorites.")
    else:
        messages.info(request, f"'{book.title}' was not in your favorites.")

    return redirect('bookstore:book_detail', book_id=book_id)


class FavoritesListView(LoginRequiredMixin, generic.ListView):
    model = Favorite
    template_name = 'bookstore/favorites_list.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('book')

