# pcgs_prices: Tools for scraping coin price information

Scrape current PCGS coin prices from https://www.pcgs.com/prices and save them to a lookup table for easy price lookup or
other manipulation

### Requirements:

- BeautifulSoup4: web scraping
- ft: free table utilities

### Design and Functionality

The PCGS coin prices website is a labyrinth of html. This script first navigates to https://www.pcgs.com/prices, where
it navigates through each category (e.g. Type Coins, Half-Cents and Cents, etc.) and saves urls for each subcategory. 
The script then follows each subcategory URL and scrapes all price information from the table, including the PCGS# as
well as the prices for each grade. The website divides the grades into different pages, or bins of grades: 1-20, 25-60,
and 61-70. That means that for each subcategory there are three pages to scrape data from. (Note: I skip the 
"Most Active" page because it is redundant).

In order to ensure that a rogue error at a later step won't cause the user to lose all the data from scraping, which can
take some time, the data is saved to a pickle file at the end of the preliminary scraping function, and before the 
processing step that combines the data from the three bins into one lookup table. 
This file is saved in the pcgs_prices directory using the date and time upon
completion to name the file `pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl`. It is a free table, or a list of dictionaries with 
each key representing the header row, and each value representing that cell. This file serves as the input to the 
processing function, which merges rows with the same PCGS# to creates the lookup table. 
The processing function saves it both as a pickle file and as a json file (because why not). These 
files are saved to the same directory and named `pcgs_price_guide.{json, pkl}`

The data structure of the price guide lookup table is a dictionary. The keys are the PCGS Numbers, and the values are data extracted
from the tables. 
- pcgs_num: (str) PCGS Number
- desig: (str) Designation (More info: https://www.pcgs.com/news/a-look-at-pcgs-designations)
- prices: (dict) Price by grade, each grade points to a tuple (n=2) of prices (each a str). The top price in the table
is index 0, the bottom is index 1. See Known Issues #1
- merged_from: the three entries for each grade bin used to create this merged entry (see paragraph one of this section),
retained for debugging purposes

```python
merged_entry = {
            'pcgs_num': pcgs_num,       # PCGS Number
            'desig': merged_desig,      # Designation (BN, RB, RD)
            'prices': price_by_grade,   # Price dictionary {Grade: [Price, Price+]}
            'merged_from': entries,     # History for merge, for debugging
        }
price_guide[pcgs_num] = merged_entry
```

NOTE: the description from the table is excluded in the final lookup table, it was too messy and I was under a
time crunch to get this done. My goal is to scrape the PCGS number data from pcgs.com to have better descriptions for
each PCGS# in the final lookup table, but for now that is not implemented. See Known Issues #2

### Usage:

#### Setup

1. Clone the repository to the directory of your choice with `$ git clone https://github.com/ryanamannion/pcgs_prices.git`

2. Navigate to the pcgs_prices subdirectory

3. If you are using a venv or other environment, activate it

4. `$ pip install beautifulsoup4 ft`

#### Running
1. To show help dialogue: `$ python pcgs_prices.py --help`
2. To scrape all prices and clean up the data: `$ python pcgs_prices.py --all`
3. To just scrape data, create new unprocessed data binary: `$ python pcgs_prices.py --scrape_only`
    * This will save a file called `pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl` with the current date and time
4. To just turn unprocessed binary into a lookup table: `$ python pcgs_prices.py --process path/to/pcgs_prices-DD-MM-YYY-HH:MM:SS.pkl`
    * This saves two files: `pcgs_price_guide.{json, pkl}`, both are of the same object 

### Known Issues:

1. Cases where there is only one price, and it is for the + designation are stored in the first place of the price double
2. Descriptions are excluded from the final lookup table because they are too messy, but they are retained in the merged_from values
