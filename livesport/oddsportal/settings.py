# Scrapy settings for oddsportal project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'oddsportal'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0'

DOWNLOADER_MIDDLEWARES = {
    'middlewares.WebDriverMiddleware': 543,
}
DOWNLOAD_DELAY = 0
CONCURRENT_REQUESTS = 1

HTTPERROR_ALLOWED_CODES = [404]