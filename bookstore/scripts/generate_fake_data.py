import random
from faker import Faker
from django.contrib.auth.models import User
from bookstore.models import Order, OrderItem, Review, Favorite, Book, Payment

faker = Faker()

NUM_CUSTOMERS = 1000  # Total number of customers to generate
NUM_ORDERS = 6500     # Total number of orders to generate
NUM_REVIEWS = 5000   # Total number of reviews to generate
NUM_FAVORITES = 3000  # Total number of favorite relationships to generate
BATCH_SIZE = 100     # Number of records to insert in a single batch


def create_customers():
    print("Creating customers...")
    users = [
        User(
            username=faker.unique.user_name(),
            email=faker.email(),
            password="password123"
        )
        for _ in range(NUM_CUSTOMERS)
    ]
    User.objects.bulk_create(users, BATCH_SIZE)
    print(f"{NUM_CUSTOMERS} customers created.")


def create_orders():
    print("Creating orders...")
    customers = list(User.objects.all())
    books = list(Book.objects.all())
    orders = []
    order_items = []

    for _ in range(NUM_ORDERS):
        customer = random.choice(customers)
        order = Order(
            user=customer,
            total_amount=0,
            address=faker.address(),
            full_name=faker.name()
        )
        orders.append(order)
        if len(orders) >= BATCH_SIZE:
            Order.objects.bulk_create(orders)
            orders = []

    if orders:
        Order.objects.bulk_create(orders)

    print("Creating order items...")
    orders = list(Order.objects.all())
    for order in orders:
        selected_books = random.sample(books, random.randint(1, 5))
        total_amount = 0
        for book in selected_books:
            quantity = random.randint(1, 5)
            price_at_time = book.price
            total_amount += quantity * price_at_time
            order_items.append(OrderItem(
                order=order,
                book=book,
                quantity=quantity,
                price_at_time=price_at_time
            ))
        order.total_amount = total_amount

    Order.objects.bulk_update(orders, ['total_amount'])
    OrderItem.objects.bulk_create(order_items, BATCH_SIZE)
    print(f"{NUM_ORDERS} orders and their items created.")


def create_reviews(num_reviews):
    print("Creating reviews...")
    customers = list(User.objects.all())
    books = list(Book.objects.all())
    reviews = []
    existing_reviews = set()  # Track (user_id, book_id) to ensure uniqueness

    for _ in range(num_reviews):
        customer = random.choice(customers)
        book = random.choice(books)
        review_key = (customer.id, book.id)

        # Ensure this user-book combination does not already exist
        if review_key not in existing_reviews and not Review.objects.filter(user=customer, book=book).exists():
            existing_reviews.add(review_key)
            reviews.append(
                Review(user=customer, book=book, review_message=faker.text(max_nb_chars=200), rating=random.randint(1, 5))
            )

    if reviews:
        Review.objects.bulk_create(reviews, BATCH_SIZE)
        print(f"{len(reviews)} reviews created.")
    else:
        print("No reviews created. All user-book combinations already exist.")


def create_favorites():
    print("Creating favorites...")
    customers = list(User.objects.all())
    books = list(Book.objects.all())
    favorites = []

    for _ in range(NUM_FAVORITES):
        customer = random.choice(customers)
        book = random.choice(books)
        if not Favorite.objects.filter(user=customer, book=book).exists():
            favorites.append(Favorite(user=customer, book=book))
        if len(favorites) >= BATCH_SIZE:
            Favorite.objects.bulk_create(favorites)
            favorites = []

    if favorites:
        Favorite.objects.bulk_create(favorites)
    print(f"{NUM_FAVORITES} favorites created.")


def create_payments():
    print("Creating payments...")
    payments = [
        Payment(
            order=order,
            payment_method=random.choice(["Credit Card", "PayPal"]),
            amount=order.total_amount
        )
        for order in Order.objects.all()
    ]
    Payment.objects.bulk_create(payments, BATCH_SIZE)
    print("Payments created for all orders.")


def run():
    create_customers()
    create_orders()
    create_reviews(NUM_REVIEWS)
    create_favorites()
    create_payments()
    print("Large dataset generation completed!")
