from django.core.management.base import BaseCommand
from authapp.models import ShopUser, ShopUserProfile



class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in ShopUser.objects.all():
            user_profile = ShopUserProfile.objects.create(user=user)
            user_profile.save()