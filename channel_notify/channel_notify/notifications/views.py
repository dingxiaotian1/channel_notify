from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification


def index(request):
    """首页视图，根据用户组显示相应的界面"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # 获取用户所属的组
    user_groups = request.user.groups.all()
    group_names = [group.name for group in user_groups]
    
    context = {
        'user': request.user,
        'groups': group_names,
    }
    
    return render(request, 'notifications/index.html', context)


def user_login(request):
    """用户登录视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        
        if user:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'notifications/login.html', {'error': '用户名或密码错误'})
    
    return render(request, 'notifications/login.html')


def user_logout(request):
    """用户注销视图"""
    logout(request)
    return redirect('login')


def create_groups(request):
    """创建运营和财务组（仅用于演示）"""
    # 创建运营组
    operations_group, created_ops = Group.objects.get_or_create(name='operations')
    # 创建财务组
    finance_group, created_finance = Group.objects.get_or_create(name='finance')
    
    return JsonResponse({
        'operations_created': created_ops,
        'finance_created': created_finance
    })


def create_users(request):
    """创建测试用户（仅用于演示）"""
    # 获取或创建组
    operations_group = Group.objects.get_or_create(name='operations')[0]
    finance_group = Group.objects.get_or_create(name='finance')[0]
    
    # 创建运营用户
    try:
        op_user1 = User.objects.create_user(username='op1', password='password123')
        op_user1.groups.add(operations_group)
        
        op_user2 = User.objects.create_user(username='op2', password='password123')
        op_user2.groups.add(operations_group)
    except:
        op_user1 = None
        op_user2 = None
    
    # 创建财务用户
    try:
        fin_user1 = User.objects.create_user(username='fin1', password='password123')
        fin_user1.groups.add(finance_group)
        
        fin_user2 = User.objects.create_user(username='fin2', password='password123')
        fin_user2.groups.add(finance_group)
    except:
        fin_user1 = None
        fin_user2 = None
    
    return JsonResponse({
        'operations_users_created': op_user1 is not None and op_user2 is not None,
        'finance_users_created': fin_user1 is not None and fin_user2 is not None
    })


@login_required
def get_notifications(request):
    """获取用户相关的通知"""
    user = request.user
    
    try:
        # 获取用户所属的组
        user_groups = user.groups.all()
        
        # 获取用户发送的通知，按创建时间倒序排列
        sent_notifications = Notification.objects.filter(sender=user).order_by('-created_at')
        
        # 获取发送给用户所在组的通知，按创建时间倒序排列
        received_notifications = Notification.objects.filter(receiver_group__in=user_groups).order_by('-created_at')
        
        # 序列化通知数据
        sent_data = [{
            'id': notif.id,
            'content': notif.content,
            'sender': notif.sender.username if notif.sender else None,
            'sender_group': notif.sender_group.name if notif.sender_group else None,
            'receiver_group': notif.receiver_group.name if notif.receiver_group else None,
            'status': notif.status,
            'created_at': notif.created_at.isoformat(),
            'confirmed_by': notif.confirmed_by.username if notif.confirmed_by else None,
            'confirmed_at': notif.confirmed_at.isoformat() if notif.confirmed_at else None
        } for notif in sent_notifications]
        
        received_data = [{
            'id': notif.id,
            'content': notif.content,
            'sender': notif.sender.username if notif.sender else None,
            'sender_group': notif.sender_group.name if notif.sender_group else None,
            'receiver_group': notif.receiver_group.name if notif.receiver_group else None,
            'status': notif.status,
            'created_at': notif.created_at.isoformat(),
            'confirmed_by': notif.confirmed_by.username if notif.confirmed_by else None,
            'confirmed_at': notif.confirmed_at.isoformat() if notif.confirmed_at else None
        } for notif in received_notifications]
        
        return JsonResponse({
            'status': 'success',
            'sent_notifications': sent_data,
            'received_notifications': received_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
