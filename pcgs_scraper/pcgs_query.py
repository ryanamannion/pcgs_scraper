#!/usr/bin/env python3
"""
pcgs_query.py

After scraping price data, this allows the user to query for coins with an input
string

Author: Ryan A. Mannion, 2020
github: ryanamannion
twitter: @ryanamannion
"""
import ft
import sys
import pickle
import argparse
from copy import deepcopy

from nltk.metrics import edit_distance

from pcgs_scraper.utils import YEAR, DENOM_CI, MINT_CI       # regex
from pcgs_scraper.utils import fold_denoms, price_table


def validate_query(query_str, verbose=True):
    """
    Given a query, ensure it has a year and a denomination and extract them

    :param query_str: (str), query input from user
    :return query_params: (tuple)
        year(str),
        denomination(str),
        mint mark(str), str if included, None if not
        original query(str),
        normalized query(str), denomination folded query
    """
    original_query = deepcopy(query_str)

    # normalize query
    query_str = fold_denoms(query_str)      # normalize denominations

    # Required for every query: Year and Denomination
    query_year = YEAR.search(query_str)
    query_denom = DENOM_CI.search(query_str)      # case insensitive
    if query_year is None:
        resp = 'I could not detect a year in your query, please make sure you' \
               ' include a year! e.g. 1997-P 25c'
        if verbose:
            sys.exit(resp)
        else:
            return None
    if query_denom is None:
        resp = 'I could not detect an acceptable denomination in your query, ' \
               'please make sure you include one! e.g. 1997-P 25c'
        if verbose:
            sys.exit(resp)
        else:
            return None

    year_match = query_year.group(0)
    denom_match = query_denom.group(0)

    # get mint mark if provided, else set to None
    query_mint = MINT_CI.search(query_str)
    if query_mint is not None:
        mint_match = query_mint.group(0).strip('-').upper()
    else:
        mint_match = None

    normalized_query = query_str        # alias for clarity

    query_params = (year_match,
                    denom_match,
                    mint_match,
                    original_query,
                    normalized_query)

    return query_params


def rank_results(normalized_query, results):
    """
    Rank results by lowest-highest Levenshtein Edit Distance

    v0.0.4: exact description match returns just that result

    :param normalized_query: query normalized (denom folded)
    :param results: results list from query_price_guide
    :return sorted_results: results sorted from lowest to highest edit distance
    """
    scores = []
    for result in results:
        score = edit_distance(normalized_query, result['description'])
        if score == 0:      # exact match
            return [result]
        scores.append((score, result))
    # sort scores by index 0, aka edit distance
    scores.sort(key=lambda x: x[0])
    sorted_results = [score[1] for score in scores]
    return sorted_results


def query_price_guide(query_tuple, coin_ft):
    """
    With a validated query, return one or more coins from the free table
    matching the description

    :param query_tuple: (tuple) output from validate_query
    :param coin_ft: (list(dict)) free table of coin prices, made with
        pcgs_scraper
    :return :
    """
    query_year, query_denom, query_mint, query_orig, query_norm = query_tuple

    # lots of loops, make life easy
    result_found = False

    # index the ft by year to quick search for year
    coins_by_year = ft.indexBy('year_short', coin_ft)
    for year, year_coins in coins_by_year.items():
        if result_found:
            break
        if year == query_year:
            coins_by_denom = ft.indexBy('denom', year_coins)
            for denom, denom_coins in coins_by_denom.items():
                if result_found:
                    break
                if denom == query_denom:
                    if query_mint is not None:
                        coins_by_mint = ft.indexBy('mint', denom_coins)
                        for mint, mint_coins in coins_by_mint.items():
                            if mint == query_mint:
                                # ding ding ding: year, denom, & mint match
                                results = mint_coins
                                result_found = True
                                break
                        else:
                            # mint loop completed without breaks, means no mint
                            # match was found ... return denomination matches
                            # anyway (max 4-5 coins, user can choose)
                            results = denom_coins
                            result_found = True
                            break
                    else:
                        # query_mint is none, return denominations
                        results = denom_coins
                        result_found = True
                        break
            else:
                # denomination loop completed without breaking, no match found
                # perhaps that denomination was not minted in the specified year
                results = None
                break
    else:
        # year loop completed without breaking, no year match found
        # perhaps the specified year was out of range, or mistyped
        results = None

    # rank results by Levenshtein Edit Distance
    if results is not None:
        if len(results) > 1:
            results = rank_results(query_norm, results)

    return results


def query_cli(query_str, price_guide):
    """
    Handle printing messages etc. for CLI

    :param query_str:
    :param price_guide:
    :return:
    """
    if query_str is None:
        sys.exit("Please provide a query with the -q option")

    validated_query = validate_query(query_str)

    print(f"Recognized Query:")
    print(f"\tInput: {validated_query[3]}")
    print(f"\tYear: {validated_query[0]}")
    print(f"\tMint: {validated_query[2]}")
    print(f"\tDenomination: {validated_query[1]}")

    query_results = query_price_guide(validated_query, price_guide)
    if query_results is None:
        print(f"Found 0 results")
        sys.exit()
    print(f"Found {len(query_results)} results:")
    for i, query_result in enumerate(query_results):
        pcgs_num = query_result['pcgs_num']
        description = query_result['description']
        print(f"{i} -> PCGS#{pcgs_num}: {description}")

    inspect = True
    while inspect is True:
        print(f"Enter the number of the coin you would like to see prices for")
        print(f"Enter quit to quit")
        selection = input("> ")
        if selection.isdigit() and int(selection) in range(len(query_results)):
            selected_coin = query_results[int(selection)]
            table = price_table(selected_coin['desig'], selected_coin['prices'])
            print(f'Prices for {selected_coin["description"]}:')
            print(table)
        elif selection.isdigit() and selection not in range(len(query_results)):
            print('Please enter one of the numbers listed above')
        elif selection.lower() in ['quit', 'exit', 'stop', 'end']:
            sys.exit()
        else:
            print('Input not recognized. Try again.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--price_guide', '-p', action='store',
                        help='path to binary for price guide created with '
                             'pcgs_scraper package, link at '
                             'https://github.com/ryanamannion/pcgs_scraper.git '
                             '\nDefaults to 30-11-2020',
                        default='data/pcgs_price_guide.pkl'
                        )
    parser.add_argument('--query', '-q', action='store',
                        help='Coin to get price for, in format: \n '
                             '\tYYYY(-M) DNM...\n'
                             'where YYYY is the year, -M the optional mint mark'
                             ' and DNM the denomination (dime, penny, 25c, $1),'
                             ' any details may follow to give more information'
                             ' about the coin')
    args = parser.parse_args()

    query_cli(args.query, pickle.load(open(args.price_guide, 'rb')))
