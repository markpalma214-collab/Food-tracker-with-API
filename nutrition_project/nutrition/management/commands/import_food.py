from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from nutrition.models import FoodEntry
from nutrition.services.dietly import DietlyAPIError, DietlyNotConfigured, search_food


class Command(BaseCommand):
    help = "Look up a food in the nutrition API, print a readable label, and optionally save it to a user's log."

    def add_arguments(self, parser):
        parser.add_argument('query', type=str, help="Food name or barcode to search for")
        parser.add_argument('--limit', type=int, default=5, help="Max number of results to fetch")
        parser.add_argument('--user', type=str, default='admin', help="Username to attach the entry to")
        parser.add_argument('--quantity', type=int, default=1, help="Number of servings eaten")
        parser.add_argument('--save', action='store_true', help="Save the result as a FoodEntry")

    def handle(self, *args, **options):
        query = options['query']

        try:
            foods = search_food(query, limit=options['limit'])
        except DietlyNotConfigured as exc:
            raise CommandError(str(exc))
        except DietlyAPIError as exc:
            raise CommandError(str(exc))

        if not foods:
            self.stdout.write(self.style.WARNING(f"No match found for '{query}'."))
            return

        item = foods[0]
        self.print_label(item)

        if options['save']:
            self.save_entry(item, options['user'], options['quantity'])

    def print_label(self, item):
        name = item.get('name', 'Unknown food')
        brand = item.get('brand', '')
        rows = [
            ("Calories", item.get('calories_kcal', 0), "kcal"),
            ("Protein", item.get('protein_g', 0), "g"),
            ("Fat", item.get('fat_g', 0), "g"),
            ("Saturated Fat", item.get('saturated_fat_g', 0), "g"),
            ("Carbs", item.get('carbs_g', 0), "g"),
            ("Fiber", item.get('fiber_g', 0), "g"),
            ("Sugar", item.get('sugar_g', 0), "g"),
            ("Sodium", item.get('sodium_mg', 0), "mg"),
            ("Cholesterol", item.get('cholesterol_mg', 0), "mg"),
            ("Potassium", item.get('potassium_mg', 0), "mg"),
        ]

        width = 50
        self.stdout.write(self.style.HTTP_INFO("=" * width))
        self.stdout.write(self.style.HTTP_INFO(f" {name}  ({brand})".strip()))
        self.stdout.write(f" Serving: {item.get('serving_desc', 'N/A')}   Category: {item.get('category', 'N/A')}")
        self.stdout.write("-" * width)
        for label, value, unit in rows:
            self.stdout.write(f" {label:<15}: {value:>8.1f} {unit}")
        self.stdout.write(self.style.HTTP_INFO("=" * width))

    def save_entry(self, item, username, quantity):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist. Create it first or pass --user.")

        entry = FoodEntry.objects.create(
            user=user,
            food=item.get('name', 'Unknown food'),
            quantity=quantity,
            calories_kcal=item.get('calories_kcal', 0),
            protein_g=item.get('protein_g', 0),
            fat_g=item.get('fat_g', 0),
            saturated_fat_g=item.get('saturated_fat_g', 0),
            carbs_g=item.get('carbs_g', 0),
            fiber_g=item.get('fiber_g', 0),
            sugar_g=item.get('sugar_g', 0),
            sodium_mg=item.get('sodium_mg', 0),
            cholesterol_mg=item.get('cholesterol_mg', 0),
            potassium_mg=item.get('potassium_mg', 0),
            image_url=item.get('image_url'),
        )
        self.stdout.write(self.style.SUCCESS(f"Saved '{entry.food}' to {username}'s log (id={entry.pk})."))
