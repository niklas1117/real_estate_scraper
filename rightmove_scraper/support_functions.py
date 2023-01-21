import requests 
from PIL import Image
from bs4 import BeautifulSoup

    
def url_to_html(url):
    # returns html soup
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    return soup 


def get_regions():
    url = "https://www.rightmove.co.uk/london-popular-regions.html"
    soup = url_to_html(url)
    regions =  []
    for li in soup.findAll("div", {"class": "primarycontent"})[0].findAll("li"):
        regions.append(li.find("a").string)
    regions = [i.split(' property')[0] for ind, i in enumerate(regions) if ind%3 == 0]
    regions = ['-'.join(i.split(' ')) for i in regions]
    return regions

def string_to_int(s):
    return int(''.join(i for i in s if i.isdigit()))

def sqm_from_string(s):
    first_clean = s.split('(')[1].split(' sq')[0]
    if (first_clean.isnumeric()) or (len(first_clean.split(',')) == 2):
        return string_to_int(first_clean)
    else:    
        return f'work on this = {s}'

def sqft_from_string(s):
    first_clean = s.split(' sq')[0]
    if (first_clean.isnumeric()) or (len(first_clean.split(',')) == 2):
        return string_to_int(first_clean)
    else:    
        return f'work on this - {s}'

def save_image(property_id, url, folder):
    try:
        im = Image.open(requests.get(url, stream=True).raw)
        im.save(f'{folder}/{property_id}.png')
    except OSError:
        pass
# def get_image(property_id):
#     link = RightmoveScraper().image_directory
#     Image.open()
