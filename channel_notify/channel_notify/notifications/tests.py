from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse
import json
from .models import Notification
from channels.testing import WebsocketCommunicator
from .consumers import NotificationConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationModelTests(TestCase):
    """测试通知模型的基本功能"""
    
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass')
        
        # 创建测试用户组
        self.finance_group = Group.objects.create(name='finance')
        self.hr_group = Group.objects.create(name='hr')
        
        # 将用户添加到组
        self.user.groups.add(self.finance_group)
        self.user2.groups.add(self.hr_group)
    
    def test_notification_creation(self):
        """测试通知创建功能"""
        notification = Notification.objects.create(
            sender=self.user,
            content='测试通知内容',
            sender_group=self.finance_group,
            receiver_group=self.hr_group,
            status='pending'
        )
        
        self.assertEqual(notification.sender, self.user)
        self.assertEqual(notification.content, '测试通知内容')
        self.assertEqual(notification.sender_group, self.finance_group)
        self.assertEqual(notification.receiver_group, self.hr_group)
        self.assertEqual(notification.status, 'pending')
        self.assertIsNone(notification.confirmed_by)
        self.assertIsNone(notification.confirmed_at)
    
    def test_notification_confirmation(self):
        """测试通知确认功能"""
        notification = Notification.objects.create(
            sender=self.user,
            content='测试通知内容',
            sender_group=self.finance_group,
            receiver_group=self.hr_group,
            status='pending'
        )
        
        # 确认通知
        notification.status = 'confirmed'
        notification.confirmed_by = self.user2
        notification.save()
        
        self.assertEqual(notification.status, 'confirmed')
        self.assertEqual(notification.confirmed_by, self.user2)
        self.assertIsNotNone(notification.confirmed_at)  # 保存时应该自动设置
    
    def test_notification_str_method(self):
        """测试通知的字符串表示"""
        notification = Notification.objects.create(
            sender=self.user,
            content='测试通知内容',
            sender_group=self.finance_group,
            receiver_group=self.hr_group,
            status='pending'
        )
        
        # 检查__str__方法输出格式
        str_representation = str(notification)
        self.assertIn('测试通知内容', str_representation)
        self.assertIn('finance', str_representation)
        self.assertIn('hr', str_representation)

class NotificationAPITests(TestCase):
    """测试通知相关API"""
    
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user2 = User.objects.create_user(username='testuser2', password='testpass')
        
        # 创建测试用户组
        self.finance_group = Group.objects.create(name='finance')
        self.hr_group = Group.objects.create(name='hr')
        
        # 将用户添加到组
        self.user.groups.add(self.finance_group)
        self.user2.groups.add(self.hr_group)
        
        # 创建测试通知
        self.notification = Notification.objects.create(
            sender=self.user,
            content='API测试通知',
            sender_group=self.finance_group,
            receiver_group=self.hr_group,
            status='pending'
        )
    
    def test_get_notifications(self):
        """测试获取通知API"""
        # 登录用户
        self.client.login(username='testuser', password='testpass')
        
        # 访问通知API
        response = self.client.get(reverse('get_notifications'))
        
        # 检查响应状态和内容
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['sent_notifications']), 1)
        self.assertEqual(len(data['received_notifications']), 0)

class NotificationWebSocketTests(TestCase):
    """测试WebSocket功能"""
    
    def setUp(self):
        # 创建测试用户和组
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.finance_group = Group.objects.create(name='finance')
        self.user.groups.add(self.finance_group)
    
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        # 创建WebSocket通信器
        communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), '/ws/notifications/finance/')
        
        # 设置scope参数
        communicator.scope['url_route'] = {'kwargs': {'group_name': 'finance'}}
        communicator.scope['user'] = self.user
        
        # 连接WebSocket
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # 检查连接成功消息
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'connection_established')
        
        # 关闭连接
        await communicator.disconnect()
    
    async def test_send_notification(self):
        """测试发送通知功能"""
        communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), '/ws/notifications/finance/')
        
        # 设置scope参数
        communicator.scope['url_route'] = {'kwargs': {'group_name': 'finance'}}
        communicator.scope['user'] = self.user
        
        await communicator.connect()
        
        # 接收连接成功消息
        conn_response = await communicator.receive_json_from()
        self.assertEqual(conn_response['type'], 'connection_established')
        
        # 发送通知消息
        await communicator.send_json_to({
            'type': 'send_notification',
            'content': 'WebSocket测试通知',
            'receiver_group': 'finance'
        })
        
        # 接收响应
        response = await communicator.receive_json_from()
        
        # 检查响应
        self.assertEqual(response['type'], 'notification_sent')
        
        await communicator.disconnect()

# 同步测试装饰器
from django.test import override_settings

@override_settings(ASGI_APPLICATION='channel_notify.asgi.application')
def test_sync_websocket_connection():
    """同步版本的WebSocket连接测试"""
    import asyncio
    
    async def async_test():
        user = User.objects.create_user(username='sync_test_user', password='testpass')
        finance_group = Group.objects.create(name='finance')
        user.groups.add(finance_group)
        
        communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), '/ws/notifications/finance/')
        # 设置scope参数
        communicator.scope['url_route'] = {'kwargs': {'group_name': 'finance'}}
        communicator.scope['user'] = user
        
        connected, _ = await communicator.connect()
        assert connected
        
        response = await communicator.receive_json_from()
        assert response['type'] == 'connection_established'
        
        await communicator.disconnect()
    
    asyncio.run(async_test())
