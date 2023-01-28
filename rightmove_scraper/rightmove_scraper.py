from datetime import date
from pathlib import Path
from tqdm import tqdm 

import pandas as pd
from bs4 import BeautifulSoup

from rightmove_scraper.support_functions import (url_to_html, string_to_int, 
    sqm_from_string, sqft_from_string, save_image)

from rightmove_scraper.database_setup import engine

HOME_PATH = Path.home()

class RightmoveScraper:


    def __init__(self, buy:bool=True):
        self.mode = 'SALE' if buy else 'LET'
        self.region_mode = 'sale' if buy else 'rent'
        self.date = date.today()

        self.done = []

        pd.read_sql(f"""
            delete table rightmove_data where date = {self.date};
            delete table rightmove_features where date = {self.date};
            """)


    def scrape_regions(self, regions:list, save=True, verbose=True):
        for ind, region in enumerate((pbar := tqdm(regions, disable=not verbose))):
            # try: 
            pbar.set_description(f'{region}, {ind}')
            if ind == 0:
                region_attributes = self.scrape_region(region, save, False)
            else:
                these_attributes = self.scrape_region(region, save, False)
                if these_attributes is not None:
                    region_attributes = pd.concat([region_attributes, these_attributes]) 
        print('Done!')
        # return region_attributes.reset_index(drop=True)
        


    def scrape_region(self, region:str, save=True, verbose=True):
        attributes_list = []
        page_n = 0
        if verbose: print(f'scraping {region} properties')
        while True:
            property_ids = self.get_property_ids(region, page_n)
            if len(property_ids) == 0:
                break
            page_attributes_df, feature_dict = self.scrape_id_list(property_ids)
            page_attributes_df["REGION"] = region
            page_attributes_df["MODE"] = self.mode
            page_attributes_df["DATE"] = self.date
            if 'TENURE' in page_attributes_df.columns:
                page_attributes_df.drop('TENURE', axis=1, inplace=True)
            if 'PROPERTY TYPE' in page_attributes_df.columns:
                page_attributes_df.rename({'PROPERTY TYPE': 'TYPE'}, axis=1, inplace=True)
            
            if 'SIZE AVAILABLE' in page_attributes_df.columns:
                page_attributes_df.drop('SIZE AVAILABLE', axis=1, inplace=True)
                
            if 'SECTOR' in page_attributes_df.columns:
                page_attributes_df.drop('SECTOR', axis=1, inplace=True)

            if save:
                with engine.begin() as con:
                    page_attributes_df.to_sql('rightmove_data', con, 
                        if_exists='append', index=False)

                with engine.begin() as con:
                    for key, value in feature_dict.items():
                        features = pd.DataFrame(data=value, columns=['FEATURE'])
                        features['ID'] = key
                        features['DATE'] = self.date
                        features.to_sql('rightmove_features', con, 
                            if_exists='append', index=False)
            del page_attributes_df, features, feature_dict
    

    def get_property_ids(self, region:str, page_n:int):

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
        feature_dict = {}
        for property_id in property_ids: 
            if property_id not in self.done:
                try:
                    individual_attributes, feature_dict[property_id] = self.scrape_attributes(property_id)
                    attributes_list.append(individual_attributes)
                except AttributeError:
                    pass
        attributes_df = pd.DataFrame(attributes_list).reset_index(drop=True)
        return attributes_df, feature_dict 


    def scrape_attributes(self, property_id):
        
        self.done.append(property_id)
        property_url = f"https://www.rightmove.co.uk/properties/{property_id}#/?channel=RES_{self.mode}"
        soup = url_to_html(property_url)
        info_reel = soup.find("div", {"data-test": "infoReel"})
        property_info = {i.string: ii.string for i, ii in zip(info_reel.findAll('dt'), info_reel.findAll('dd'))}
        features = [i.string for i in soup.findAll('article')[3].findAll('ul')[0]]
        # for i in info_reel.findAll('div', recursive=False):
        #     category_key = i.find('div').string
        #     category_values = [p.string for p in i.findAll('p')]
        #     if (len(category_values) == 1) & (category_key == 'SIZE'):
        #         property_info['SIZE SQFT'] = sqft_from_string(category_values[0])
        #     elif (len(category_values) == 2) & (category_key == 'SIZE'):
        #         property_info['SIZE SQFT'] = sqft_from_string(category_values[0])
        #         property_info['SIZE SQM'] = sqm_from_string(category_values[1])
        #     elif ((len(category_values) == 1) 
        #             & ((category_key == 'BEDROOMS') | (category_key == 'BATHROOMS'))):
        #         property_info[category_key] = string_to_int(category_values[0])
        #     elif len(category_values) == 1:
        #         property_info[category_key] = category_values[0]
            
        price = soup.findAll("article")[1].findAll("span")[0].string
        
        try: 
            property_info['PRICE'] = string_to_int(price)
        except ValueError:
            property_info['PRICE'] = None
        
        for category in ['BEDROOMS', 'BATHROOMS', 'SIZE']:
            try:
                property_info[category] = string_to_int(property_info[category])
            except KeyError:
                pass
        property_info['LINK'] = property_url
        property_info['ID'] = property_id        
        return property_info, features
 
