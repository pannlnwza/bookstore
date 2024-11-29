from django.contrib.auth.models import User
from bookstore.models import Transaction, Review, Favorite, Payment


def delete_user_data(name):
    try:
        # Fetch the user
        user = User.objects.get(username=name)

        # Delete related data manually if needed
        Transaction.objects.filter(user=user).delete()
        Review.objects.filter(user=user).delete()
        Favorite.objects.filter(user=user).delete()

        # Finally, delete the user
        user.delete()
        print(f"User {user.username} and all related data have been deleted.")
    except User.DoesNotExist:
        print("User not found.")

