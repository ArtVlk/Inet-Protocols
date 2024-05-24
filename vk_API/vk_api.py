import requests
from config import API_KEY, USER_ID, API_VERSION

URL = f"https://api.vk.com/method/friends.get?user_id={USER_ID}&fields=first_name,last_name&access_token={API_KEY}&v={API_VERSION}"


def fetch_friends():
    response = requests.get(URL)
    with open('data.txt', 'w', encoding='utf-8') as file:
        friend = response.json()

        if 'response' in friend:
            friend_list = friend['response']['items']
            for friend in friend_list:
                file.write(friend['first_name'] + ' ' + friend['last_name'] + '\n')
        else:
            print('Ошибка при получении полного списка друзей:', friend)


class VK_API:
    def __init__(self, user_id, access_token, version):
        self.version = version
        self.user_id = user_id
        self.access_token = access_token


vk_app = VK_API(USER_ID, API_KEY, API_VERSION)
fetch_friends()
