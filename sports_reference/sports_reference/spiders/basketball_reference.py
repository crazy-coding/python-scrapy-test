# -*- coding: utf-8 -*-
import scrapy
from scrapy.item import Item

from datetime import datetime

from scrapy_splash import SplashRequest

import base64
import time


class BasketballReferenceSpider(scrapy.Spider):

	# must start splash first
	# sudo docker run -p 8050:8050 scrapinghub/splash

	name = 'basketball_reference'
	allowed_domains = ['www.basketball-reference.com']

	# start and end ate in which to scrape through. 
	# format is (year, month, day)
	start_date = datetime(2019, 10, 1)
	end_date = datetime(2019, 12, 1)


	team_total_stats = ['fg', 'fga', 'fg3', 'fg3a', 'ft', 'fta', 'orb', 'drb', 'trb', 'ast', 'stl', 'blk', 'tov', 'pf']

	wait_for_total_script = """
		function main(splash)

			splash:wait(10)

	  		-- requires Splash 2.3  
	  		while splash:select("table#line_score tbody tr") do
	    		splash:wait(1)
	  		end

	  		return {html=splash:html()}
		end
	"""

	splash_request_args = {"lua_source": wait_for_total_script, 'timeout': 60, 'wait': 5, 'User-Agent':"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36", 'render_all': 1, 'width': 1440}

	def start_requests(self):
		start_urls = ['https://www.basketball-reference.com/leagues/NBA_{0}_games.html'.format(year) for year in range(self.start_date.year+1, self.end_date.year+2)]
		for url in start_urls:
			yield SplashRequest(url, self.parse)


	def parse(self, response):
		
		months = response.css('.filter a')

		for month in months:
			month_url = response.urljoin(month.xpath('@href').extract_first())
			yield scrapy.Request(url=month_url, callback=self.parse_month)

	def parse_month(self, response):

		# box_scores = response.css("#schedule tbody td[data-stat='box_score_text'] a")
		match_rows = response.css("#schedule tbody tr:not(.thead)")

		print("matches found", len(match_rows))

		for row in match_rows:
			match_date_string = row.css("th[data-stat='date_game'] a::text").extract_first()
			match_date = datetime.strptime(match_date_string, '%a, %b %d, %Y')

			bs_link = row.css("td[data-stat='box_score_text'] a")
			bs_url = response.urljoin(bs_link.xpath('@href').extract_first())

			print(match_date_string, match_date, bs_url)

			if self.start_date < match_date <= self.end_date and 'leagues' not in bs_url:
				print("yielding request", bs_url)
				yield SplashRequest(url=bs_url, callback=self.parse_box_score, args=self.splash_request_args)


	def parse_box_score(self, response):

		data_item = {}

		away_team_scorebox = response.css('.scorebox div:nth-of-type(1)')
		home_team_scorebox = response.css('.scorebox div:nth-of-type(2)')

		game_date_string = response.css('.scorebox .scorebox_meta div::text').extract_first()
		game_start_datetime = datetime.strptime(game_date_string, '%I:%M %p, %B %d, %Y')
		data_item['start_time'] = game_start_datetime.strftime('%d/%m/%Y %H:%M')

		away_team_name = away_team_scorebox.css('strong a::text').extract_first()
		home_team_name = home_team_scorebox.css('strong a::text').extract_first()
		data_item['away_team_name'] = away_team_name
		data_item['home_team_name'] = home_team_name

		scoring_table = response.css('table#line_score')

		scoring_table_header = scoring_table.css('tbody tr.thead th')
		away_ht = 0
		home_ht = 0
		away_ft = 0
		home_ft = 0
		away_ot = 0
		home_ot = 0

		if scoring_table:

			scoring_table_rows = response.css('table#line_score tr')

			# iterate over the columns to get the scores of each period
			for i, score_header in enumerate(scoring_table_header):
				# skip the first column
				if i == 0: continue

				header_text = score_header.css('::text').extract_first()

				if header_text == "T": break

				away_score = scoring_table_rows[2].css("td:nth-of-type(%s)::text" % (i+1)).extract_first()
				home_score = scoring_table_rows[3].css("td:nth-of-type(%s)::text" % (i+1)).extract_first()

				if not away_score:
					continue

				away_score = int(away_score)
				home_score = int(home_score)

				if header_text in ['1', '2']:
					away_ht += away_score
					home_ht += home_score

				if header_text in ['1', '2', '3', '4']:
					away_ft += away_score
					home_ft += home_score

				away_ot += away_score
				home_ot += home_score

		data_item['away_ht'] = away_ht
		data_item['home_ht'] = home_ht
		data_item['away_ft'] = away_ft
		data_item['home_ft'] = home_ft
		data_item['away_ot'] = away_ot
		data_item['home_ot'] = home_ot

		away_team_basic_statbox = response.css("table[id^='box-'][id*='game-basic']")[0]
		home_team_basic_statbox = response.css("table[id^='box-'][id*='game-basic']")[1]

		away_team_basic_stat_team_total = away_team_basic_statbox.css('tfoot')
		home_team_basic_stat_team_total = home_team_basic_statbox.css('tfoot')

		for side in ['a', 'h']:
			for key in self.team_total_stats:
				value = ""
				stat_table = away_team_basic_stat_team_total if side == 'a' else home_team_basic_stat_team_total

				if stat_table:
					value = stat_table.css("td[data-stat='%s']::text" % key).extract_first()

				data_item[side + '_' + key] = value

		yield data_item
