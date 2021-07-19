from collections import OrderedDict
from datetime import datetime
from urllib.parse import urlencode, urlunparse

import requests
from django.utils import timezone
from social_core.exceptions import AuthForbidden

from authapp.models import ShopUserProfile


def save_user_profile(backend, user, response, *args, **kwargs):
    if backend.name != 'vk-oauth2':
        return

    params = f"fields=bdate, sex, about, photo_max_orig&v=5.131&access_token={response['access_token']}"
    api_url = f"http://api.vk.com/method/users.get?{params}"

    resp = requests.get(api_url)
    if resp.status_code != 200:
        return

    data = resp.json()['response'][0]
    if data['sex']:
        user.shopuserprofile.gender = ShopUserProfile.MALE if data['sex'] == 2 else ShopUserProfile.FEMALE

    if data['about']:
        user.shopuserprofile.about_me = data['about']

    if data['bdate']:
        bdate = datetime.strptime(data['bdate'], '%d.%m.%Y').date()

        age = timezone.now().date().year - bdate.year
        if age < 18:
            user.delete()
            raise AuthForbidden('social_core.backends.vk.VKOAuth2')
        user.age = age

    if data['photo_max_orig']:
        photo_link = data['photo_max_orig']
        photo_response = requests.get(photo_link)
        user_photo_path = f"users_avatars/{user.pk}.jpg"
        with open(f'media/{user_photo_path}', 'wb') as photo_file:
            photo_file.write(photo_response.content)
        user.avatar = user_photo_path

    user.save()