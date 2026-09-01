from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Stores the values needed to calculate a user's daily calorie intake."""

    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Lightly active (1-3 days/week)'),
        ('moderate', 'Moderately active (3-5 days/week)'),
        ('active', 'Very active (6-7 days/week)'),
        ('extra', 'Extra active (physical job/training)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height_cm = models.FloatField(help_text="Height in centimeters")
    weight_kg = models.FloatField(help_text="Weight in kilograms")
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='sedentary')

    def calculate_bmr(self):
        """Mifflin-St Jeor Equation."""
        if self.gender == 'M':
            return (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) + 5
        return (10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) - 161

    def calculate_daily_calories(self):
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'extra': 1.9,
        }
        bmr = self.calculate_bmr()
        return round(bmr * multipliers.get(self.activity_level, 1.2), 2)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class FoodEntry(models.Model):
    """A logged food item. Nutrition fields are filled from the food API
    (see management command) or entered manually."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.CharField(max_length=200)
    quantity = models.IntegerField(help_text="Number of servings")
    date = models.DateTimeField(auto_now_add=True)

    calories_kcal = models.FloatField(default=0)
    protein_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)
    saturated_fat_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fiber_g = models.FloatField(default=0)
    sugar_g = models.FloatField(default=0)
    sodium_mg = models.FloatField(default=0)
    cholesterol_mg = models.FloatField(default=0)
    potassium_mg = models.FloatField(default=0)
    image_url = models.URLField(blank=True, null=True, help_text="Image URL returned by the food API")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.food} x{self.quantity} ({self.user.username})"
