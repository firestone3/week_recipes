from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    """
    Adds a CSS class to a form field widget while preserving other attributes.
    """
    if hasattr(value, 'as_widget'):
        # 既存の属性を取得
        attrs = {}
        if hasattr(value.field.widget, 'attrs'):
            attrs = value.field.widget.attrs.copy()
        
        # 既存のクラスがあれば保持し、新しいクラスを追加
        if 'class' in attrs:
            attrs['class'] = f"{attrs['class']} {css_class}"
        else:
            attrs['class'] = css_class
            
        return value.as_widget(attrs=attrs)
    return value