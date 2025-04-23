from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import Ingredient, Recipe, WeeklyMenu, ShoppingItem
from .forms import IngredientForm
import requests
import json
import datetime
from django.conf import settings
import urllib.parse
from django.contrib import messages

def index(request):
    return render(request, 'week_recipe/index.html')

def detail(request, recipe_id):
    return render(request, 'week_recipe/detail.html', {'recipe_id': recipe_id})

def create(request):
    return render(request, 'week_recipe/create.html')

def edit(request, recipe_id):
    return render(request, 'week_recipe/edit.html', {'recipe_id': recipe_id})

def ingredient_list(request):
    ingredients = Ingredient.objects.all()
    return render(request, 'week_recipe/ingredient_list.html', {'ingredients': ingredients})

def add_ingredient(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ingredient_list')
    else:
        form = IngredientForm()
    return render(request, 'week_recipe/add_ingredient.html', {'form': form})

def shopping_list(request):
    """買い物リストを表示する画面"""
    # 買い物リストの取得
    shopping_items = ShoppingItem.objects.all().order_by('-added_at')
    
    # 購入済みと未購入でフィルタリング
    unpurchased_items = shopping_items.filter(is_purchased=False)
    purchased_items = shopping_items.filter(is_purchased=True)
    
    return render(request, 'week_recipe/shopping_list.html', {
        'unpurchased_items': unpurchased_items,
        'purchased_items': purchased_items
    })

def add_to_shopping_list(request, recipe_id):
    """レシピから不足している食材を買い物リストに追加"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    if request.method == 'POST':
        # 選択された食材を取得
        selected_items = request.POST.getlist('ingredients')
        
        # 選択された食材を買い物リストに追加
        items_added = 0
        for item_text in selected_items:
            # カンマやカッコなどがあれば取り除く簡単な正規化
            item_parts = item_text.split(' ', 1)
            name = item_parts[0]
            quantity = item_parts[1] if len(item_parts) > 1 else '適量'
            
            # 既存の同じ名前の買い物リストアイテムを確認
            existing_item = ShoppingItem.objects.filter(name=name, is_purchased=False).first()
            
            if existing_item:
                # 既存のアイテムがあれば、数量を更新
                existing_item.quantity = quantity
                existing_item.save()
            else:
                # 新規作成
                ShoppingItem.objects.create(
                    name=name,
                    quantity=quantity,
                    recipe=recipe
                )
            items_added += 1
        
        messages.success(request, f'{items_added}個の食材を買い物リストに追加しました')
        return redirect('recipe_detail', recipe_id=recipe.id)
    
    # レシピの材料を解析
    ingredients = []
    if recipe.ingredients:
        # カンマ区切りの場合
        if ',' in recipe.ingredients:
            ingredients = recipe.ingredients.split(',')
        else:
            # 改行区切りの場合
            ingredients = recipe.ingredients.splitlines()
    
    # 冷蔵庫に既にある食材を取得
    available_ingredients = Ingredient.objects.all()
    available_names = [ingredient.name for ingredient in available_ingredients]
    
    # 足りない材料を特定
    missing_ingredients = []
    for ingredient in ingredients:
        ingredient = ingredient.strip()
        if ingredient:
            # 部分一致で冷蔵庫にあるか確認
            is_available = False
            for avail_name in available_names:
                if avail_name in ingredient:
                    is_available = True
                    break
            
            if not is_available:
                missing_ingredients.append(ingredient)
    
    return render(request, 'week_recipe/add_to_shopping_list.html', {
        'recipe': recipe,
        'missing_ingredients': missing_ingredients
    })

def toggle_shopping_item(request, item_id):
    """買い物リストの項目の購入状態を切り替え"""
    item = get_object_or_404(ShoppingItem, id=item_id)
    item.is_purchased = not item.is_purchased
    item.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'is_purchased': item.is_purchased})
    
    return redirect('shopping_list')

def delete_shopping_item(request, item_id):
    """買い物リストの項目を削除"""
    item = get_object_or_404(ShoppingItem, id=item_id)
    item.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, '買い物リストから削除しました')
    return redirect('shopping_list')

def check_missing_ingredients(request, recipe_id):
    """レシピに不足している食材をチェック"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    # レシピの材料を解析
    ingredients = []
    if recipe.ingredients:
        # カンマ区切りの場合
        if ',' in recipe.ingredients:
            ingredients = recipe.ingredients.split(',')
        else:
            # 改行区切りの場合
            ingredients = recipe.ingredients.splitlines()
    
    # 冷蔵庫に既にある食材を取得
    available_ingredients = Ingredient.objects.all()
    available_names = [ingredient.name for ingredient in available_ingredients]
    
    # 足りない材料を特定
    missing_ingredients = []
    for ingredient in ingredients:
        ingredient = ingredient.strip()
        if ingredient:
            # 部分一致で冷蔵庫にあるか確認
            is_available = False
            for avail_name in available_names:
                if avail_name in ingredient:
                    is_available = True
                    break
            
            if not is_available:
                missing_ingredients.append(ingredient)
    
    return JsonResponse({
        'missing_count': len(missing_ingredients),
        'missing_ingredients': missing_ingredients
    })

def select_ingredients(request):
    """使用する食材を選択する画面"""
    ingredients = Ingredient.objects.all()
    if request.method == 'POST':
        selected_ingredients = request.POST.getlist('ingredients')
        if selected_ingredients:
            # 選択された食材をセッションに保存
            request.session['selected_ingredients'] = selected_ingredients
            return redirect('search_recipes')
    return render(request, 'week_recipe/select_ingredients.html', {'ingredients': ingredients})

def search_recipes(request):
    """楽天レシピAPIを使用してレシピを検索"""
    selected_ingredients = request.session.get('selected_ingredients', [])
    
    if not selected_ingredients:
        return redirect('select_ingredients')
    
    # 選択された食材の名前を取得
    ingredient_names = []
    for ingredient_id in selected_ingredients:
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
            ingredient_names.append(ingredient.name)
        except Ingredient.DoesNotExist:
            pass
    
    # 楽天レシピAPIを使った検索
    if ingredient_names:
        recipes = search_rakuten_recipes(ingredient_names)
        request.session['recipe_results'] = recipes
        return redirect('recipe_suggestions')
    
    return render(request, 'week_recipe/search_recipes.html', {
        'selected_ingredients': selected_ingredients,
        'ingredient_names': ingredient_names
    })

def recipe_suggestions(request):
    """検索結果のレシピを提案"""
    recipes = request.session.get('recipe_results', [])
    selected_ingredients = request.session.get('selected_ingredients', [])
    
    # 選択された食材の名前を取得
    ingredient_names = []
    for ingredient_id in selected_ingredients:
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
            ingredient_names.append(ingredient.name)
        except Ingredient.DoesNotExist:
            pass
    
    return render(request, 'week_recipe/recipe_suggestions.html', {
        'recipes': recipes,
        'ingredient_names': ingredient_names
    })

def search_rakuten_recipes(ingredients):
    """楽天レシピAPIを使用して検索する"""
    # 本番環境ではsettingsから取得するが、開発環境では仮のキー
    api_key = getattr(settings, 'RAKUTEN_API_KEY', 'YOUR_API_KEY')
    
    # 食材名をカンマ区切りの文字列に変換
    ingredient_query = ' '.join(ingredients)
    
    # 楽天レシピAPIのエンドポイント
    url = 'https://app.rakuten.co.jp/services/api/Recipe/CategoryRanking/20170426'
    
    params = {
        'applicationId': api_key,
        'categoryId': '10',  # カテゴリID（必要に応じて変更）
        'keyword': ingredient_query,
        'format': 'json'
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('result', [])
        else:
            return []
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return []

def assign_recipes(request):
    """曜日ごとにレシピを割り当てる画面"""
    weekdays = [
        (0, '月曜日'),
        (1, '火曜日'),
        (2, '水曜日'),
        (3, '木曜日'),
        (4, '金曜日'),
        (5, '土曜日'),
        (6, '日曜日'),
    ]
    
    # 現在の週の月曜日を計算
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    
    return render(request, 'week_recipe/assign_recipes.html', {
        'weekdays': weekdays,
        'monday': monday,
    })

def save_weekly_menu(request):
    """週間献立を保存する処理"""
    if request.method == 'POST':
        recipes_data = json.loads(request.POST.get('recipes_data', '{}'))
        
        if not recipes_data:
            return redirect('assign_recipes')
        
        # 現在の週の月曜日を計算
        today = datetime.date.today()
        monday = today - datetime.timedelta(days=today.weekday())
        
        # 各曜日のレシピを保存
        for day_num, recipe_data in recipes_data.items():
            # DBに既にレシピが存在するか確認
            try:
                recipe = Recipe.objects.get(recipe_id=recipe_data['recipeId'])
            except Recipe.DoesNotExist:
                # レシピがなければ新規作成
                recipe = Recipe(
                    recipe_id=recipe_data['recipeId'],
                    title=recipe_data['title'],
                    image_url=recipe_data.get('imageUrl', ''),
                    recipe_url=recipe_data['recipeUrl'],
                    ingredients=recipe_data.get('ingredients', ''),
                )
                recipe.save()
            
            # 週間献立に追加（既存のものがあれば更新）
            WeeklyMenu.objects.update_or_create(
                week_of=monday,
                weekday=int(day_num),
                defaults={'recipe': recipe}
            )
        
        return redirect('weekly_menu')
    
    return redirect('assign_recipes')

def weekly_menu(request):
    """週間献立表を表示する画面"""
    # 現在の週の月曜日を計算
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    
    # 週間メニューを取得
    weekly_menus = WeeklyMenu.objects.filter(week_of=monday).order_by('weekday')
    
    # 曜日ごとのメニューを整理
    weekdays = [
        {'day_num': 0, 'name': '月曜日', 'date': monday},
        {'day_num': 1, 'name': '火曜日', 'date': monday + datetime.timedelta(days=1)},
        {'day_num': 2, 'name': '水曜日', 'date': monday + datetime.timedelta(days=2)},
        {'day_num': 3, 'name': '木曜日', 'date': monday + datetime.timedelta(days=3)},
        {'day_num': 4, 'name': '金曜日', 'date': monday + datetime.timedelta(days=4)},
        {'day_num': 5, 'name': '土曜日', 'date': monday + datetime.timedelta(days=5)},
        {'day_num': 6, 'name': '日曜日', 'date': monday + datetime.timedelta(days=6)},
    ]
    
    # 各曜日にレシピを割り当て
    for menu in weekly_menus:
        weekdays[menu.weekday]['recipe'] = menu.recipe
        weekdays[menu.weekday]['menu_id'] = menu.id
    
    return render(request, 'week_recipe/weekly_menu.html', {
        'weekdays': weekdays,
        'week_of': monday,
    })

def recipe_detail(request, recipe_id):
    """レシピの詳細を表示する"""
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return render(request, 'week_recipe/recipe_detail.html', {'recipe': recipe})
