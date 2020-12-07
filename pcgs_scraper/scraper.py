#!/usr/bin/env python3
"""
scraper.py

Brings together PCGS# data scraped with pcgs_nums.py and price data from
pcgs_prices.py to create single set of information containing:
    - PCGS Number
    - Price data at the time of scraping
    - Designation
    - Detailed Description

Author: Ryan A. Mannion, 2020
github: ryanamannion
twitter: @ryanamannion
"""
import sys
import json
import pickle
from os.path import isfile

from pcgs_scraper import pcgs_nums
from pcgs_scraper import pcgs_prices
from pcgs_scraper.utils import parse_descriptions


def prompt(message):
    response = input(message)
    if response.lower() in ['yes', 'y', '1']:
        return True
    elif response.lower() in ['no', 'n', '0']:
        return False
    print('Response not recognized')
    prompt(message)


def combine_number_price():
    """
    Combine the scraped number data and descriptions with the price information
    """
    price_guide = pickle.load(open('data/scraped_pcgs_prices.pkl', 'rb')) # dict
    pcgs_numbers = pickle.load(open('data/number_data.pkl', 'rb'))       # ft

    # -1 because of the None tags
    print(f"Price guide contains {len(price_guide) - 1} entries")
    print(f"Detailed PCGS # to description mapping contains "
          f"{len(pcgs_numbers)} entries")

    pcgs_number_lookup = {}
    for entry in pcgs_numbers:
        pcgs_number_lookup[entry['pcgs_num']] = entry

    for number, price_entry in price_guide.items():
        try:
            detail = pcgs_number_lookup[number]
        except KeyError:
            # for debugging, see note below
            # print(f'KeyError for key: {number}', end=" ", flush=True)
            # print('continuing...')
            continue
        price_entry['description'] = detail['description']
        price_entry['coin_detail'] = detail

    coins_w_description = []        # free table

    # So here was the point when I realized there are about 3000 PCGS numbers in
    # the price guide that when you look them up on pcgs.com/pcgsnolookup it
    # will tell you:
    #     (e.g.) The PCGS #2417 is not a valid US coin number.
    # ... huh?? So I did some digging and it looks like those may be the prices
    # for different sets or type coins

    for number, entry in price_guide.items():
        if 'description' in list(entry.keys()):
            coins_w_description.append(entry)

    return coins_w_description


def cli():
    # ensure user has the necessary files
    if isfile('data/scraped_pcgs_prices.pkl') \
            and isfile('data/number_data.pkl'):

        # check if user wants to redownload prices
        msg = "It looks like you have already scraped data, would you like to" \
              " rescrape? Selecting yes will rescrape price data, selecting" \
              " no will continue the process of creating the price guide y/n\n>"
        response = prompt(msg)
        if response:
            msg = "WARNING: This operation will overwrite files with the " \
                  "name: data/scraped_pcgs_prices.pkl\n" \
                  "Are you sure you want to continue? y/n\n>"
            confirmation = prompt(msg)
            if confirmation:
                pcgs_prices.main()
            else:
                sys.exit()

        detailed_price_guide = combine_number_price()
        parsed_price_guide = parse_descriptions(detailed_price_guide)
        msg = 'The PCGS Price Guide is complete. Would you like to save as a ' \
              'pickle file? This format is good for loading as a python ' \
              'object. y/n\n> '
        response = prompt(msg)
        if response:
            pickle.dump(parsed_price_guide,
                        open('data/pcgs_price_guide.pkl', 'wb'))
        msg = 'Would you like to save the PCGS Price Guide as a JSON file? ' \
              'y/n\n> '
        response = prompt(msg)
        if response:
            with open('data/pcgs_price_guide.json', 'w') as outfile:
                json.dump(parsed_price_guide, outfile)
    # if they do not, prompt to download them
    else:
        if not isfile('data/scraped_pcgs_prices.pkl'):
            price_prompt = "It looks like you are missing the pricing data. " \
                           "Would you like to scrape that data now? y/n\n> "
            download_price = prompt(price_prompt)
            if download_price:
                pcgs_prices.main()
        if not isfile('data/number_data.pkl'):
            number_prompt = "It looks like you are missing the PCGS number " \
                            "data. Would you like to scrape that data now? y/n" \
                            "\n> "
            download_numbers = prompt(number_prompt)
            if download_numbers:
                pcgs_nums.main()
        # try main again
        cli()


if __name__ == "__main__":
    cli()
