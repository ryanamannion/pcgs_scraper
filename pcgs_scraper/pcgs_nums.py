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

from pcgs_scraper.utils import non_ns_children, request_page
from pcgs_scraper.pcgs_prices import get_urls

URL = "https://www.pcgs.com"
URL_NOLOOKUP = "https://www.pcgs.com/pcgsnolookup/"


def scrape_coinfacts(url):
    """

    :param coinfacts_url:
    :return:
    """
    time.sleep(2)
    page = request_page(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    images_html = soup.find_all('img')
    filtered_images = []
    for image_html in images_html:
        if 'alt' not in image_html.attrs.keys():
            continue
        alt = image_html.attrs['alt']
        if "logo" in alt:
            continue        # no logos
        if "PCGS" in alt:
            filtered_images.append(image_html)
    # images = all images of the coin on this page
    # image = the large one on the page, i.e. the first one in the html
    images = [(i.attrs['data-src'], i.attrs['alt'].strip()) for i in filtered_images]
    if len(images) != 0:
        image = images[0]
    else:       # no images on page
        images = None
        image = None
    narrative_html = soup.find(id="sectionNarrative")
    if narrative_html is None:
        narrative = None
    else:
        narrative = narrative_html.text
    return {'image': image, 'images': images, 'narrative': narrative}


def scrape_nums(url, delay_s=25):
    """
    Scrape PCGS numbers from a single given pcgs.com/pcgsnolookup url

    :param url: (str) url to pcgsnolookup page
    :param delay_s: time to wait to avoid error code 429
        this means that each subcategory will wait delay_s num of seconds
    :return rows: (list(dict)) free table of all rows containing pcgs_nums on
        this page
    """
    time.sleep(delay_s)
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
                        coinfacts_url = URL + cell.contents[0].attrs['href']
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
            coinfacts = scrape_coinfacts(coinfacts_url)
            row_cells = {
                'pcgs_num': pcgs_num,
                'desig': designation,
                'description': description,
                'coinfacts_url': coinfacts_url,
                'image': coinfacts['image'],
                'images': coinfacts['images'],
                'narrative': coinfacts['narrative']
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
        print(f"\tStarting Category {i+1}/{len(urls.items())}: {category}...")
        for subcat_name, subcat_url in tqdm(subcategories):
            time.sleep(1.0)
            subcat_data = scrape_nums(subcat_url)
            all_data.extend(subcat_data)
    print('Done with PCGS Number Data! Saving...')

    pickle.dump(all_data, open('data/number_data.pkl', 'wb'))

    print('Saved to data/number_data.pkl')


if __name__ == "__main__":
    main()
