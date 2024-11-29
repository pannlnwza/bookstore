import random
from faker import Faker
from django.contrib.auth.models import User
from bookstore.models import Stock, Transaction, TransactionItem, Review, Favorite, Payment, Book

faker = Faker()

NUM_CUSTOMERS = 1000  # Total number of customers to generate
NUM_TRANSACTIONS = 6500  # Total number of transactions to generate
NUM_REVIEWS = 5000    # Total number of reviews to generate
NUM_FAVORITES = 3000  # Total number of favorites to generate
BATCH_SIZE = 100      # Batch size for bulk create


def create_stocks():
    print("Creating stocks...")
    books = Book.objects.all()  # Fetch existing books
    stocks = [
        Stock(book=book, quantity_in_stock=random.randint(0, 500))
        for book in books
    ]
    Stock.objects.bulk_create(stocks, BATCH_SIZE)
    print(f"Stock created for {len(stocks)} books.")


def create_customers():
    print("Creating customers...")
    users = [
        User(
            username=faker.unique.user_name(),
            email=faker.email(),
            password="password123"  # Use hashed password in production
        )
        for _ in range(NUM_CUSTOMERS)
    ]
    User.objects.bulk_create(users, BATCH_SIZE)
    print(f"{NUM_CUSTOMERS} customers created.")


def create_transactions():
    print("Creating transactions and items...")
    users = list(User.objects.all())
    books = list(Book.objects.all())
    transactions = []
    transaction_items = []

    for _ in range(NUM_TRANSACTIONS):
        user = random.choice(users)
        transaction = Transaction(
            user=user,
            full_name=faker.name(),
            status=random.choice(["cart", "confirmed"]),
            address=faker.address(),
            phone=faker.phone_number()[:10]
        )
        transactions.append(transaction)

    Transaction.objects.bulk_create(transactions, BATCH_SIZE)

    transactions = list(Transaction.objects.all())
    for transaction in transactions:
        num_items = random.randint(1, 5)
        selected_books = random.sample(books, num_items)
        for book in selected_books:
            quantity = random.randint(1, 5)
            price_at_time = round(book.price, 2)
            transaction_items.append(TransactionItem(
                transaction=transaction,
                book=book,
                quantity=quantity,
                price_at_time=price_at_time
            ))

    TransactionItem.objects.bulk_create(transaction_items, BATCH_SIZE)
    print(f"{NUM_TRANSACTIONS} transactions and their items created.")


def create_reviews():
    print("Creating reviews...")
    users = list(User.objects.all())
    books = list(Book.objects.all())
    reviews = []
    existing_reviews = set(
        Review.objects.values_list("user_id", "book_id")
    )  # Fetch existing user-book pairs

    for _ in range(NUM_REVIEWS):
        user = random.choice(users)
        book = random.choice(books)
        review_key = (user.id, book.id)

        if review_key not in existing_reviews:  # Ensure uniqueness
            existing_reviews.add(review_key)
            reviews.append(
                Review(
                    user=user,
                    book=book,
                    review_message=faker.text(max_nb_chars=200),
                    rating=random.randint(1, 5),
                    name=user.username
                )
            )
            if len(reviews) >= BATCH_SIZE:
                Review.objects.bulk_create(reviews)
                reviews = []

    if reviews:
        Review.objects.bulk_create(reviews)
    print(f"{NUM_REVIEWS} reviews created (or as many unique pairs as possible).")


def create_favorites():
    print("Creating favorites...")
    users = list(User.objects.all())
    books = list(Book.objects.all())
    favorites = []
    existing_favorites = set(
        Favorite.objects.values_list("user_id", "book_id")
    )  # Fetch existing user-book pairs

    for _ in range(NUM_FAVORITES):
        user = random.choice(users)
        book = random.choice(books)
        favorite_key = (user.id, book.id)

        if favorite_key not in existing_favorites:  # Ensure uniqueness
            existing_favorites.add(favorite_key)
            favorites.append(Favorite(user=user, book=book))
            if len(favorites) >= BATCH_SIZE:
                Favorite.objects.bulk_create(favorites)
                favorites = []

    if favorites:
        Favorite.objects.bulk_create(favorites)
    print(f"{len(existing_favorites)} unique favorites created.")


def create_payments():
    print("Creating payments...")
    transactions = Transaction.objects.filter(status="confirmed")
    payments = [
        Payment(
            transaction=transaction,
            payment_method=random.choice(["Credit Card", "PayPal"]),
            amount=transaction.total
        )
        for transaction in transactions
    ]
    Payment.objects.bulk_create(payments, BATCH_SIZE)
    print(f"Payments created for {len(payments)} confirmed transactions.")


def run():
    create_stocks()
    create_customers()
    create_transactions()
    create_reviews()
    create_favorites()
    create_payments()
    print("Data generation completed successfully!")
