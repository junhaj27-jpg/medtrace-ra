import os
from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
class Command(BaseCommand):
    help='전체 권한 관리자 계정을 생성하거나 갱신합니다.'
    def add_arguments(self,parser):
        parser.add_argument('--username',default=os.getenv('ADMIN_USERNAME'))
        parser.add_argument('--email',default=os.getenv('ADMIN_EMAIL',''))
        parser.add_argument('--password',default=os.getenv('ADMIN_PASSWORD'))
    def handle(self,*args,**options):
        username=options['username']; password=options['password']; email=options['email']
        if not username: raise CommandError('사용자명은 --username 또는 ADMIN_USERNAME으로 입력해야 합니다.')
        if not password: raise CommandError('비밀번호는 --password 또는 ADMIN_PASSWORD로 입력해야 합니다.')
        if len(password)<8: raise CommandError('비밀번호는 8자 이상이어야 합니다.')
        User=get_user_model(); user,created=User.objects.get_or_create(username=username,defaults={'email':email})
        user.email=email; user.is_staff=True; user.is_superuser=True; user.is_active=True; user.set_password(password); user.save()
        admin_group,_=Group.objects.get_or_create(name='ADMIN'); user.groups.add(admin_group)
        verb='생성' if created else '갱신'; self.stdout.write(self.style.SUCCESS(f'관리자 계정을 {verb}했습니다: {username}'))

