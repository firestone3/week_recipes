from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:recipe_id>/', views.detail, name='detail'),
    path('create/', views.create, name='create'),
    path('<int:recipe_id>/edit/', views.edit, name='edit'),
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/add/', views.add_ingredient, name='add_ingredient'),
    path('shopping-list/', views.shopping_list, name='shopping_list'),
    
    # レシピ作成の3ステップのURLパターン
    path('select-ingredients/', views.select_ingredients, name='select_ingredients'),
    path('search-recipes/', views.search_recipes, name='search_recipes'),
    path('recipe-suggestions/', views.recipe_suggestions, name='recipe_suggestions'),
    
    # 週間献立関連のURLパターン
    path('assign-recipes/', views.assign_recipes, name='assign_recipes'),
    path('save-weekly-menu/', views.save_weekly_menu, name='save_weekly_menu'),
    path('weekly-menu/', views.weekly_menu, name='weekly_menu'),
    
    # 買い物リスト関連のURLパターン
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('add-to-shopping-list/<int:recipe_id>/', views.add_to_shopping_list, name='add_to_shopping_list'),
    path('toggle-shopping-item/<int:item_id>/', views.toggle_shopping_item, name='toggle_shopping_item'),
    path('delete-shopping-item/<int:item_id>/', views.delete_shopping_item, name='delete_shopping_item'),
    path('check-missing-ingredients/<int:recipe_id>/', views.check_missing_ingredients, name='check_missing_ingredients'),
]