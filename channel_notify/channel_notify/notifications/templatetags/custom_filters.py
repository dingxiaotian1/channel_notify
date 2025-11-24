from django import template

register = template.Library()

@register.filter(name='any_starts_with')
def any_starts_with(items, prefix):
    """
    检查列表中是否有任何项目以指定前缀开头
    """
    if not items:
        return False
    return any(item.startswith(prefix) for item in items)
