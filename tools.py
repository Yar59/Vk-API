import requests


def save_pic(pic_url, pic_path, headers=None, params=None):
    response = requests.get(pic_url, headers=headers, params=params)
    response.raise_for_status()
    with open(pic_path, 'wb') as file:
        file.write(response.content)
