import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User, Group
from django.utils import timezone
from .models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket消费者，处理通知的发送和接收"""
    
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.user = self.scope['user']
        
        # 添加详细调试日志
        print(f"WebSocket连接尝试: group_name={self.group_name}, user={self.user}, is_authenticated={self.user.is_authenticated}")
        
        # 验证用户是否已认证
        if not self.user.is_authenticated:
            print(f"WebSocket连接拒绝: 用户未认证")
            await self.close(code=401)  # 未授权
            return
        
        # 验证用户是否属于该组
        user_in_group = await self.user_in_group(self.user, self.group_name)
        print(f"用户组验证: user_in_group={user_in_group}")
        
        if not user_in_group:
            print(f"WebSocket连接拒绝: 用户不属于组 {self.group_name}")
            await self.close(code=403)  # 禁止访问
            return
        
        # 将用户添加到对应的WebSocket组
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        print(f"WebSocket连接成功: 用户 {self.user} 加入组 {self.group_name}")
        await self.accept()
        
        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'成功连接到{self.group_name}组的通知频道'
        }))
    
    async def disconnect(self, close_code):
        # 从组中移除用户
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """接收WebSocket消息"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'send_notification':
                # 发送通知给另一个组
                await self.send_notification(text_data_json)
            elif message_type == 'confirm_notification':
                # 确认通知
                await self.confirm_notification(text_data_json)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'未知的消息类型: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '无效的JSON格式'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'处理消息时发生错误: {str(e)}'
            }))
    
    async def send_notification(self, data):
        """发送通知给接收组，确保组对应关系正确"""
        content = data.get('content')
        receiver_group_name = data.get('receiver_group')
        
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '缺少必要参数: content'
            }))
            return
        
        try:
            # 获取当前用户所属的组
            sender_group = await self.get_user_group(self.user)
            
            if not sender_group:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': '用户不属于任何组'
                }))
                return
            
            sender_group_name = sender_group.name
            
            # 根据对应关系确定接收组
            if not receiver_group_name:
                # 如果没有指定接收组，根据对应关系自动选择
                receiver_group_name = await self.get_corresponding_group(sender_group_name)
                if not receiver_group_name:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'无法确定与{sender_group_name}对应的组'
                    }))
                    return
            else:
                # 验证指定的接收组是否与发送组对应
                expected_receiver = await self.get_corresponding_group(sender_group_name)
                if expected_receiver and receiver_group_name != expected_receiver:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': f'{sender_group_name}只能发送通知给{expected_receiver}'
                    }))
                    return
            
            # 验证接收组是否存在
            if not await self.group_exists(receiver_group_name):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'接收组 {receiver_group_name} 不存在'
                }))
                return
            
            # 获取接收组
            receiver_group = await self.get_group_by_name(receiver_group_name)
            
            # 创建通知记录
            notification = await self.create_notification(
                content=content,
                sender=self.user,
                sender_group=sender_group,
                receiver_group=receiver_group
            )
            
            # 向接收组广播通知
            await self.channel_layer.group_send(
                receiver_group_name,
                {
                    'type': 'notification_message',
                    'message': {
                        'id': notification.id,
                        'content': notification.content,
                        'sender': notification.sender.username,
                        'sender_group': notification.sender_group.name,
                        'created_at': notification.created_at.isoformat(),
                        'status': notification.status
                    }
                }
            )
            
            # 向发送者返回成功消息
            await self.send(text_data=json.dumps({
                'type': 'notification_sent',
                'message': {
                    'id': notification.id,
                    'content': notification.content,
                    'receiver_group': receiver_group_name,
                    'created_at': notification.created_at.isoformat(),
                    'status': notification.status
                }
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'创建通知时发生错误: {str(e)}'
            }))
    
    async def confirm_notification(self, data):
        """确认通知"""
        notification_id = data.get('notification_id')
        
        if not notification_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '缺少通知ID'
            }))
            return
        
        try:
            # 获取通知信息（包括必要的外键字段）
            notification_data = await self.get_notification_with_groups(notification_id)
            
            if not notification_data:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': '通知不存在'
                }))
                return
            
            # 检查通知是否已被确认
            if notification_data['status'] == 'confirmed':
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': '该通知已经被确认'
                }))
                return
            
            # 检查用户是否有权限确认该通知
            if not await self.user_in_group(self.user, notification_data['receiver_group_name']):
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': '您没有权限确认此通知'
                }))
                return
            
            # 更新通知状态
            updated_data = await self.update_notification_status(
                notification_id=notification_id,
                user=self.user
            )
            
            if not updated_data:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': '更新通知状态失败'
                }))
                return
            
            # 向发送组广播确认消息
            await self.channel_layer.group_send(
                notification_data['sender_group_name'],
                {
                    'type': 'notification_confirmed',
                    'message': {
                        'id': updated_data['id'],
                        'content': updated_data['content'],
                        'confirmed_by': updated_data['confirmed_by_username'],
                        'confirmed_at': updated_data['confirmed_at'],
                        'receiver_group': notification_data['receiver_group_name']
                    }
                }
            )
            
            # 向确认者返回成功消息
            await self.send(text_data=json.dumps({
                'type': 'notification_confirmed',
                'message': {
                    'id': updated_data['id'],
                    'content': updated_data['content'],
                    'confirmed_by': updated_data['confirmed_by_username'],
                    'confirmed_at': updated_data['confirmed_at']
                }
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'确认通知时发生错误: {str(e)}'
            }))
    
    async def notification_message(self, event):
        """发送通知消息给客户端"""
        await self.send(text_data=json.dumps(event))
    
    async def notification_confirmed(self, event):
        """发送确认消息给客户端"""
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def user_in_group(self, user, group_name):
        """检查用户是否属于指定组"""
        return user.groups.filter(name=group_name).exists()
    
    @database_sync_to_async
    def get_user_group(self, user):
        """获取用户所属的组，包括具体的运营组和财务组"""
        groups = user.groups.all()
        # 返回用户所属的第一个组
        return groups[0] if groups else None
        
    @database_sync_to_async
    def get_corresponding_group(self, group_name):
        """获取对应的组，运营一组对应财务一组，运营二组对应财务二组"""
        group_mapping = {
            'operations_group_1': 'finance_group_1',
            'finance_group_1': 'operations_group_1',
            'operations_group_2': 'finance_group_2',
            'finance_group_2': 'operations_group_2'
        }
        return group_mapping.get(group_name)
    
    @database_sync_to_async
    def get_group_by_name(self, name):
        """根据名称获取组"""
        try:
            return Group.objects.get(name=name)
        except Group.DoesNotExist:
            return None
    
    @database_sync_to_async
    def create_notification(self, content, sender, sender_group, receiver_group):
        """创建新通知"""
        return Notification.objects.create(
            content=content,
            sender=sender,
            sender_group=sender_group,
            receiver_group=receiver_group
        )
    
    @database_sync_to_async
    def update_notification_status(self, notification_id, user):
        """更新通知状态为已确认，返回更新后的信息字典而不是对象"""
        try:
            notification = Notification.objects.get(id=notification_id)
            # 检查用户是否属于接收组
            if user.groups.filter(id=notification.receiver_group.id).exists():
                notification.status = 'confirmed'
                notification.confirmed_by = user
                notification.confirmed_at = timezone.now()
                notification.save()
                # 返回字典而不是对象，避免在异步上下文中访问关系字段
                return {
                    'id': notification.id,
                    'content': notification.content,
                    'confirmed_by_username': user.username,
                    'confirmed_at': notification.confirmed_at.isoformat()
                }
            return None
        except Notification.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_notification_with_groups(self, notification_id):
        """获取通知及其关联的组信息，避免在异步上下文中触发懒加载"""
        try:
            notification = Notification.objects.select_related('sender_group', 'receiver_group').get(id=notification_id)
            return {
                'id': notification.id,
                'content': notification.content,
                'status': notification.status,
                'sender_group_name': notification.sender_group.name,
                'receiver_group_name': notification.receiver_group.name
            }
        except Notification.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_notification(self, notification_id):
        """获取通知"""
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None
    
    @database_sync_to_async
    def group_exists(self, group_name):
        """检查组是否存在"""
        return Group.objects.filter(name=group_name).exists()