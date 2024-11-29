from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    universal_product_code = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    product_description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='book_images/', blank=True, null=True)
    sales_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["-sales_count"]),
        ]
    def get_image_url(self):
        """
        Returns the uploaded image URL if available; otherwise, returns the image_url.
        """
        if self.image:
            return self.image.url
        return self.image_url

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return None

    def get_sale_count(self):
        return self.transaction_items.count()

    def __str__(self):
        return self.title


class Stock(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name="stock")
    quantity_in_stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Stock for {self.book.title}: {self.quantity_in_stock}"


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("cart", "Cart"),
        ("confirmed", "Confirmed Order"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="cart")
    address = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_cart(self):
        return self.status == "CART"

    @property
    def total(self):
        return sum(item.subtotal for item in self.transaction_items.all())

    def __str__(self):
        return f"Transaction {self.id} - {self.get_status_display()} for {self.user.username}"


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="transaction_items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="transaction_items")
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)

    @property
    def subtotal(self):
        return (self.price_at_time or 0) * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.book.title} in Transaction {self.transaction.id}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal'),
    ]

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="payment")
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment for Order #{self.transaction.id}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    review_message = models.TextField(max_length=1000)  # Increased length for detailed reviews
    rating = models.PositiveSmallIntegerField()  # Typically between 1 and 5
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=50)

    class Meta:
        unique_together = ('user', 'book')  # Ensures one review per user per book
        ordering = ['-created_at']  # Newest reviews appear first

    def clean(self):
        if not (1 <= self.rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")

    def __str__(self):
        return f"Review by {self.user.username} on {self.book.title}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="favorited_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')  # Ensure a user can only favorite a book once

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
