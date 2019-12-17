
import scrapy
import csv

from datetime import datetime, timedelta

import dateutil.parser


class OpBase(scrapy.Spider):
	name = "default_name"
	allowed_domains = ["oddsportal.com"]

	check_output_before_scrape = False

	start_urls = []
	search_to_date = None

	parse_season_paging = True

	def parse(self, response):

		seasons = response.css('div.main-menu2.main-menu-gray ul.main-filter li a')

		for season in seasons:

			url = response.urljoin(season.xpath('@href').extract_first())
			year = int(season.xpath('text()').extract_first()[:4])

			if year >= (self.search_to_date.year-1):
				print ("yielding request to process season %s" % year)
				yield scrapy.Request(url, callback=self.parse_season, priority=-1, dont_filter=True)


	def parse_season(self, response):

		parse_season_paging = True

		league = response.xpath("//div[@id='breadcrumb']//a[last()]/text()").extract_first()

		for match in response.css("tr[xeid]"):

			inplay = match.css("td.table-participant a[href*='inplay']")
			if inplay: 
				print ("ignoring inplay game")
				continue

			match_epoch = match.css("td.table-time::attr(class)").extract_first()
			match_date = self.extract_date_from_class(match_epoch)
			# print("md, me", match_epoch, match_date)

			team_name_nodes = match.css("td.table-participant *::text").extract()
			# print(team_name_nodes)
			team_names = ''.join(team_name_nodes)
			# print(team_names)
			team1 = team_names.split(" - ")[0].strip()
			team2 = team_names.split(" - ")[1].strip()
			# print(f"parsing match list, match: {match_date}, {team1}, {team2}")

			if self.sport_match_url_key == "mlb" and match_date.month < 4:
				# hack to avoid scraping pre-season
				continue

			if match_date < self.search_to_date:
				# print ("breaking upon search to date rule", match_date, self.search_to_date)
				# parse_season_paging = False
				continue

			if self.search_from_date >=  match_date > self.search_to_date:

				if self.check_output_before_scrape and self.is_match_in_csv_output(match_date, team1, team2, self.sport_match_url_key=="mlb"): 
					print("match already is in the output, skip scraping")
					continue

				for anchor in self.season_url_anchors:

					match_url = response.urljoin(match.css("td.table-participant  a[href*='{}']".format(self.sport_match_url_key)).xpath('@href').extract_first() + anchor)
					print ("match found, url is: %s " % match_url)
					request = scrapy.Request(match_url, self.parse_match_data)
					yield request

		pagination = response.css('#pagination')
		if not pagination: return

		active_page = int(pagination.css('span.active-page::text').extract_first())
		last_page = int(pagination.xpath('//a[last()]/@x-page').extract_first())

		print (">>>>>>>>>>-----------------------------------------------")
		print ("active page %s / last page %s, do paging %s " % (active_page, last_page, parse_season_paging))

		if active_page < last_page and parse_season_paging:
			next_page_url = pagination.css("a[x-page='%i']::attr('href')" % int(active_page+1)).extract_first()
			url = response.urljoin(next_page_url)
			print ("next pagination url is: %s " % url)
			yield scrapy.Request(url, callback=self.parse_season, dont_filter=True)


	def change_team_name(self, input_name, season_year=None):
		# season year can be used where a team changes its name between seasons

		if input_name in self.team_names:
			return self.team_names[input_name]
		return input_name


	def extract_date_from_class(self, class_string):

		first_point = class_string.find(" t")
		epoch_string = class_string[first_point+2:first_point+2+10]
		epoch_value = float(epoch_string)
		match_date = datetime.fromtimestamp(epoch_value)
		return match_date

	def is_match_in_csv_output(self, match_date, team1, team2, us=False):
		csv_output_filename = self.settings.attributes['FEED_URI'].value

		if us:
			# US only
			match_date = match_date - timedelta(hours=5)

		with open(csv_output_filename, 'r') as csvfile:
			csvreader = csv.reader(csvfile, delimiter=',')

			print(f">>> looking for: {match_date}, {team1}, {team2}")

			for row in csvreader:
				if row[1] == "date":
					continue
				# use dateutil because it can deal with short and long years
				row_date = dateutil.parser.parse(row[1], dayfirst=True)
				if us:
					row_team1 = row[3].strip()
					row_team2 = row[2].strip()
				else:
					row_team1 = row[2].strip()
					row_team2 = row[3].strip()

				# if row_date > datetime(year=2019, month=10, day=1):
					# print(f"{match_date} {row_date} and {team1} == {row_team1} and {team2} == {row_team2}")
				# print(f"{timedelta(hours=-2) < (match_date - row_date) < timedelta(hours=2)} and {team1 == row_team1} and {team2 == row_team2}")

				if (match_date == row_date) and team1 == row_team1 and team2 == row_team2:
					print(f"{match_date}, {team1}, {team2} match found, returning true")
					return True

				# break the loop if row/search date is past the search date
				# to speed things up a bit
				if (row_date - match_date) > timedelta(days=3): break


		return False
