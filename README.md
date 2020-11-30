# pcgs_scraper: Tools for scraping coin data from PCGS

Scrape current PCGS coin prices from https://www.pcgs.com/prices and save them to a lookup table for easy price lookup 
or other manipulation

## Requirements:

- BeautifulSoup4: web scraping
- ft: free table utilities

## Design and Functionality

### `pcgs_scraper.py`

`pcgs_scraper.py` is the main file in this library, and handles the dispatching of the scraping scripts contained in the
other two files in this library, discussed below. Additionally, this file handles postprocessing of the data which
results from the below-discussed files. 

The interface prompts the user to download the necessary files if they have not been scraped already. The two resulting
saved files `scraped_pcgs_prices.pkl` and `number_data.pkl` are combined into a single free table, with the detailed
descriptions from the number data filling in the more messy descriptions from the prices. 

The result is a free table with high quality details about each coin, including the PCGS Number, Year,
Denomination, Mint Mark (if applicable), Detail information (e.g. Full Bands or other details relevant to that
particular coin), Price data at time of scraping, and metadata for the purposes of debugging (e.g. the URL it was
scraped from, etc.). 

Please note, during this step entries from the price data which do not have a description from the number data are 
excluded. These are mostly type coins, as well as type sets and other subsets of coins which can be given a valuation.

The final free table is saved to `pcgs_price_guide.{pkl, json}`

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
completion to name the file `pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl`. It is a free table, or a list of dictionaries with 
each list item representing a row, and each key:value pair representing the column. This file serves as the input to the 
processing function, which merges rows with the same PCGS# to creates the lookup table. 
The processing function saves it both as a pickle file and as a json file (because why not). These  files are saved to 
the same directory and named `scraped_pcgs_prices.{json, pkl}`

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

NOTE: the description from the table is excluded in the final lookup table, it was too messy and I was under a
time crunch to get this done. My goal is to scrape the PCGS number data from pcgs.com to have better descriptions for
each PCGS# in the final lookup table, but for now that is not implemented. See Known Issues #2

## Detailed Usage Notes:

### Setup and Basic Usage

1. Clone the repository to the directory of your choice with `$ git clone https://github.com/ryanamannion/pcgs_prices.git`
2. Navigate to the pcgs_scraper subdirectory
3. If you are using a venv or other environment, activate it
4. `$ pip install beautifulsoup4 ft`
5. `$ python pcgs_scraper.py`

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

## Known Issues and Future Changes:

1. Cases where there is only one price, and it is for the + designation are stored in the first place of the price 
   double
3. Most coin detail pages have MS as well as PR and sometimes other designations on a different page. Currently, only 
   the MS prices are scraped. The other will be implemented shortly, it helps that they have different PCGS 
   numbers
