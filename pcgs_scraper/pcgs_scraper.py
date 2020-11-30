#!/usr/bin/env python3
"""
pcgs_scraper.py

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
import json
import pickle
from os.path import isfile

import pcgs_nums
import pcgs_prices


def prompt(message):
    response = input(message)
    if response.lower() in ['yes', 'y', '1']:
        return True
    elif response.lower() in ['no', 'n', '0']:
        return False
    else:
        print('Response not recognized')
        prompt(message)


def combine_number_price():
    """
    Combine the scraped number data and descriptions with the price information
    """
    price_guide = pickle.load(open('scraped_pcgs_prices.pkl', 'rb'))   # dict
    pcgs_numbers = pickle.load(open('number_data.pkl', 'rb'))       # ft

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
    """
    So here was the point when I realized there are about 3000 PCGS numbers in
    the price guide that when you look them up on pcgs.com/pcgsnolookup it will
    tell you:
        (e.g.) The PCGS #2417 is not a valid US coin number.
    ... huh?? So I did some digging and it looks like those may be the prices 
    for different sets or type coins
    """
    for number, entry in price_guide.items():
        if 'description' in list(entry.keys()):
            coins_w_description.append(entry)

    return coins_w_description


def parse_descriptions(price_guide):
    """
    Parse descriptions for coins, e.g.
        '1794 1/2C Low Relief Head, BN' -->
            {'year': '1794',
             'denom': '1/2c',
             'desc': Low Relief Head,
             'color': BN
            }

    :param price_guide: price guide with descriptions, i.e.
        output of combine_number_price
    :return price_guide_parsed: original price guide but with new keys from the
        description
    """
    import re

    year_regex = re.compile(r'\(?(\d\d\d\d)\)?(/\(?\d+\)?)*')
    # notes on year:   #93924: 1914/(3) 5C
    #   #3939: 1918/7-D 5C
    #   #38975: 1825/4/(2) 25C Browning 2
    #   #715594: (2019) 1C Blank Planchet Explore & Discover Set, RD

    mint_regex = re.compile(r'-((P|D|S|CC|O|W|M|A|H)(/(P|D|S|CC|O|W|M|A|H)))')
    # mint mark reference: en.wikipedia.org/wiki/Historical_United_States_mints
    # can have slash with two mints: e.g. #3985: 1938-D/S 5C Buffalo

    denominations = [
        # US Coins
        r'1/2C',     # half cent
        r'1C',       # 1 cent
        r'Cent',
        r' C ',
        r'2C',       # 2 cent
        r'3CS',      # 3 cent silver
        r'3CN',      # 3 cent nickel
        r'5C',       # 5 cent (nickel)
        r'H10C',     # half Dime
        r'10C',      # dime
        r'20C',      # 20 cent
        r'25C',      # quarter
        r'50C',      # half dollar
        r'\$1',       # dollar coin
        r'\$2.50',    # $2.50 gold
        r'\$3',       # $3 gold
        r'\$4',       # $4 gold
        r'\$5',       # $4 gold
        r'\$10',      # $10 gold
        r'\$20',      # $20 St. Gaudens Double Eagle
        r'\$25',      # Gold Eagle
        r'\$50',      # Gold Eagle
        # Colonials and special cases
        r'\'?Penny\'?',
        r'1P',
        r'1/2 ?P',
        r'3Pence',
        r'2Pence',
        r'6Pence',
        r'Shilling',
        r'Shilng',    # Special case, see PCGS#249
        r'1/24RL',    # see PCGS#49
        r'9 Den',     # French colonies, Deniers
        r'15 Den',
        r'30 Den',
        r'Farth',     # e.g. PCGS#256
        r'Sou',       # French Colonies
        r'Sol',       # French Colonies, see PCGS#167113
        r'1/2 Db',    # see PCGS#489
        r'1/2 R'      # see PCGS#600506
        r'1/2 RL',
        r'Rial'
    ]
    denom_option = r'(' + r'|'.join(denominations) + r')'
    denom_regex = re.compile(denom_option)
    # !Cannot just do contains() for denomination:
    #       #4282: 1835 H10C Large Date, Large 5C
    # re.search handles this for us since it just matches the first one

    # Detail is just everything after the denom
    #   #5063: 1945-S 10C Micro S, FB
    #   #802036: 1814 10C STATESOF S.S. Central America #2 (with Pinch)
    # Search algorithm will handle this by calculating edit distance between the
    # multiple options and ranking them

    for entry in price_guide:
        description = entry['description']
        year_search = year_regex.match(description)
        if year_search is None:
            year_short = None
            year_full = None
        else:
            year_short = year_search.group(1)
            year_full = year_search.group(0)
        denom_search = denom_regex.search(description)
        if denom_search is None:
            denom = None
            # detail information would start at different points
            if year_short is None:
                detail = description    # no denomination no year
            else:
                year_span_end = year_search.regs[0][1]
                detail = description[year_span_end:]    # year but no denom
        else:
            denom = denom_search.group(0)
            denom_span_end = denom_search.regs[0][1]
            detail = description[denom_span_end:]

        # update entry with parsed description info
        entry['year_short'] = year_short
        entry['year_full'] = year_full
        entry['denom'] = denom
        entry['detail'] = detail

    return price_guide


def main():
    if isfile('scraped_pcgs_prices.pkl') and isfile('number_data.pkl'):
        # TODO: combine into one
        detailed_price_guide = combine_number_price()
        parsed_price_guide = parse_descriptions(detailed_price_guide)
        msg = 'The PCGS Price Guide is complete. Would you like to save as a ' \
              'pickle file? This format is good for loading as a python ' \
              'object. y/n\n> '
        response = prompt(msg)
        if response is True:
            pickle.dump(parsed_price_guide,
                        open('pcgs_price_guide.pkl', 'wb'))
        msg = 'Would you like to save the PCGS Price Guide as a JSON file? ' \
              'y/n\n> '
        response = prompt(msg)
        if response is True:
            with open('pcgs_price_guide.json', 'w') as outfile:
                json.dump(parsed_price_guide, outfile)
    else:
        if not isfile('scraped_pcgs_prices.pkl'):
            price_prompt = "It looks like you are missing the pricing data. " \
                           "Would you like to scrape that data now? y/n\n> "
            download_price = prompt(price_prompt)
            if download_price is True:
                pcgs_prices.main()
        if not isfile('number_data.pkl'):
            number_prompt = "It looks like you are missing the PCGS number " \
                            "data. Would you like to scrape that data now? y/n" \
                            "\n> "
            download_numbers = prompt(number_prompt)
            if download_numbers:
                pcgs_nums.main()
        # try main again
        main()


if __name__ == "__main__":
    main()
