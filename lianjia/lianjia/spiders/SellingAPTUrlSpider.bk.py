import datetime
import json
import logging
import math
import os
import random
import time

import scrapy
from bs4 import BeautifulSoup
import re
from lianjia.items import CrawlUrlItem
from decimal import *

from lianjia.pipelines.Sql import Sql


class SellingAPTUrlSpider(scrapy.Spider):
    name = "SellingAPTUrlSpider"
    custom_settings = {
        'ITEM_PIPELINES': {
            'lianjia.pipelines.pipelines.CrawlUrlPipeLine': 1
        }
    }
    base_url = "https://m.lianjia.com"

    headers_list = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "m.lianjia.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1"
    }
    headers_ajax = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Host": "m.lianjia.com",
        "Referer": "https://m.lianjia.com/gz/ershoufang/",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1",
        "X-Requested-With": "XMLHttpRequest"
    }

    def start_requests(self):
        url_list = ['https://m.lianjia.com/gz/ershoufang/panyu/',
                    'https://m.lianjia.com/gz/ershoufang/zengcheng/']
        base_url = 'https://m.lianjia.com/gz/ershoufang/co32pg1rs%s/'
        area_list = Sql.get_community_by_area('番禺')
        for area in area_list:
            time.sleep(random.random() + 0.5)
            url = base_url % area[1]
            yield scrapy.Request(url=url, headers=self.headers_list, callback=self.parse, meta={'rawurl': url_list[0]})

        area_list = Sql.get_community_by_area('增城')
        for area in area_list:
            time.sleep(random.random() + 0.5)
            url = base_url % area[1]
            yield scrapy.Request(url=url, headers=self.headers_list, callback=self.parse, meta={'rawurl': url_list[1]})

    def parse(self, response):
        total_num = int(re.findall('data-info="total=(.*)"', response.text)[0])
        ret = Sql.get_crawl_url_total_num2('lianjia', 'selling_apt', response.meta['rawurl'], response.url,
                                           datetime.datetime.now().strftime('%Y-%m-%d'))
        if int(ret[0]) >= int(total_num):
            logging.info("当天url已爬取完毕，不需要再爬取，来源有【%s】条，已爬取【%s】条【%s】" % (total_num, ret[0], response.url))
        else:
            logging.info("开始爬取，来源有【%s】条，已爬取【%s】条【%s】" % (total_num, ret[0], response.url))
            item_list= self.get_apt_url(response)
            for li in item_list:
                yield li
            max_num = math.ceil(total_num / 30)
            base_url = response.url
            for num in range(2, int(max_num) + 1):
                url = base_url.replace('co32pg1', 'co32pg' + str(num))
                hd = self.headers_list
                hd["referer"] = url
                time.sleep(random.random() + 0.5)
                yield scrapy.Request(url=url, callback=self.get_apt_url, headers=hd,
                                     meta={'rawurl': response.meta['rawurl']})

    def get_apt_url(self, response):
        list = BeautifulSoup(response.body, "html.parser").find_all("a", {'class': 'a_mask post_ulog post_ulog_action'})
        item_list = []
        for a in list:
            com_url = self.base_url + a.get('href')
            item = CrawlUrlItem()
            item['id'] = re.findall('/(\d*)\.html', com_url)[0]
            item["crawl_date"] = datetime.datetime.now().strftime('%Y-%m-%d')
            item["crawl_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            item["source"] = "lianjia"
            item["url"] = com_url
            item["type"] = "selling_apt"
            item["rawurl"] = response.meta['rawurl']
            item["rawurl2"] = response.url
            item["rawurl3"] = ''
            item["rawurl4"] = ""
            item["status"] = 0
            item["error_count"] = 0
            item_list.append(item)
        return item_list
