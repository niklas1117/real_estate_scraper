from rightmove_scraper import RightmoveScraper, get_regions

regions = get_regions()[26:]

rms = RightmoveScraper(buy=True)
rms.scrape_region('Hackney', save=True, verbose=True)

# rms = RightmoveScraper(False)
# df = rms.scrape_regions(regions, save=True, verbose=True)
# print(df)
