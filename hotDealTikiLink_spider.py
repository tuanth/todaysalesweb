import scrapy


class HotDealTikiSpider(scrapy.Spider):
    name = "tikiLink"
    start_urls = ["https://tiki.vn/hot",]
    def parse(self, response): 
        hotDealsElms = "div.deal-block.broadcast-banner div.col-sm-6.padding-8"        
        linkElms = "a::attr(href)"
        titleElms = "div img::attr(title)"
        imgElms = "div img::attr(data-src)"           
        for deal in response.css(hotDealsElms):
            if deal.css(linkElms).extract_first() == None:
                break            
            yield{ 'link' : deal.css(linkElms).extract_first(), }
            