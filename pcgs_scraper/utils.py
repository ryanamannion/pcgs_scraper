#!/usr/bin/env python3
"""
utils.py

utils for scraping

Author: Ryan A. Mannion, 2020
github: ryanamannion
twitter: @ryanamannion
"""
import sys
import time
import requests

from bs4.element import NavigableString


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
        time.sleep(retry_after + 2)     # for good measure
        print("Retrying...")
        request_page(page_url)
    elif not response.status_code == 200:
        print(f'Something went wrong with {page_url}!\n'
              f'Status code: {response.status_code}\n'
              f'Status text:\n' + response.text)
        sys.exit()
    else:
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
            if type(child) is not NavigableString:
                filtered.append(child)
    elif search_type == 'descendants':
        for child in tag.descendants:
            if type(child) is not NavigableString:
                filtered.append(child)
    return filtered
