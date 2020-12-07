#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pcgs_prices.py

Script to programmatically scrape all coin prices from www.pcgs.com/prices

Author: Ryan A. Mannion, 2020
github: ryanamannion
twitter: @ryanamannion
"""
import json
import time
import pickle
import argparse
from tqdm import tqdm
from datetime import datetime
from collections import defaultdict

import ft
from bs4 import BeautifulSoup

from pcgs_scraper.utils import request_page, non_ns_children

INDEX = 'https://www.pcgs.com'
PRICES = 'https://www.pcgs.com/prices'
BINS = ['grades-1-20', 'grades-25-60', 'grades-61-70']
GRADES = [1, 2, 3, 4, 6, 8, 10, 12, 15, 20, 25, 30, 35, 40, 45, 50, 53, 55, 58,
          60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70]


######################
# SCRAPING FUNCTIONS #
######################
def get_urls(page_url):
    """
    Gets urls for each subcategory on the /prices page, returns them as a
    dictionary where the keys are the categories, and the values are a tuple of
    (subcategory_name, subcategory_url)

    :return urls_by_category: (dict) dict of all urls on /prices page
    """
    # prep page html and soup
    page = request_page(page_url)
    soup = BeautifulSoup(page.text, 'html.parser')

    urls_by_category = defaultdict(list)

    # get all category urls from /prices page
    # first: get two columns which contain the boxes for each category
    columns = soup.find_all('div', class_='col-xs-12 col-sm-6')
    for column in columns:
        for box in non_ns_children(column, 'children'):
            for box_element in non_ns_children(box, 'children'):
                if 'class' in box_element.attrs and \
                        'coin-heading' in box_element.attrs['class']:
                    heading = box_element.text.strip()
                elif box_element.name == 'ul':
                    for list_item in non_ns_children(box_element, 'children'):
                        # presumably only has one tag as a child, <a>
                        category_href = list_item.contents[0].attrs['href']
                        category_url = INDEX + category_href
                        category_name = list_item.contents[0].text.strip()
                        this_category = (category_name, category_url)
                        urls_by_category[heading].append(this_category)
    # turn into a regular dict
    return dict(urls_by_category)


def get_prices(url, delay_s=1.5):
    """
    For a given URL, extract price information

    :param url: url for a page under www.pcgs.com/prices/detail/...
    :param delay_s: seconds to sleep to avoid response status 429, 1.5s worked
        in my testing, though I did not try any lower
    :return prices: a list of dictionaries representing each row in the table
    """

    # 1: prep for task
    time.sleep(delay_s)
    page = request_page(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    # 2: determine which grades we are dealing with in the table
    for grade_bin in BINS:
        if grade_bin in url:
            grades = grade_bin

    # 3: find the table
    table = soup.find('table', class_='table-main')
    if table is None:
        # some pages like counterstamped colonials have no price information,
        # would crash script otherwise
        return []

    # 4: loop through table elements and scrape prices
    prices = []
    for element in non_ns_children(table, 'children'):
        if element.name == 'tbody':
            for child in non_ns_children(element, 'children'):
                # table has lots of elements, but the ones which contain coin
                # prices are colored bg-pale and bg-light, this makes IDing
                # them a lot easier
                if 'class' in child.attrs:      # check if it has class attr
                    if 'bg-pale' in child.attrs['class'] \
                            or 'bg-light' in child.attrs['class']:
                        # each row has 13 cells with two possible internal rows
                        cells = non_ns_children(child, 'children')
                        row_prices = []     # to collect all prices in this row
                        for i, cell in enumerate(cells):
                            if i == 0:          # cell 0 is the pcgs number
                                pcgs_num = cell.text.strip()
                                if len(pcgs_num) == 0:
                                    pcgs_num = None
                            elif i == 1:        # cell 1 is the description
                                description = cell.text.strip()
                            elif i == 2:        # cell 2 is the designation
                                desig = cell.text.split()
                            elif 3 <= i <= 12:  # rest are prices
                                this_cell_prices = cell.text.strip('▲▼').split()
                                # always make prices cell a double for ease
                                # KNOWN ISSUE: in some rare cases, only one
                                # price is shown and appears in the bottom row
                                if len(this_cell_prices) == 0:
                                    this_cell_prices = (None, None)
                                elif len(this_cell_prices) == 1:
                                    this_cell_prices.append(None)
                                this_cell_prices = tuple(this_cell_prices)
                                row_prices.append(this_cell_prices)
                        # after each cell is scraped, turn into a dict & append
                        row = {
                            'pcgs_num': pcgs_num,
                            'description': description,
                            'desig': desig,
                            'grades': grades,
                            'prices': row_prices,
                            'url': url
                        }
                        prices.append(row)
    return prices


def scrape_all():
    """
    Entire scraping process in one call:
        Step 1: Load www.pcgs.com/prices and get all URL information
        Step 2: Load each URL and scrape prices from its table
        Step 3: Save price information to pickle
    """

    # Step 1
    print(f"Getting URLs from {PRICES}...")
    urls_by_category = get_urls(PRICES)
    print("Success!")

    # Step 2
    print("Scraping price data by category...")
    prices = []
    for i, (category, subcategories) in enumerate(urls_by_category.items()):
        print(f"\tBeginning category {i + 1}/{len(urls_by_category.items())}:"
              f" {category}")
        for subcat, subcat_url in tqdm(subcategories):
            for grade_bin in BINS:
                # url defaults to most-active page first, but we want all the
                # grade information
                this_bin_url = subcat_url.replace('most-active', grade_bin)
                this_bin_url += '?pn=1&ps=-1'       # show all prices one page
                this_bin_prices = get_prices(this_bin_url, delay_s=1.0)
                prices.extend(this_bin_prices)
    print("Success!")

    # Step 3
    today = datetime.now()
    current_time = today.strftime("%d-%m-%Y-%H:%M:%S")
    filename = f'data/pcgs_prices_unprocessed-{current_time}.pkl'
    print(f"Saving price data to {filename}")
    pickle.dump(prices, open(filename, 'wb'))
    print(f"Success!")
    return filename


########################
# PROCESS SCRAPED DATA #
########################
def merge_grade_bins(filepath):
    """
    data from scrape_all is separated by grade_bins, combine into a single
    entry for each pcgs number

    The reason this is a separate function from the scrape function is to ensure
    that the scraped data is saved as soon as possible to avoid errors causing
    data loss after waiting for all the prices to be scraped

    :param filepath: path to scraped data pkl from scrape_all
    :return price_guide: (dict) lookup table for
    """
    # NOTE: there will be a lot of entries with a None pcgs_num, these are
    # typically the prices for full type sets of a certain coin on the price
    # detail page, which this script currently does not account for. To get
    # that information, capture the title of each subsection of the table and
    # you can relate it

    price_guide = {}

    scraped_data = pickle.load(open(filepath, 'rb'))
    by_pcgs_num = ft.indexBy('pcgs_num', scraped_data)

    for pcgs_num, entries in by_pcgs_num.items():
        if pcgs_num is None:
            continue        # see above comment

        # 1: merge price information into a single dict that points from # to $
        assert len(entries) == 3, 'Something went wrong, more than 3 bins'
        # make absolutely certain that prices are in the correct order, overkill
        temp_order = [None, None, None]
        desigs = []
        for entry in entries:
            desigs.append(entry['desig'])       # save desig for step 2
            if entry['grades'] == 'grades-1-20':
                temp_order[0] = entry['prices']
            elif entry['grades'] == 'grades-25-60':
                temp_order[1] = entry['prices']
            elif entry['grades'] == 'grades-61-70':
                temp_order[2] = entry['prices']
        this_num_prices = []        # prices for this pcgs number
        for grade_bin in temp_order:
            for price in grade_bin:
                this_num_prices.append(price)
        assert len(this_num_prices) == len(GRADES), \
            f'Wrong number of grades for PCGS#{pcgs_num}: ' \
            f'{len(this_num_prices)}'
        price_by_grade = dict(zip(GRADES, this_num_prices))

        # 2: Ensure that the desig is always two place if at least one is
        merged_desig = []       # start with len == 0
        for desig in desigs:
            if len(desig) > len(merged_desig):   # longest desig wins
                merged_desig = desig

        merged_entry = {
            'pcgs_num': pcgs_num,
            'desig': merged_desig,
            'prices': price_by_grade,
            'merged_from': entries,
        }
        price_guide[pcgs_num] = merged_entry

    print('Saving price guide to pkl and json files...')
    pickle.dump(price_guide, open('data/scraped_pcgs_prices.pkl', 'wb'))
    with open('data/scraped_pcgs_prices.json', 'w') as outfile:
        json.dump(price_guide, outfile)


def main():
    save_file = scrape_all()
    merge_grade_bins(save_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', '-a', action='store_true',
                        help="scrape all coin prices, create lookup table")
    parser.add_argument('--scrape_only', '-s', action='store_true',
                        help="only scrape coin prices and save unprocessed "
                             "file")
    parser.add_argument('--process', '-p', action='store',
                        help="process only, specify path to .pkl file to "
                             "process and create lookup table from")

    args = parser.parse_args()

    if args.all is True:
        main()
    elif args.scrape_only is True:
        scrape_all()
    elif args.process is not None:
        merge_grade_bins(args.process)
    else:
        print('Please specify an option. Documentation available at '
              'https://github.com/ryanamannion/pcgs_prices')
