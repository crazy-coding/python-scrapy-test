from scrapy.http import HtmlResponse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
import platform
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import logging

logging.getLogger('selenium.webdriver.remote.remote_connection').setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

urlNavTabLabels = {
	"#ah;1" : "FT including OT",
	"#ah;2" : "Full Time",
	"#1X2;2" : "Full Time",
	"#home-away;1" : "FT including OT",
	"#home-away;2" : "Full Time"
}

class WebDriverMiddleware(object):

	# this middleware uses Webdriver to load the page, navigate
	# to the required part of the page (activating the js/ajax/etc)
	# and then returns the raw source html

	driver = None
	browser_loops = 200

	def __init__(self):
		# if Rpi, restart after fewer loops
		if platform.machine() == "armv7l":
			self.browser_loops = 20


	def start_browser(self):
		firefox_capabilities = DesiredCapabilities.FIREFOX.copy()
		firefox_capabilities['marionette'] = True

		profile = webdriver.FirefoxProfile();
		profile.set_preference("privacy.trackingprotection.enabled", True);
		profile.set_preference("privacy.trackingprotection.ui.enabled", False);
		profile.set_preference("privacy.trackingprotection.introCount", 20);
		self.driver = webdriver.Firefox(firefox_profile=profile, capabilities=firefox_capabilities, timeout=240)
		self.load_counter = 0
		self.driver.implicitly_wait(20)


	def is_session_active(self):
		if self.driver:
			try:
				# there is a window
				return len(self.driver.window_handles) > 0
			except WebDriverException:
				return False

		# there is no driver
		return False

	def process_request(self, request, spider):

		print("<<<<<<<<<<<<<<<< requested URL", request.url)

		request_is_game = "results" not in request.url and "matches" not in request.url

		if not self.is_session_active():
			self.start_browser()

		# count the pages loaded then stop/start the browser
		# otherwise the ram usage will cripple the computer
		if self.load_counter > self.browser_loops:
			self.driver.quit()
			time.sleep(3)
			self.start_browser()	

		# if it's a paging url then quickly switch to a blank page so to avoid the ajax
		if "oddsportal.com" in self.driver.current_url:
			if "results/" in request.url:
				self.driver.get("about:blank")

			if self.driver.current_url in request.url:
				self.driver.get("about:blank")

		# this is to check if we are just navigating to a different tab of the same URL
		# in that case we can just stay on this page and return the html source again

		if request_is_game and self.driver.current_url.split(";")[0] == request.url.split(";")[0]:
			request_tab = "#" + request.url.split("#")[1]

			print(">>>>>>>>>>>> attempting to reload a different tab " + request_tab)
			print("looking for: " +  urlNavTabLabels[request_tab])

			all_butts = self.driver.find_elements(By.CSS_SELECTOR, "ul.sub-menu a")
			butt_found = False
			for butt in all_butts:
				print ("button text: " + butt.text)
				print (butt.text == urlNavTabLabels[request_tab])
				if butt.text.encode('utf-8') == urlNavTabLabels[request_tab]:
					butt.click()
					time.sleep(1)
					butt_found = True
					WebDriverWait(self.driver, 40).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '#event-wait-msg-main')))

			if butt_found == False:
				print ("----------  did not find the tab we need, returning 404")
				return HtmlResponse(url=self.driver.current_url, status=404)

		else:
			# now get the URL
			print("5555555555555555555 getting the url, finally")
			self.driver.get(request.url)
			time.sleep(1)
			WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.status-dot-green')))
			WebDriverWait(self.driver, 40).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '#event-wait-msg-main')))

			if request_is_game:

				requested_url_anchor = "#" + request.url.split("#")[1]
				actual_url_anchor = "#" + self.driver.current_url.split("#")[1]

				if requested_url_anchor != actual_url_anchor:
					print("Loaded the page but got redirected to a different anchor.. no good so just exit")
					return HtmlResponse(url=self.driver.current_url, status=404)


				print(" >>>>>>>>>>>> waiting for display submenu")
				WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sub-menu.subactive li.active strong span')))

				# is_ah = "ah;" in request.url
				# if is_ah:
				actual_url_anchor = "#" + self.driver.current_url.split("#")[1]

				displayed_submenu = self.driver.find_element(By.CSS_SELECTOR, '.sub-menu.subactive li.active strong span').text
				print ("-.-.-.-.-.-.-.-.-.-.-.- " + displayed_submenu)

				# if we haven't got the actual page that we want, return a 404
				if urlNavTabLabels[requested_url_anchor] != displayed_submenu:
					print ("we've loaded the page but the submenu we want isn't there")
					return HtmlResponse(url=self.driver.current_url, status=404)

		self.load_counter+=1

		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.status-dot-green')))

		# if any(s in spider.name for s in ["oddsportal_basketball", "oddsportal_baseball", "oddsportal_hockey"]):

		if '/usa/' in self.driver.current_url:

			WebDriverWait(self.driver, 40).until(EC.visibility_of_element_located((By.ID, 'user-header-timezone-expander')))
			timezone_setting = self.driver.find_element(By.ID, 'user-header-timezone-expander')
			if "GMT -4" not in timezone_setting.text and "GMT -5" not in timezone_setting.text:
				timezone_setting.click()
				us_et_tz = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="/set-timezone/15/"]')))
				us_et_tz.click()
				time.sleep(3)
				WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.status-dot-green')))

		# elif spider.name == "oddsportal_football_ah" or spider.name == "oddsportal_tennis_ah":
		else:

			WebDriverWait(self.driver, 40).until(EC.visibility_of_element_located((By.ID, 'user-header-timezone-expander')))
			timezone_setting = self.driver.find_element(By.ID, 'user-header-timezone-expander')
			if ("GMT +1" not in timezone_setting.text) and ("GMT 0" not in timezone_setting.text):
				timezone_setting.click()
				gmt_tz = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="/set-timezone/35/"]')))
				gmt_tz.click()
				time.sleep(3)
				WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.status-dot-green')))


		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.status-dot-green')))
		WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'user-header-oddsformat-expander')))

		odds_setting = self.driver.find_element(By.ID, 'user-header-oddsformat-expander')
		if odds_setting.text != "EU Odds":
			odds_setting.click()
			odds_el = self.driver.find_element(By.XPATH, '//a[span[text()="EU Odds"]]')
			odds_el.click()
			time.sleep(3)
			WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.status-dot-green')))

		# if asian handicap, go through and open up all the boxes
		if "ah;" in request.url:
			oddsRows = self.driver.find_elements(By.CSS_SELECTOR, 'div.table-container:not(.exchangeContainer)')
			oddsRows.reverse()
			for el in oddsRows:
				count = None
				try:
					count = el.find_element(By.CSS_SELECTOR, '.odds-cnt')
				except:
					continue

				if not count: continue
				if count.text == "(0)": continue

				compare = el.find_element(By.CSS_SELECTOR, '.odds-co a.more')
				if compare.is_displayed() and "Compare" in compare.text:
					compare.click()

		if request.url not in self.driver.current_url:
			print("ERROR page did not load ", request.url, self.driver.current_url)
			return HtmlResponse(url=self.driver.current_url, status=404)

		print("================ returning requested url", self.driver.current_url)
		body = self.driver.page_source
		response = HtmlResponse(url=self.driver.current_url, body=body, encoding='utf-8', request=request)
		return response

	def close_spider(self, reason):
		self.driver.quit()
