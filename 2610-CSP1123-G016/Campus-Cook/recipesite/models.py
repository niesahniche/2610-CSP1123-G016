from django.db import models

class Recipe(models.Model):

    CATEGORY_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('dessert', 'Dessert'),
    ]

    APPLIANCE_CHOICES = [
        ('none', 'No Appliance Needed'),
        ('microwave', 'Microwave'),
        ('oven', 'Oven'),
        ('stove', 'Stove'),
        ('airfryer', 'Air Fryer'),
        ('blender', 'Blender'),
    ]

    BUDGET_CHOICES = [
        ('low', 'Budget Friendly (Below RM5)'),
        ('medium', 'Moderate (RM5 - RM15)'),
        ('high', 'Splurge (Above RM15)'),
    ]

    title        = models.CharField(max_length=200)
    description  = models.TextField()
    ingredients  = models.TextField()
    instructions = models.TextField()
    category     = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='lunch')
    appliance    = models.CharField(max_length=50, choices=APPLIANCE_CHOICES, default='stove')
    budget       = models.CharField(max_length=50, choices=BUDGET_CHOICES, default='low')
    price        = models.DecimalField(max_digits=5, decimal_places=2)
    time_minutes = models.IntegerField(help_text="Cooking time in minutes")
    is_halal     = models.BooleanField(default=True)
    image        = models.ImageField(upload_to='recipes/', blank=True, null=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title