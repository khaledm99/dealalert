from dotenv import load_dotenv
import os
import requests
from pprint import pprint
import time
import json
from enum import Enum

load_dotenv()

STEAM_ID = os.getenv('STEAM_ID')
ITAD_API_KEY = os.getenv('ITAD_API_KEY')


class Shops(Enum):
    EPIC        = 16
    GOG         = 35
    MICROSOFT   = 48
    NEWEGG      = 49
    STEAM       = 61


def get_wishlist(steamid: str) -> dict:

    try:
        with open('wishlist.json', mode='r', encoding='utf-8') as f:
            names = json.load(f)
            return names
    except OSError:
        print('Failed to open wishlist.json, creating new file and fetching wishlist from Steam...')

    WISHLIST_URL = 'https://api.steampowered.com/IWishlistService/GetWishlist/v1/'
    try:
        response = requests.get(WISHLIST_URL, params={'steamid': steamid})
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(e)
        return None

    data = response.json()
    names = {}

    APPID_LOOKUP_URL = 'http://store.steampowered.com/api/appdetails'
    items = data.get('response').get('items')
    n = 0
    for i in items:
        print(f'Getting item {n}/{len(items)}')
        appid = str(i.get('appid'))
        time.sleep(3)
        try:
            response = requests.get(APPID_LOOKUP_URL, params={'appids': appid})
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)
            return None
        names[appid] = response.json().get(appid).get('data').get('name')
        n += 1

    with open('wishlist.json', mode='w', encoding='utf-8') as f:
        json.dump(names, f)

    return names


def get_itad_id(steamid: str) -> str:

    ITAD_URL = 'https://api.isthereanydeal.com/games/lookup/v1'

    try:
        response = requests.get(ITAD_URL,
                                params={'appid': steamid},
                                headers={'ITAD-API-Key': ITAD_API_KEY})
        response.raise_for_status()
    except Exception as e:
        print(e)
        return 0
    data = response.json()
    if not data.get('found'):
        print(f'Game with steamid {steamid} not found...')
        return 0
    return data.get('game').get('id')


def get_itad_shop_codes():
    URL = 'https://api.isthereanydeal.com/service/shops/v1'

    try:
        response = requests.get(URL, params={'country': 'CA'})
        response.raise_for_status()
    except Exception as e:
        print(e)
        return
    return response.json()


def get_itad_deals(ids: list(str)):

    payload = json.dumps(ids)
    SHOPS = [Shops.STEAM, Shops.GOG, Shops.MICROSOFT, Shops.EPIC, Shops.NEWEGG]
    ITAD_PRICE_URL = 'https://api.isthereanydeal.com/games/overview/v2'
    try:
        response = requests.post(ITAD_PRICE_URL,
                                 params={'country': 'CA',
                                         'shops': SHOPS},
                                 headers={'ITAD-API-Key': ITAD_API_KEY},
                                 json=payload)
        response.raise_for_status()
    except Exception as e:
        print(e)
        return
    return response.json()


if __name__ == '__main__':

    wishlist = get_wishlist(STEAM_ID)
    itad_ids = {}
    try:
        with open('itad_ids.json', mode='r', encoding='utf-8') as f:
            itad_ids = json.load(f)
    except OSError:
        print('Failed to open itad_ids.json, creating new file and fetching ids from IsThereADeal...')
        for steamid in wishlist.keys():
            itad_ids[steamid] = get_itad_id(steamid)

        with open('itad_ids.json', mode='w', encoding='utf-8') as f:
            json.dump(itad_ids, f)

    pprint(itad_ids)
