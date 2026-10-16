# DealAlert
Python script to retrieve today's PC video game deals from a variety of storefronts.
Pulls a user's Steam wishlist and queries the IsThereADeal public API to get currently
active deals on every game in the wishlist.

All API queries are done via the requests module. Steam wishlist is cached in a local
JSON file, as well as the IsThereADeal game ID's to reduce the amount of mass API
queries from large wishlists.

Uses a discord webhook to send a formatted message containing today's deals complete with
current price, discount percentage, historical low, and link to store pages for each game

To run, requires the following environment variables:
STEAM_ID: User steamid to retrieve wishlist
ITAD_API_KEY: API key from IsThereADeal
DISCORD_WEBHOOK: Discord channel webhook link

Usage:
    pip install -r requirements.txt
    python dealalert.py


