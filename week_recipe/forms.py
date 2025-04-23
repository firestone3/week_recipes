from django import forms
from django.forms.widgets import TextInput, NumberInput, DateInput, Textarea
from .models import Ingredient

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'quantity', 'purchase_date', 'expiration_date', 'memo', 'storage_method']
        labels = {
            'name': '食材名',
            'quantity': '数量',
            'purchase_date': '購入日',
            'expiration_date': '賞味期限',
            'memo': 'メモ',
            'storage_method': '保存方法',
        }
        widgets = {
            'name': TextInput(attrs={'class': 'form-control', 'placeholder': '例: にんじん'}),
            'quantity': NumberInput(attrs={'class': 'form-control', 'placeholder': '例: 2'}),
            'purchase_date': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiration_date': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'memo': Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '例: 料理用'}),
            'storage_method': TextInput(attrs={'class': 'form-control', 'placeholder': '例: 冷蔵庫'}),
        }