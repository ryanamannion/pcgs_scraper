# pcgs_scraper: Tools for scraping coin data from PCGS

![pcgs_scraper_logo](pcgs_logo_and_scraper.png)

Scrape current PCGS coin prices from https://www.pcgs.com/prices and save them to a lookup table for easy price lookup 
or other manipulation

This repo is not sponsored or endorsed by PCGS. Logo for stylistic purposes, following PCGS Brand Guidelines

## Requirements:

- BeautifulSoup4: web scraping
- ft: free table utilities

`$ pip install beautifulsoup4 ft`

## Design and Functionality

### `pcgs_scraper.py`

`pcgs_scraper.py` is the main file in this library, and handles the dispatching of the scraping scripts. Additionally, this file handles postprocessing of those scraping scripts.

Running it from the command line calls the cli() function.
The interface prompts the user to download the necessary files if they have not been scraped already. It will download
both the PCGS#-->Description information from www.pcgs.com/pcgsnolookup as well as the PCGS#-->Price information from
www.pcgs.com/prices. 

`pcgs_scraper.py` then postprocesses that data and combines them to create a data-rich free table
(list of dictionaries) where each list item represents a coin. The free table has details about each coin, including the PCGS Number, Year, Denomination, Mint Mark (if applicable), Detail information (e.g. Full Bands or other details relevant to that particular coin), Price data at time of scraping, and metadata for the purposes of debugging (e.g. the URL it was
scraped from, etc.). 

Please note, during this step entries from the price data which do not have a description from the number data are 
excluded. These are mostly type coins, as well as type sets and other subsets of coins which can be given a valuation.

The final free table is saved to `data/pcgs_price_guide.{pkl, json}`, based on what the user selects in the CLI

### `pcgs_prices.py`

The first step in creating the price guide is to scrape the prices from www.pcgs.com/prices. 

The PCGS coin prices website is a labyrinth of html. This script first navigates to https://www.pcgs.com/prices, where
it navigates through each category (e.g. Type Coins, Half-Cents and Cents, etc.) and saves urls for each subcategory. 
The script then follows each subcategory URL and scrapes all price information from the table, including the PCGS# as
well as the prices for each grade. The website divides the grades into different pages, or bins of grades: 1-20, 25-60,
and 61-70. That means that for each subcategory there are three pages to scrape data from. (Note: I skip the 
"Most Active" page because it is redundant).

In order to ensure that a rogue error at a later step won't cause the user to lose all the data from scraping, which can
take some time, the data is saved to a pickle file at the end of the preliminary scraping function, and before the 
processing step that combines the data from the three bins into one lookup table. 
This file is saved in the pcgs_scraper directory using the date and time upon
completion to name the file `data/pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl`. This file serves as the input to the 
processing function, which merges rows with the same PCGS# to creates the lookup table. It can be used any time with the 
`-p` command line option to be reprocessed should you need historical price data

The processing function saves the price data both as a pickle file and as a json file (because why not). These  files are saved to the same directory and named `data/scraped_pcgs_prices.{json, pkl}`

The resulting data structure is a dictionary. The keys are the PCGS Numbers, and the values are 
data extracted from the tables. 
- pcgs_num: (str) PCGS Number
- desig: (str) Designation (More info: https://www.pcgs.com/news/a-look-at-pcgs-designations)
- prices: (dict) Price by grade, each grade points to a tuple (n=2) of prices (each a str). The top price in the table 
  is index 0, the bottom is index 1. See Known Issues #1
- merged_from: the three entries for each grade bin used to create this merged entry (see paragraph one of this 
  section), retained for debugging purposes

```python
merged_entry = {
            'pcgs_num': pcgs_num,       # PCGS Number
            'desig': merged_desig,      # Designation (BN, RB, RD)
            'prices': price_by_grade,   # Price dictionary {Grade: [Price, Price+]}
            'merged_from': entries,     # History for merge, for debugging
        }
price_guide[pcgs_num] = merged_entry
```

### `pcgs_nums.py`

The second step in creating the price guide is to scrape the mappings of PCGS Numbers to detailed descriptions, which
adds high quality information about a coin's year, mint mark, denomination, and other details. This script uses the same
function from `pcgs_prices.py` to scrape URLs from the main page of the PCGS# lookup page by category and subcategory.
Each subcategory URL is then followed and the number:description pair is scraped and stored in a free table and saved to
`number_data.pkl`.


### `pcgs_query.py`

One a user has compiled the `pcgs_price_guide.pkl` binary, it can be queried from the command line with:

`$ python pcgs_query.py -q '1909-S VDB Wheat Cent'` 

or similar inputs. The query function uses some regex to determine the necessary elements of the query: the year and
denomination. It can then also find the mint mark (specified with -M where M stands for mint) to help narrow down
the search. Once the search algorithm has a target year and denomination (and possibly mint), it will rank the
results by Levenshtein Edit Distance from the user-generated input string. The user can then simply choose from the 
results list (if there are more than one option) and the price data will be displayed.

**Here are some general query guidelines:**

1. Always specify a year
2. Always specify a denomination
  * Can be of the form 1C, 3CS, 3 cent silver, $1, Dollar, half dollar, $2.50 etc.
3. If you want to specify a mint mark, do so with a hyphen following the year, e.g. `-q '1909-S VDB Cent'`


## Detailed Usage Notes:

### Setup and Basic Usage

1. Clone the repository to the directory of your choice with `$ git clone https://github.com/ryanamannion/pcgs_prices.git`
2. Navigate to the pcgs_scraper subdirectory
3. If you are using a venv or other environment, activate it
4. `$ pip install beautifulsoup4 ft`
5. `$ python pcgs_scraper.py`
6. `$ python pcgs_query.py -q '1909-S VDB Cent'`

### Running `pcgs_prices.py`
1. To show help dialogue: `$ python pcgs_prices.py --help`
2. To scrape all prices and clean up the data: `$ python pcgs_prices.py --all`
3. To just scrape data, create new unprocessed data binary: `$ python pcgs_prices.py --scrape_only`
    * This will save a file called `pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl` with the current date and time
4. To just turn unprocessed binary into a lookup table: `$ python pcgs_prices.py --process path/to/pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl`
    * This saves two files: `pcgs_price_guide.{json, pkl}`, both are of the same object 
    
### Running `pcgs_nums.py`

`pcgs_nums.py` has no CLI options. Running `$ python pcgs_nums.py` will download the number data and save it to 
`number_data.pkl`

### Running `pcgs_query.py`

1. Specify a query with `-q`
2. Specify a source price_guide binary with `-p`

## Known Issues and Future Changes:

1. Cases where there is only one price, and it is for the + designation are stored in the first place of the price 
   double
3. Most coin detail pages have MS as well as PR and sometimes other designations on a different page. Currently, only 
   the MS prices are scraped. The other will be implemented shortly, it helps that they have different PCGS 
   numbers
