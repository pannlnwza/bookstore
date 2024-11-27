import os
import json
from django.core.management.base import BaseCommand
from bookstore.models import Book, Genre, Stock
from django.conf import settings


class Command(BaseCommand):
    help = 'Imports JSON files from the json folder into the Book, Genre, and Stock models'

    def handle(self, *args, **kwargs):
        json_folder = os.path.join(settings.BASE_DIR, 'bookstore', 'data', 'json')

        for filename in os.listdir(json_folder):
            if filename.endswith('.json'):
                file_path = os.path.join(json_folder, filename)
                self.import_json_file(file_path)

    def import_json_file(self, file_path):
        conversion_rate = 43.53  # GBP to THB exchange rate

        with open(file_path, 'r') as f:
            data = json.load(f)

        for item in data:
            category, created = Genre.objects.get_or_create(name=item.get('category'))

            price_including_tax = item.get('price_including_tax')
            if price_including_tax:
                price_including_tax_gbp = float(price_including_tax.replace('£', '').strip())
                price_including_tax_thb = round(price_including_tax_gbp * conversion_rate)
            else:
                price_including_tax_thb = 0.0

            book = Book.objects.create(
                product_page_url=item.get('product_page_url'),
                universal_product_code=item.get('universal_product_code'),
                title=item.get('title'),
                price=price_including_tax_thb,
                product_description=item.get('product_description'),
                genre=category,
                review_rating=item.get('review_rating'),
                image_url=item.get('image_url'),
            )

            Stock.objects.create(
                book=book,
                quantity_in_stock=int(item.get('number_available', 0)),
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully imported data from {file_path}'))
