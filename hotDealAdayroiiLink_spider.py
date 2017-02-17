import scrapy


class HotDealTikiSpider(scrapy.Spider):
    name = "tikiLink"
    start_urls = ["https://deal.adayroi.com/deal-gia-soc-lp18",]
    def parse(self, response): 
        hotDealsElms = "adr items deal-list"        
        linkElms = "a::attr(href)"
        titleElms = "div img::attr(title)"
        imgElms = "div img::attr(data-src)"           
        for deal in response.css(hotDealsElms):
            if deal.css(linkElms).extract_first() == None:
                break            
            yield{ 'link' : deal.css(linkElms).extract_first(), }
            