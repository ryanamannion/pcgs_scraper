#!/usr/bin/env python3
"""
utils.py

utils for scraping

Author: Ryan A. Mannion, 2020
github: ryanamannion
twitter: @ryanamannion
"""
import re
import sys
import time
import requests

from bs4.element import NavigableString


##################
# SCRAPING UTILS #
##################

def request_page(page_url):
    """
    Makes sure page is responding

    :param page_url: url to request
    :return: requested page if its working, error message with status if not
    """
    response = requests.get(page_url)
    if response.status_code == 429:
        # too many requests
        retry_after = response.headers['retry-after']
        print("Encountered response status 429: too many requests\n"
              f"Waiting {retry_after}s and retrying...")
        time.sleep(int(retry_after) + 2)     # for good measure
        print("Retrying...")
        response = request_page(page_url)
    elif not response.status_code == 200:
        print(f'Something went wrong with {page_url}!\n'
              f'Status code: {response.status_code}\n'
              f'Status text:\n' + response.text)
        sys.exit()
    return response


def non_ns_children(tag, search_type):
    """
    Filters out NavigableString children from tree navigation, allows use of
    .children and .descendants methods

    :param tag: bs4.Tag object
    :param search_type: string, {children, descendants}
    :return: list of bs4.Tag objects
    """
    filtered = []
    if search_type == 'children':
        for child in tag.children:
            if not isinstance(child, NavigableString):
                filtered.append(child)
    elif search_type == 'descendants':
        for child in tag.descendants:
            if not isinstance(child, NavigableString):
                filtered.append(child)
    return filtered


#########################
# QUERY & PARSING UTILS #
#########################
YEAR = re.compile(r'\(?(\d\d\d\d)\)?(/\(?\d+\)?)*')

MINT_CODES = [
    'P',        # Philadelphia, also often no mint mark
    'D',        # Dahlonega 1838-1861 (gold); Denver 1906-
    'S',        # San Francisco 1854-
    'CC',       # Carson City 1870-1893
    'O',        # New Orleans 1838-1909
    'W',        # West Point 1937- (commems)
    'M',        # Manila, Philippines 1920-1922, 1925-1941  (centavo)
    'A',
    'H'
    ]
mint_option = r'(' + r'|'.join(MINT_CODES) + r')'
#               -D                     /D
mint_pattern = r'-(' + mint_option + '(/' + mint_option + ')?)'
mint_pattern = r'-((P|D|S|CC|O|W|M|A|H)(/(P|D|S|CC|O|W|M|A|H))?)'
MINT = re.compile(mint_pattern)
MINT_CI = re.compile(mint_pattern, re.IGNORECASE)

DENOMINATIONS = [
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
        r'\$1(?!0)',       # dollar coin
        r'\$2.50',    # $2.50 gold
        r'\$3',       # $3 gold
        r'\$4',       # $4 gold
        r'\$5(?!0)',       # $4 gold
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
denom_option = r'(' + r'|'.join(DENOMINATIONS) + r')'
DENOM = re.compile(denom_option)
DENOM_CI = re.compile(denom_option, re.IGNORECASE)


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
    #################
    # PARSING NOTES #
    #################

    # year:
    #   #93924: 1914/(3) 5C                                 overstamp with paren
    #   #3939: 1918/7-D 5C                                   overstamp w/o paren
    #   #38975: 1825/4/(2) 25C Browning 2                       triple overstamp
    #   #715594: (2019) 1C Blank Planchet Explore & Discover Set, RD       paren

    # mint mark reference: en.wikipedia.org/wiki/Historical_United_States_mints
    # can have slash with two mints: e.g. #3985: 1938-D/S 5C Buffalo

    # Detail is just everything after the denom, or after date if no denom
    #   #5063: 1945-S 10C -->Micro S, FB<--
    #   #802036: 1814 10C -->STATESOF S.S. Central America #2 (with Pinch)<--
    # Search algorithm will handle this by calculating edit distance between the
    # multiple options and ranking them

    for entry in price_guide:
        description = entry['description']

        # get year
        year_search = YEAR.match(description)
        if year_search is None:
            year_short = None
            year_full = None
        else:
            # year_short is for search purposes, year_full is more descriptive
            year_short = year_search.group(1)       # e.g. 1825
            year_full = year_search.group(0)        # e.g. 1825/4/(2) for errors

        # get mint information
        mint_search = MINT.search(description)
        if mint_search is None:
            mint = None
        else:
            mint = mint_search.group(0)
            mint = mint.strip('-')

        # get denomination
        # get detail (everything after denomination, or year if no denom)
        denom_search = DENOM.search(description)
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
        entry['mint'] = mint
        entry['denom'] = denom
        entry['detail'] = detail

    return price_guide


def word_to_digit(input_string):
    """
    Help normalize the query string by replacing typed-out forms of numbers into
    digits. NOTE: this is only for numbers common to coins, and is not meant to
    be for all numbers

    :param input_string: string to change words to digits
    :return output_string: new string with digits in place of numbers
    """
    replacement_pairs = [
        ('one', '1'),
        ('two', '2'),
        ('three', '3'),
        ('four', '4'),
        (r'(?<!twenty )five', '5'),
        ('six', '6'),
        ('seven', '7'),
        ('eight', '8'),
        ('nine', '9'),
        ('ten', '10'),
        ('twenty', '20'),
        ('twenty five', '25'),
        ('fifty', '50')
    ]
    for pattern, replacement in replacement_pairs:
        output_string = re.sub(pattern, replacement, input_string)

    return output_string


def fold_denoms(query_str):
    """
    Given a user input string, normalize and 'fold' denominations into PCGS
    denomination category, less focus is given to colonial coins here, that's a
    to-do

    :param query_str: string queried by the user
    :return :
    """
    denominations_mapping = [
        # key is PCGS denomination
        (r'1/2C', r'(1 )?half( of (a|one) ?)? cents?'),  # half cent
        (r'1C', r'(1 cent|penny)'),  # 1 cent
        # (r'Cent', ['1C']),
        # (r' C ', ['1C'],
        (r'2C', r'2 cents? (silver)?'),  # 2 cent
        (r'3CS', r'3( ?C| cents?) silver'),  # flag this and ask if they mean silver or nickel
        (r'3CN', r'3 cents? nickel'),  # 3 cent nickel
        (r'5C', r'((?<!cent )nickel|5 cents?)'),  # 5 cent (nickel)
        (r'H10C', r'half dime'),  # half Dime
        (r'10C', '(dime|10 cents?)'),  # dime
        (r'20C', r'20 cents?'),  # 20 cent
        (r'25C', r'(quarter|25 cents?)'),  # quarter
        (r'50C', r'(?<!and a )(half dollar|50 cents?)'),  # half dollar
        (r'$1', r'(?<![02-9] )(?<!half )(1 )?dollar'),  # dollar coin
        (r'$2.50', r'(2 (and a half dollars?|dollars and 50 cents)|\$?2\.50)'),  # $2.50 gold
        (r'$3', r'3 dollars?'),  # $3 gold
        (r'$4', r'4 dollars?'),  # $4 gold
        (r'$5', r'5 dollars?'),  # $4 gold
        (r'$10', r'10 dollars?'),  # $10 gold
        (r'$20', r'20 dollars?'),  # $20 St. Gaudens Double Eagle
        (r'$25', r'25 dollars?'),  # Gold Eagle
        (r'$50', r'50 dollars?'),  # Gold Eagle
        # after all of the main ones are done
        (r'1C', r'(?<![0-9] )(?<!half )cent')     # lincoln cent, wheat cent, etc.
        # Colonials and special cases
        # (r'\'?Penny\'?', ['']),
        # (r'1P', ['']),
        # (r'1/2 ?P', ['']),
        # (r'3Pence', ['']),
        # (r'2Pence', ['']),
        # (r'6Pence', ['']),
        # (r'Shilling', ['']),
        # (r'Shilng', ['']),  # Special case, see PCGS#249
        # (r'1/24RL', ['']),  # see PCGS#49
        # (r'9 Den', ['']),  # French colonies, Deniers
        # (r'15 Den', ['']),
        # (r'30 Den', ['']),
        # (r'Farth', ['']),  # e.g. PCGS#256
        # (r'Sou', ['']),  # French Colonies
        # (r'Sol', ['']),  # French Colonies, see PCGS#167113
        # (r'1/2 Db', ['']),  # see PCGS#489
        # (r'1/2 (R', ['']),  # see PCGS#600506
        # (r'1/2 RL', ['']),
        # (r'Rial', ['']
    ]

    query_str = word_to_digit(query_str)

    for repl, pattern in denominations_mapping:
        query_str = re.sub(pattern, repl, query_str, flags=re.IGNORECASE)

    return query_str


def price_table(desig, prices_by_grade):
    """
    Generate printable table for price data

    :param desig: designation info, from coin_entry['desig'] for a given
        coin_entry in the price_guide ft
    :param prices_by_grade: coin_entry['prices'] for a given desig
    :return :
    """
    # get max length for every row to format table
    all_lens = []
    all_lens.extend([len(_) for _ in desig])
    for grade, prices in prices_by_grade.items():
        all_lens.append(len(str(grade)))
        for price in prices:
            if price is not None:
                all_lens.append(len(price))
            else:
                all_lens.append(4)      # len(str(None))
    max_len = max(all_lens)

    # format table parts
    header_row = f'%-{max_len+2}s%-{max_len+2}s%-{max_len+2}s\n' % \
                 ('grade', desig[0], desig[1])
    lines = '='*(max_len+1)
    midrule = lines + '|' + lines + '|' + lines + '\n'

    # table body
    rows = []
    for grade, (price0, price1) in prices_by_grade.items():
        row = f'%-{max_len + 2}s%-{max_len + 2}s%-{max_len + 2}s\n' % \
              (grade, price0, price1)
        rows.append(row)
    body = ''.join(rows)

    table = header_row + midrule + body

    return table
