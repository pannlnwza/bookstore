import random
from faker import Faker
from django.contrib.auth.models import User
from bookstore.models import Customer, Order, OrderItem, Stock, Review, Favorite, Book, Payment

faker = Faker()


def create_customers(num=20):
    print("Creating customers...")
    customers = []
    for _ in range(num):
        user = User.objects.create_user(
            username=faker.unique.user_name(),
            email=faker.email(),
            password="password123"
        )
        customer = Customer(
            user=user,
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            email=user.email,
            phone_number=faker.phone_number(),
        )
        customers.append(customer)
    Customer.objects.bulk_create(customers)
    print(f"{num} customers created.")


def create_orders(num=30):
    print("Creating orders...")
    orders = []
    customers = Customer.objects.all()
    for _ in range(num):
        customer = random.choice(customers)
        order = Order(
            customer=customer,
            total_amount=0,  # Will calculate later
            address=faker.address()
        )
        orders.append(order)
    orders = Order.objects.bulk_create(orders)

    print("Creating order items...")
    order_items = []
    for order in orders:
        books = random.sample(list(Book.objects.all()), random.randint(1, 5))
        total_amount = 0
        for book in books:
            quantity = random.randint(1, 5)
            price_at_time = book.price
            total_amount += quantity * price_at_time
            order_items.append(OrderItem(
                order=order,
                book=book,
                quantity=quantity,
                price_at_time=price_at_time,
            ))
        order.total_amount = total_amount
        order.save()
    OrderItem.objects.bulk_create(order_items)
    print(f"{num} orders and their items created.")


def create_reviews(num=50):
    print("Creating reviews...")
    reviews = []
    customers = Customer.objects.all()
    for _ in range(num):
        customer = random.choice(customers)
        book = random.choice(Book.objects.all())
        review = Review(
            customer=customer,
            book=book,
            review_message=faker.text(max_nb_chars=200),
            rating=random.randint(1, 5),
        )
        reviews.append(review)
    Review.objects.bulk_create(reviews)
    print(f"{num} reviews created.")

def create_favorites(num=50):
    print("Creating favorites...")
    favorites = []
    users = User.objects.all()
    for _ in range(num):
        user = random.choice(users)
        book = random.choice(Book.objects.all())
        if not Favorite.objects.filter(user=user, book=book).exists():
            favorite = Favorite(
                user=user,
                book=book,
            )
            favorites.append(favorite)
    Favorite.objects.bulk_create(favorites)
    print(f"{num} favorites created.")

def create_payments():
    print("Creating payments...")
    payments = []
    for order in Order.objects.all():
        payment = Payment(
            order=order,
            payment_method=random.choice(["Credit Card", "PayPal"]),
            amount=order.total_amount,
        )
        payments.append(payment)
    Payment.objects.bulk_create(payments)
    print("Payments created for all orders.")

def run():
    create_customers()
    create_orders()
    create_reviews()
    create_favorites()
    create_payments()
    print("Fake data generation completed!")
