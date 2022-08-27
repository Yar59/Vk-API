import logging
import os
from urllib.parse import urlparse
from time import sleep

import requests
from dotenv import load_dotenv

from tools import save_pic


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


if __name__ == '__main__':
    load_dotenv()
    comics_dir = os.getenv("COMICS_DIR", "./comics")
    os.makedirs(comics_dir, exist_ok=True)

    while True:
        try:
            get_comic(comics_dir)
            break
        except requests.exceptions.HTTPError:
            logging.warning("Не удалось загрузить текущий комикс, попробуйте позднее")
            break
        except requests.exceptions.ConnectionError or requests.exceptions.ReadTimeout:
            logging.warning("Ошибка подключения, проверьте сеть интернет.")
            sleep(5)
            logging.warning("Попытка переподключения")
