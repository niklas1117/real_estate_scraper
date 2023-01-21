from datetime import date
from pathlib import Path
from tqdm import tqdm 

import pandas as pd
from bs4 import BeautifulSoup

from rightmove_scraper.support_functions import (url_to_html, string_to_int, 
    sqm_from_string, sqft_from_string, save_image)

HOME_PATH = Path.home()

class RightmoveScraper:


    def __init__(self, buy:bool=True):
        self.mode = 'SALE' if buy else 'LET'
        self.region_mode = 'sale' if buy else 'rent'
        self.date = date.today().strftime('%Y_%m_%d')

        directory = 'sale_data' if buy else 'rent_data' 
        self.directory = Path.joinpath(HOME_PATH, f"rightmove/{directory}")
        self.directory.mkdir(parents=True, exist_ok=True)

        self.image_directory = Path.joinpath(HOME_PATH, 'rightmove/images')
        self.image_directory.mkdir(parents=True, exist_ok=True)

    def scrape_regions(self, regions:list, save=True, verbose=True):
        for ind, region in enumerate((pbar := tqdm(regions, disable=not verbose))):
            # try: 
            pbar.set_description(region)
            if ind == 0:
                region_attributes = self.scrape_region(region, save, False)
            else:
                these_attributes = self.scrape_region(region, save, False)
                region_attributes = pd.concat([region_attributes, these_attributes]) 
        #     attributes_list.append(region_attributes)
        #         ## maybe cancel somehow if condition?
        #     # except: 
        #     #     pass
        # attributes_df = pd.concat(attributes_list).reset_index(drop=True)
        print('Done!')
        return region_attributes.reset_index(drop=True)
        


    def scrape_region(self, region:str, save=True, verbose=True):
        attributes_list = []
        page_n = 0
        if verbose: print(f'scraping {region} properties')
        while True:
            property_ids = self.get_property_ids(region, page_n)
            if len(property_ids) == 0:
                break
            page_attributes_df = self.scrape_id_list(property_ids)
            page_attributes_df["region"] = region
            attributes_list.append(page_attributes_df)
            if verbose: print(f'page {page_n+1}')
            page_n += 1        
            
        attributes_df = pd.concat(attributes_list)
        if save: 
            attributes_df.to_excel(f'{self.directory}/{region}_{self.region_mode}_{self.date}.xlsx')
        return attributes_df


    def get_property_ids(self, region:str, page_n:int):

        ## try except stuff for non existant pages
        index = page_n*24
        region_url = f"https://www.rightmove.co.uk/property-for-{self.region_mode}/{region}.html?index={index}&"
        soup = url_to_html(region_url)
        try:
            cards = soup.find(id = "l-searchResults")
            property_ids = []
            for card in cards.findAll("div", {"class":"l-searchResult"}):
                property_ids.append(card["id"].split('-')[1])
            property_ids = property_ids[1:] ## ignore the first 
            property_ids = [id for id in property_ids if id != '0'] ## drop non existant ones
        except AttributeError:
            property_ids = []
        return property_ids


    def scrape_id_list(self, property_ids):
        attributes_list = []
        for property_id in property_ids: 
            try:
                individual_attributes = self.scrape_attributes(property_id)
                attributes_list.append(individual_attributes)
            except AttributeError:
                pass
        attributes_df = pd.DataFrame(attributes_list).reset_index(drop=True)
        return attributes_df


    def scrape_attributes(self, property_id):
        
        property_url = f"https://www.rightmove.co.uk/properties/{property_id}#/?channel=RES_{self.mode}"
        soup = url_to_html(property_url)
        
        info_reel = soup.find("div", {"data-test": "infoReel"})
        property_info = {}
        for i in info_reel.findAll('div', recursive=False):
            category_key = i.find('div').find('div').string
            category_values = [p.string for p in i.findAll('p')]
            if (len(category_values) == 1) & (category_key == 'SIZE'):
                property_info['SIZE SQFT'] = sqft_from_string(category_values[0])
            elif (len(category_values) == 2) & (category_key == 'SIZE'):
                property_info['SIZE SQFT'] = sqft_from_string(category_values[0])
                property_info['SIZE SQM'] = sqm_from_string(category_values[1])
            elif ((len(category_values) == 1) 
                    & ((category_key == 'BEDROOMS') | (category_key == 'BATHROOMS'))):
                property_info[category_key] = string_to_int(category_values[0])
            elif len(category_values) == 1:
                property_info[category_key] = category_values[0]
            
        price = soup.findAll("article")[1].findAll("span")[0].string
        
        try: 
            property_info['PRICE'] = string_to_int(price)
        except ValueError:
            property_info['PRICE'] = None

        property_info['LINK'] = property_url
        property_info['ID'] = property_id

        image_url = soup.find('link', {'rel': 'canonical'}).find('meta', {'property':'og:image'})['content']
        save_image(property_id, image_url, self.image_directory)
        
        # all together
        return property_info

 
