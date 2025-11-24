from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = '初始化通知系统所需的组和用户'

    def handle(self, *args, **kwargs):
        # 创建组
        self.stdout.write('正在创建组...')
        operations_group_1, created = Group.objects.get_or_create(name='operations_group_1')
        if created:
            self.stdout.write(self.style.SUCCESS(f'创建运营一组: {operations_group_1.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'运营一组已存在: {operations_group_1.name}'))
        
        operations_group_2, created = Group.objects.get_or_create(name='operations_group_2')
        if created:
            self.stdout.write(self.style.SUCCESS(f'创建运营二组: {operations_group_2.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'运营二组已存在: {operations_group_2.name}'))
        
        finance_group_1, created = Group.objects.get_or_create(name='finance_group_1')
        if created:
            self.stdout.write(self.style.SUCCESS(f'创建财务一组: {finance_group_1.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'财务一组已存在: {finance_group_1.name}'))
        
        finance_group_2, created = Group.objects.get_or_create(name='finance_group_2')
        if created:
            self.stdout.write(self.style.SUCCESS(f'创建财务二组: {finance_group_2.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'财务二组已存在: {finance_group_2.name}'))
        
        # 创建用户
        self.stdout.write('\n正在创建用户...')
        
        # 运营一组用户
        try:
            op_user1, created = User.objects.get_or_create(username='op1')
            if created:
                op_user1.set_password('password123')
                op_user1.save()
                op_user1.groups.add(operations_group_1)
                self.stdout.write(self.style.SUCCESS(f'创建运营一组用户: op1'))
            else:
                # 更新用户组
                op_user1.groups.clear()
                op_user1.groups.add(operations_group_1)
                self.stdout.write(self.style.WARNING(f'运营一组用户已存在，更新组: op1'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建运营一组用户失败: {e}'))
        
        # 运营二组用户
        try:
            op_user2, created = User.objects.get_or_create(username='op2')
            if created:
                op_user2.set_password('password123')
                op_user2.save()
                op_user2.groups.add(operations_group_2)
                self.stdout.write(self.style.SUCCESS(f'创建运营二组用户: op2'))
            else:
                # 更新用户组
                op_user2.groups.clear()
                op_user2.groups.add(operations_group_2)
                self.stdout.write(self.style.WARNING(f'运营二组用户已存在，更新组: op2'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建运营二组用户失败: {e}'))
        
        # 财务一组用户
        try:
            fin_user1, created = User.objects.get_or_create(username='fin1')
            if created:
                fin_user1.set_password('password123')
                fin_user1.save()
                fin_user1.groups.add(finance_group_1)
                self.stdout.write(self.style.SUCCESS(f'创建财务一组用户: fin1'))
            else:
                # 更新用户组
                fin_user1.groups.clear()
                fin_user1.groups.add(finance_group_1)
                self.stdout.write(self.style.WARNING(f'财务一组用户已存在，更新组: fin1'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建财务一组用户失败: {e}'))
        
        # 财务二组用户
        try:
            fin_user2, created = User.objects.get_or_create(username='fin2')
            if created:
                fin_user2.set_password('password123')
                fin_user2.save()
                fin_user2.groups.add(finance_group_2)
                self.stdout.write(self.style.SUCCESS(f'创建财务二组用户: fin2'))
            else:
                # 更新用户组
                fin_user2.groups.clear()
                fin_user2.groups.add(finance_group_2)
                self.stdout.write(self.style.WARNING(f'财务二组用户已存在，更新组: fin2'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'创建财务二组用户失败: {e}'))
        
        self.stdout.write('\n初始化完成！')
        self.stdout.write('\n可用用户:')
        self.stdout.write('- 运营一组: op1 / password123')
        self.stdout.write('- 运营二组: op2 / password123')
        self.stdout.write('- 财务一组: fin1 / password123')
        self.stdout.write('- 财务二组: fin2 / password123')
