import logging
import os
from urllib.parse import urlparse
from time import sleep

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


def get_comic(comics_dir):
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    current_comic = response.json()

    pic_extension = os.path.splitext(urlparse(current_comic['img']).path)[1]
    comic_path = os.path.join(
        comics_dir,
        f'{current_comic["num"]}.{current_comic["title"]}.{pic_extension}')
    save_pic(current_comic['img'], comic_path)

    return current_comic['alt']


def get_upload_link(access_token, group_id, user_id):
    url = os.path.join(VK_API_BASE_URL, 'photos.getWallUploadServer')
    payload = {
        'access_token': access_token,
        'user_id': user_id,
        'v': '5.131',
        'group_id': group_id,
    }
    response = requests.get(url, params=payload)
    check_vk_response(response)

    return response.json()['response']['upload_url']


if __name__ == '__main__':
    load_dotenv()
    comics_dir = os.getenv('COMICS_DIR', './comics')
    client_id = os.environ['CLIENT_ID']
    access_token = os.environ['ACCESS_TOKEN']
    group_id = os.environ['GROUP_ID']
    user_id = os.environ['USER_ID']
    os.makedirs(comics_dir, exist_ok=True)

    while True:
        try:
            get_comic(comics_dir)
            upload_link = get_upload_link(access_token, group_id, user_id)
            break
        except requests.exceptions.HTTPError as error:
            logging.warning(f'Ошибка при HTTP запросе: {error}')
            break
        except requests.exceptions.ConnectionError or requests.exceptions.ReadTimeout:
            logging.warning('Ошибка подключения, проверьте сеть интернет.')
            sleep(5)
            logging.warning('Попытка переподключения')
        except VkError:
            logging.warning('Ошибка в ответе от сервера ВКонтакте. Смотри ответ выше')
            break
