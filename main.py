from rightmove_scraper import RightmoveScraper, get_regions

regions = get_regions()

rms = RightmoveScraper(buy=True)
rms.scrape_regions(regions, save=True, verbose=True)

rms = RightmoveScraper(False)
rms.scrape_regions(regions, save=True, verbose=True)