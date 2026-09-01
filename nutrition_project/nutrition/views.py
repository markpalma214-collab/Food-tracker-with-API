from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import FoodEntryForm, FoodSearchForm, UserProfileForm
from .models import FoodEntry, UserProfile
from .services.dietly import DietlyAPIError, DietlyNotConfigured, get_first_match

# Nutrition fields returned by Dietly that get scaled by quantity and
# copied onto the FoodEntry. image_url is copied as-is (not scaled).
NUTRITION_FIELDS = [
    'calories_kcal', 'protein_g', 'fat_g', 'saturated_fat_g', 'carbs_g',
    'fiber_g', 'sugar_g', 'sodium_mg', 'cholesterol_mg', 'potassium_mg',
]

# Daily reference values used for the alert conditionals below.
SODIUM_LIMIT_MG = 2300
SUGAR_LIMIT_G = 50
CHOLESTEROL_LIMIT_MG = 300


# ---------- CRUD: FoodEntry ----------

@login_required
def food_list(request):
    entries = FoodEntry.objects.filter(user=request.user)
    return render(request, 'nutrition/food_list.html', {'entries': entries})


@login_required
def food_create(request):
    """
    The user only enters a food name + quantity. We look the food up on
    Dietly, take the first match, multiply its nutrition values by
    quantity, and save that as a FoodEntry owned by request.user.
    """
    if request.method == 'POST':
        form = FoodSearchForm(request.POST)
        if form.is_valid():
            food_name = form.cleaned_data['food']
            quantity = form.cleaned_data['quantity']

            try:
                item = get_first_match(food_name)
            except DietlyNotConfigured:
                messages.error(request, "Food lookup isn't configured yet — contact the site admin.")
                return render(request, 'nutrition/food_form.html', {'form': form, 'title': 'Add Food'})
            except DietlyAPIError:
                messages.error(request, f"Couldn't reach the food database looking up '{food_name}'. Please try again.")
                return render(request, 'nutrition/food_form.html', {'form': form, 'title': 'Add Food'})

            if not item:
                messages.warning(request, f"No match found for '{food_name}'. Try a different search term.")
                return render(request, 'nutrition/food_form.html', {'form': form, 'title': 'Add Food'})

            entry = FoodEntry(
                user=request.user,
                food=item.get('name', food_name),
                quantity=quantity,
                image_url=item.get('image_url'),
            )
            for field in NUTRITION_FIELDS:
                setattr(entry, field, item.get(field, 0) * quantity)
            entry.save()

            messages.success(request, f"Added {entry.food} to your log.")
            return redirect('food_list')
    else:
        form = FoodSearchForm()
    return render(request, 'nutrition/food_form.html', {'form': form, 'title': 'Add Food'})


@login_required
def food_update(request, pk):
    entry = get_object_or_404(FoodEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        form = FoodEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated {entry.food}.")
            return redirect('food_list')
    else:
        form = FoodEntryForm(instance=entry)
    return render(request, 'nutrition/food_form.html', {'form': form, 'title': 'Edit Food'})


@login_required
def food_delete(request, pk):
    entry = get_object_or_404(FoodEntry, pk=pk, user=request.user)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, f"Deleted {entry.food}.")
        return redirect('food_list')
    return render(request, 'nutrition/food_confirm_delete.html', {'entry': entry})


# ---------- Profile (height/weight -> daily calorie goal) ----------

@login_required
def profile_form(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'height_cm': 170, 'weight_kg': 65, 'age': 25, 'gender': 'M'},
    )
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('daily_history_today')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'nutrition/profile_form.html', {'form': form})


# ---------- Daily history / totals / alerts ----------

@login_required
def daily_history(request, date_str=None):
    if date_str:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.localdate()

    entries = FoodEntry.objects.filter(user=request.user, date__date=selected_date)

    totals = entries.aggregate(
        calories=Sum('calories_kcal'),
        protein=Sum('protein_g'),
        fat=Sum('fat_g'),
        saturated_fat=Sum('saturated_fat_g'),
        carbs=Sum('carbs_g'),
        fiber=Sum('fiber_g'),
        sugar=Sum('sugar_g'),
        sodium=Sum('sodium_mg'),
        cholesterol=Sum('cholesterol_mg'),
        potassium=Sum('potassium_mg'),
    )
    for key, value in totals.items():
        totals[key] = value or 0

    profile = UserProfile.objects.filter(user=request.user).first()
    goal_calories = profile.calculate_daily_calories() if profile else None

    alerts = []
    if goal_calories:
        if totals['calories'] >= goal_calories:
            alerts.append(('danger', f"You've reached your daily calorie goal "
                                      f"({totals['calories']:.0f}/{goal_calories:.0f} kcal)."))
        elif totals['calories'] >= goal_calories * 0.9:
            alerts.append(('warning', f"You're close to your daily calorie goal "
                                       f"({totals['calories']:.0f}/{goal_calories:.0f} kcal)."))
    else:
        alerts.append(('info', "Set up your profile to get a personalized calorie goal."))

    if totals['sodium'] > SODIUM_LIMIT_MG:
        alerts.append(('warning', f"Sodium intake ({totals['sodium']:.0f} mg) is over the "
                                   f"recommended {SODIUM_LIMIT_MG} mg/day."))
    if totals['sugar'] > SUGAR_LIMIT_G:
        alerts.append(('warning', f"Sugar intake ({totals['sugar']:.0f} g) is over the "
                                   f"recommended {SUGAR_LIMIT_G} g/day."))
    if totals['cholesterol'] > CHOLESTEROL_LIMIT_MG:
        alerts.append(('warning', f"Cholesterol intake ({totals['cholesterol']:.0f} mg) is over "
                                   f"the recommended {CHOLESTEROL_LIMIT_MG} mg/day."))

    context = {
        'entries': entries,
        'totals': totals,
        'selected_date': selected_date,
        'goal_calories': goal_calories,
        'alerts': alerts,
    }
    return render(request, 'nutrition/daily_history.html', context)
