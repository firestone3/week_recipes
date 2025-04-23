from django.db import models

class Ingredient(models.Model):
    STORAGE_CHOICES = [
        ('冷蔵', '冷蔵'),
        ('冷凍', '冷凍'),
        ('常温', '常温'),
    ]

    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)
    purchase_date = models.DateField()
    expiration_date = models.DateField()
    memo = models.TextField(blank=True, null=True)
    storage_method = models.CharField(max_length=10, choices=STORAGE_CHOICES)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    """楽天レシピAPIから取得したレシピ情報を保存するモデル"""
    recipe_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    image_url = models.URLField(blank=True, null=True)
    recipe_url = models.URLField()
    ingredients = models.TextField()  # JSONとして材料を保存
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class WeeklyMenu(models.Model):
    """曜日ごとのレシピを管理するモデル"""
    WEEKDAY_CHOICES = [
        (0, '月曜日'),
        (1, '火曜日'),
        (2, '水曜日'),
        (3, '木曜日'),
        (4, '金曜日'),
        (5, '土曜日'),
        (6, '日曜日'),
    ]
    
    week_of = models.DateField(help_text="この週の開始日（月曜日）")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='weekly_menus')
    memo = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['week_of', 'weekday']
        ordering = ['week_of', 'weekday']

    def __str__(self):
        return f"{self.get_weekday_display()} - {self.recipe.title}"

class ShoppingItem(models.Model):
    """買い物リストの項目を管理するモデル"""
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50)
    is_purchased = models.BooleanField(default=False)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True, related_name='shopping_items')
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.quantity})"
