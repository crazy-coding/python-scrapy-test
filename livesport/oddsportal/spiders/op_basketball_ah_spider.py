# -*- coding: utf-8 -*-

import scrapy

from op_base import OpBase
from mixins.basketball_mixin import BasketballMixin

from datetime import datetime


class Oddsportal_Basketball_Ah(OpBase, BasketballMixin):

	name = "oddsportal_basketball_ah"
	allowed_domains = ["oddsportal.com"]
	start_urls = [
		"https://www.oddsportal.com/basketball/usa/nba/results/"
	]

	# Remember to install geckodriver/chromedriver for running on webdriver

	# these dates search backwards
	search_from_date = datetime(2019, 12, 4)
	search_to_date = datetime(2019, 10, 1)

	sport_match_url_key = 'nba'
	season_url_anchors = ['#ah;1']
	

	def parse_match_data(self, response):
		# css selector for match table item
		league = response.xpath("//div[@id='breadcrumb']//a[last()]/text()").extract_first()
		season_year_index = league.find(" ")+1
		print("league name", league, season_year_index)
		
		if season_year_index > 0:
			season_year = int(league[season_year_index:league.find("/")])
		else:
			season_year = ""

		teams = response.css("#col-content h1::text").extract_first().split(" - ")

		raw_datestamp = response.css("#col-content p.date::text").extract_first()
		date_string = raw_datestamp[raw_datestamp.find(",")+1: raw_datestamp.rfind(",")].strip()
		match_date = datetime.strptime(date_string, '%d %b %Y')

		hcap_rows = response.css('div.table-container')

		for hcap_row in hcap_rows:
			handicap_type = hcap_row.css('a::text').extract_first()

			if handicap_type == None or "asian handicap" not in handicap_type.lower() : continue

			if "asian handicap" in handicap_type.lower():

				price_rows = hcap_row.xpath("table/tbody//tr[contains(@class,'lo')][td]")

				for price_row in price_rows:
					
					deactivate = price_row.css("div.deactivateOdd")
					if len(deactivate) > 0: continue

					bookmaker = price_row.css("a.name::text").extract_first()
					
					if  "bet365" in bookmaker.lower() or "pinnacle" in bookmaker.lower():

						item = {}
						item['league'] = league
						item['date'] = match_date.date()

						item['away_team'] = self.change_team_name(teams[1].strip(), season_year)
						item['home_team'] = self.change_team_name(teams[0].strip(), season_year)
						item['handicap_value'] = 0 - float(price_row.css("td:nth-of-type(2)::text").extract_first())
						item['away_odds'] = price_row.css("td:nth-of-type(4) div::text").extract_first()
						item['home_odds'] = price_row.css("td:nth-of-type(3) div::text").extract_first()
						item['bookmaker'] = bookmaker
						yield item

