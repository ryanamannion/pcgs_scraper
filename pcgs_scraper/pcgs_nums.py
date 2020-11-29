#!/usr/bin/env python3
"""
pcgs_nums.py

this file contains a simple script for scraping the PCGS number data from
www.pcgs.com/pcgsnolookup

Author: Ryan A. Mannion, 2020
github: ryanamannion
twitter: @ryanamannion
"""
import time
import pickle
from tqdm import tqdm
from bs4 import BeautifulSoup

from utils import non_ns_children, request_page
from pcgs_prices import get_urls

URL = "https://www.pcgs.com"
URL_NOLOOKUP = "https://www.pcgs.com/pcgsnolookup/"


def scrape_nums(url):
    """
    Scrape PCGS numbers from a single given pcgs.com/pcgsnolookup url

    :param url: (str) url to pcgsnolookup page
    :return rows: (list(dict)) free table of all rows containing pcgs_nums on
        this page
    """
    page = request_page(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    table_rows = soup.find_all('tr')

    rows = []
    for table_row in table_rows:
        # add some variables to track progress
        number_row = True           # init value of flag is True
        all_cells_filled = False    # True once all 3 columns filled

        for cell in non_ns_children(table_row, 'children'):
            if number_row:  # since init is True, always runs first cell
                if 'data-title' in cell.attrs:
                    if 'PCGS #' in cell.attrs['data-title']:
                        number_row = True       # set flag true
                        pcgs_num = cell.text.strip()
                    elif 'Designation' in cell.attrs['data-title']:
                        designation = cell.text.strip()
                    elif 'Description' in cell.attrs['data-title']:
                        description = cell.text.strip()
                        all_cells_filled = True
                else:       # cell is not in a number row
                    number_row = False
                    # one non 'data-title' cell kills a row
                    # this should save time by not having to check each cell in
                    # a row we know does not contain data-title information,
                    # like a header

        if all_cells_filled:
            row_cells = {
                'pcgs_num': pcgs_num,
                'desig': designation,
                'description': description
            }
            rows.append(row_cells)

    return rows


def main():
    """
    scrape coin categories and their href urls from the main number lookup url,
    use those to scrape the PCGS numbers and other information for each type
    from each category's detail page. Save as pkl file
    """
    urls = get_urls(URL_NOLOOKUP)
    all_data = []
    print('Scraping PCGS Number Data...')
    for i, (category, subcategories) in enumerate(urls.items()):
        print(f"\tStarting Category {i+1}/{len(urls.itmes())}: {category}...")
        for subcat_name, subcat_url in tqdm(subcategories):
            time.sleep(1.0)
            subcat_data = scrape_nums(subcat_url)
            all_data.extend(subcat_data)
    print('Done with PCGS Number Data! Saving...')

    pickle.dump(all_data, open('number_data.pkl', 'wb'))

    print('Saved to number_data.pkl')


if __name__ == "__main__":
    main()
