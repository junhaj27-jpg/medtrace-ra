from django.core.management.base import BaseCommand,CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
class Command(BaseCommand):
    help='기존 사용자를 전체 권한 관리자로 승격합니다.'
    def add_arguments(self,parser): parser.add_argument('--username',required=True)
    def handle(self,*args,**options):
        try:user=get_user_model().objects.get(username=options['username'])
        except get_user_model().DoesNotExist: raise CommandError(f"사용자를 찾을 수 없습니다: {options['username']}")
        user.is_staff=True; user.is_superuser=True; user.is_active=True; user.save(); group,_=Group.objects.get_or_create(name='ADMIN'); user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f'관리자로 승격했습니다: {user.username}'))

