import logging
import os
import random
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

from tools import save_pic

VK_API_BASE_URL = 'https://api.vk.com/method/'


class VkError(Exception):
    pass


def check_vk_response(response):
    if response.json().get('error'):
        logging.warning(response.json())
        raise VkError


def fetch_random_comic(comics_dir):
    current_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(current_comic_url)
    response.raise_for_status()
    current_comic_number = response.json()['num']

    random_comic_number = random.randint(1, current_comic_number)
    random_comic_url = f'https://xkcd.com/{random_comic_number}/info.0.json'
    response = requests.get(random_comic_url)
    response.raise_for_status()
    random_comic = response.json()

    pic_extension = os.path.splitext(urlparse(random_comic['img']).path)[1]
    comic_path = os.path.join(
        comics_dir,
        f'{random_comic_number}.{random_comic["safe_title"]}{pic_extension}'
    )
    save_pic(random_comic['img'], comic_path)

    return random_comic['alt'], comic_path


def get_upload_link(access_token, user_id, group_id):
    url = os.path.join(VK_API_BASE_URL, 'photos.getWallUploadServer')
    payload = {
        'access_token': access_token,
        'user_id': user_id,
        'v': '5.131',
        'group_id': group_id,
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_vk_response(response)

    return response.json()['response']['upload_url']


def upload_comic(upload_link, comic_path):
    with open(comic_path, 'rb') as photo:
        files = {
            'photo': photo
        }
        response = requests.post(upload_link, files=files)
    response.raise_for_status()
    check_vk_response(response)
    uploaded_photo_params = response.json()
    return uploaded_photo_params['server'],\
        uploaded_photo_params['photo'],\
        uploaded_photo_params['hash']


def save_in_album(
    access_token, group_id,
    comic_server, comic_information, comic_hash
):
    url = os.path.join(VK_API_BASE_URL, 'photos.saveWallPhoto')
    payload = {
        'access_token': access_token,
        'group_id': group_id,
        'server': comic_server,
        'photo': comic_information,
        'hash': comic_hash,
        'v': '5.131'
    }
    response = requests.post(url, params=payload)
    response.raise_for_status()
    check_vk_response(response)
    return response.json()["response"][0]["id"]


def post_comic_to_wall(access_token, group_id, user_id, comic_alt, photo_id):
    url = os.path.join(VK_API_BASE_URL, 'wall.post')
    params = {
        'access_token': access_token,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': comic_alt,
        'attachments': f'photo{user_id}_{photo_id}',
        'v': '5.131'
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    check_vk_response(response)


if __name__ == '__main__':
    load_dotenv()
    comics_dir = os.getenv('COMICS_DIR', 'comics')
    access_token = os.environ['ACCESS_TOKEN']
    group_id = os.environ['GROUP_ID']
    user_id = os.environ['USER_ID']
    os.makedirs(comics_dir, exist_ok=True)

    try:
        comic_alt, comic_path = fetch_random_comic(comics_dir)
        upload_link = get_upload_link(access_token, user_id, group_id)
        comic_server, comic_information, comic_hash = upload_comic(
            upload_link,
            comic_path
        )
        photo_id = save_in_album(
            access_token,
            group_id,
            comic_server,
            comic_information,
            comic_hash
        )
        post_comic_to_wall(
            access_token,
            group_id,
            user_id,
            comic_alt,
            photo_id
        )
    except requests.exceptions.HTTPError:
        logging.exception(f'???????????? ?????? HTTP ??????????????')
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout
    ):
        logging.exception('???????????? ??????????????????????, ?????????????????? ???????? ????????????????.')
    except VkError:
        logging.exception(
            '???????????? ?? ???????????? ???? ?????????????? ??????????????????. ???????????? ?????????? ????????.'
        )
    finally:
        files_in_dir = os.listdir(comics_dir)
        for filename in files_in_dir:
            os.remove(os.path.join(comics_dir, filename))
        os.rmdir(comics_dir)
