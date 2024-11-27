from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    product_page_url = models.URLField(blank=True, null=True)
    universal_product_code = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    product_description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    review_rating = models.CharField(max_length=50)
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

    def __str__(self):
        return self.title


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    full_name = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Payment for Order #{self.order.id}"


class Stock(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name="stock")
    quantity_in_stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Stock for {self.book.title}: {self.quantity_in_stock}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart {self.id} for {self.user.username}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.cartitem_set.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)

    @property
    def subtotal(self):
        return (self.price_at_time or 0) * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    review_message = models.TextField(max_length=1000)  # Increased length for detailed reviews
    rating = models.PositiveSmallIntegerField()  # Typically between 1 and 5
    created_at = models.DateTimeField(auto_now_add=True)

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
