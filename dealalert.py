from dotenv import load_dotenv
import os
import requests
import time
import json
from enum import IntEnum

load_dotenv()

STEAM_ID = os.getenv('STEAM_ID')
ITAD_API_KEY = os.getenv('ITAD_API_KEY')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')


# Assigns names to ITAD shop codes
class Shops(IntEnum):
    EPIC        = 16
    GOG         = 35
    MICROSOFT   = 48
    NEWEGG      = 49
    STEAM       = 61


# Retrieves steamid's and game names for user wishlist
# Caches in local file to prevent flooding Steam's API every time
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


# Gets ITAD hex uuid by querying with steam app steamid
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


# Takes a list of ITAD hex uuid's and returns all currently
# active sale details
def get_itad_deals(ids: list[str]):

    payload = ids
    raw_query_string = f'country=CA&deals=true&shops={Shops.STEAM},{Shops.GOG},{Shops.MICROSOFT},{Shops.EPIC},{Shops.NEWEGG}'
    ITAD_PRICE_URL = 'https://api.isthereanydeal.com/games/prices/v3'
    try:
        response = requests.post(ITAD_PRICE_URL,
                                 params=raw_query_string,
                                 headers={'ITAD-API-Key': ITAD_API_KEY},
                                 json=payload)
        response.raise_for_status()
    except Exception as e:
        print(e)
        return
    return response.json()


def construct_deals_string(deals, game_name):
    s = ''
    s += f'Game: {game_name}\n'
    for d in deals.get('deals'):
        s += f'    Shop: {d.get('shop').get('name')}\n'
        s += f'    Current Price: {d.get('price').get('amount')}\n'
        s += f'    Regular Price: {d.get('regular').get('amount')}\n'
        s += f'    Discount: {d.get('cut')}%\n'
        s += f'    URL: {d.get('url')}\n'
        s += '------------------------\n'
    s += f'Lowest: {deals.get('historyLow').get('all').get('amount')}\n'
    s += '############################\n'
    return s


def send_deals_to_discord(deals):

    try:
        response = requests.post(DISCORD_WEBHOOK, json={'content': deals}, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
    except Exception as e:
        print(e)
    print(response.text)


if __name__ == '__main__':

    wishlist = get_wishlist(STEAM_ID)
    itad_ids = {}

    # Retrieve ITAD game ID's, caching in a local file to reduce need
    # to constantly query the API
    try:
        with open('itad_ids.json', mode='r', encoding='utf-8') as f:
            itad_ids = json.load(f)
    except OSError:
        print('Failed to open itad_ids.json, creating new file and fetching ids from IsThereADeal...')
        for steamid in wishlist.keys():
            itad_ids[steamid] = get_itad_id(steamid)

        with open('itad_ids.json', mode='w', encoding='utf-8') as f:
            json.dump(itad_ids, f)

    # We use another dictionary to reverse lookup steamid's from ITAD id's
    inverse_itad_ids = {v: k for k, v in itad_ids.items()}

    id_list = [i for i in itad_ids.values()][:10]
    deals = get_itad_deals(id_list)
    deal_strings = []
    for d in deals:
        steamid = inverse_itad_ids.get(d.get('id'))
        name = wishlist.get(steamid)
        deal_strings.append(construct_deals_string(d, name))
    final_string = "".join(deal_strings)
    send_deals_to_discord(final_string)

