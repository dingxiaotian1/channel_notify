from django.db import models
from django.contrib.auth.models import User, Group

class Notification(models.Model):
    """通知模型，用于存储运营组发送给财务组的消息"""
    STATUS_CHOICES = (
        ('pending', '待确认'),
        ('confirmed', '已确认'),
    )
    
    content = models.TextField(verbose_name='通知内容')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name='发送者')
    sender_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name='发送者组')
    receiver_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='received_notifications', verbose_name='接收者组')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_notifications', verbose_name='确认者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'从{self.sender_group.name}到{self.receiver_group.name}: {self.content[:20]}...'
    
    def save(self, *args, **kwargs):
        # 当状态变更为confirmed时，自动设置确认时间
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = self.updated_at
        super().save(*args, **kwargs)
