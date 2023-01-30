from rightmove_scraper import RightmoveScraper, get_regions

regions = get_regions()

rms = RightmoveScraper(buy=True, delete=True) # run all regions sales, delete all 
rms.scrape_regions(regions, save=True, verbose=True)

rms = RightmoveScraper(False, delete=False) # run all regions lets
rms.scrape_regions(regions, save=True, verbose=True)