# -*- coding: utf8 -*-
from flask import Flask, jsonify
from flask import request
from flask import render_template
from flask import send_from_directory
import os 
import requests
import json
import logging
import string
import sys,json
import whoosh.index
from whoosh.index import open_dir
from whoosh.query import *
from whoosh.qparser import MultifieldParser
from whoosh.qparser import SequencePlugin
from whoosh.qparser import PhrasePlugin 
import datetime
import boto3

app = Flask(__name__, static_url_path='/static')
 
ACCESS_TOKEN = "EAADuyQw39OEBAI6HnfE2ZCEHvZCCoAptumQBt4NAoM7jXyMinlNR51ZACYf5xhgQOS3tEb8Bgq9H5XTPD2gWdsnzl7gA6nZAlZBrpPfLZBab8ZBotCAnmZCzo4K1llq1jXIZCy0ZB8xzZCZAxHQBKUpAzZBYA64cw6U2NL9mio3o3wKUhiAZDZD"
REPLY_URL = "https://graph.facebook.com/v2.8/me/messages?access_token="

loggingFORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='todaySaleChatBotDEBUG.log', level=logging.DEBUG, format=loggingFORMAT)
logging.basicConfig(filename='todaySaleChatBotINFO.log', level=logging.INFO, format=loggingFORMAT)
linkDeals = ['tiki.vn','lazada.vn']

def reduceKeyword(keyword):
	_keyword = ''
	stoplist = [u'tôi',u'muốn',u'mua',u'tìm',u'cho',u'bạn']
	for s in stoplist:
		keyword = string.replace(keyword,s,'')
	_keyword = string.replace(keyword,'  ','')
	return _keyword


def search(keyword):
	logging.debug('searching for: %s ... ',keyword.split())
	"""Search deal from indexed file"""
	ix = open_dir('C:\crawlData\indexed')
	"""Open indexed file"""
	qp =  MultifieldParser(["title", "link"], schema=ix.schema)
	# qp.remove_plugin_class(PhrasePlugin)
	# qp.add_plugin(SequencePlugin("!(~(?P<slop>[1-9][0-9]*))?"))	
	# qp.add_plugin(PhrasePlugin(expr='"(?P<text>.*?)"(~(?P<slop>[1-9][0-9]*))?'))
	q = qp.parse(keyword)
	with ix.searcher() as s:
		results = s.search(q, limit=10)
		items = '['	
		for hit in results:
			items = (items + '{"title":"' 
					+ string.replace(hit['title'],'\n',' ') 
                                        + '","link":"' + hit['link']
                                        + '","pSale":"' + string.replace(hit['pSale'],'\n',' ')
                                        + '","pRegular":"' + string.replace(hit['pRegular'],'\n',' ')
                                        + '","img":"' + hit['img'] + '"},')

			# print('matched term: ',hit.matched_terms())
		items = items[0:len(items)-1] + ']'
		# print(items)
	return items
def reply(user_id, keyword):	
        rKeyword = reduceKeyword(keyword)
	message_data = {
                "recipient": {"id": user_id},
                "message": {"text": "Chúng tôi đang tìm kiếm, bạn vui lòng đợi giây lát"}
        }
        requests.post(REPLY_URL + ACCESS_TOKEN,json=message_data)	
	
	message_data = {
		"recipient": {"id": user_id},
		"message": {"text": u'Không có \"' + rKeyword + u'\" nào đang giảm giá.\nLưu ý: Bạn chỉ việc nhập tên sản phẩm muốn tìm,\nVí dụ: Iphone 7 128GB'}
	}
	"""Set default data if no item onsale then send this"""
	try:
		items = json.loads(search(rKeyword))
	except ValueError:		
		requests.post(REPLY_URL + ACCESS_TOKEN, json=message_data)
		"""If no item onsale, sending no item available"""
		logging.debug('Reply no item onsale  to \'%s\'', str(user_id))
		"""Logging"""
		return
	messageText = ''
	messageText = (str(len(items))
                                        + u' sản phẩm \"' 
					+ rKeyword 
					+ u'\" đang khuyến mãi.'
					+ u' Xem nhiều hơn tại: \n https://todaysales.info')
	requests.post(REPLY_URL + ACCESS_TOKEN, json={"recipient":{"id":user_id},
													"message":{
													"text": messageText }})
	"""Sending number of item onsale"""
	messageData = '{"attachment":{"type":"template","payload":{"template_type":"generic","elements":['
	for item in items:
                matchLink = ''
                for link in linkDeals:
                    if(link in item['link']):
                        matchLink = link
		messageData = (messageData 
						+ u'{"title":"'
						+ string.replace(item['title'],'\n',' ')
                                                + u'","subtitle":"Giá gốc: ' + string.replace(item['pRegular'],' ','')
                                                + u'                            Giảm giá: ' + string.replace(item['pSale'],' ','')
                                                + u'tại: ' + str(matchLink)
                                                + u'","image_url":"' 
						+ item['img'] 
						+ u'","buttons":[{"type":"web_url","url":"' 
						+ item['link'] 
						+ u'","title":"Chi tiết"}]},') 
	messageData = messageData[0:len(messageData)-1]
	messageData = messageData + u']}}}'
	#logging.debug(messageData)
	replyMessage = {
    	"recipient": {"id": user_id},
    	"message": json.loads(messageData)
	}
	requests.post(REPLY_URL + ACCESS_TOKEN, json=replyMessage)
	"""Sending item onsale with title and link"""
	logging.debug('Replied items ref to: \'%s\'', str(user_id))
		
def simpleReply(user_id, message):
    logging.debug('Simple Reply to %s',str(user_id))
    """Logging"""
    message_data = {
        "recipient": {"id": user_id},
        "message": {"text": message}
    }
    #for char in message:
    requests.post(REPLY_URL + ACCESS_TOKEN,json=message_data)
 


@app.route('/chatbots', methods=['POST','GET'])

def handle_incoming_messages():	
    logging.debug(request)
    #print(request)
    data = request.json
    
    if data != None:
    	try:
            user_id = data['entry'][0]['messaging'][0]['sender']['id']
            """Getting the id of sender"""
            message = unicode(data['entry'][0]['messaging'][0]['message']['text'])
            """Getting message sent from sender"""
            logging.debug('Recieved: ' + message + ' from id:' + user_id )
    #         if user_id == '1193835397339070':
    #         	requests.post(REPLY_URL + ACCESS_TOKEN, 
    #         		json={"recipient":{"id":user_id},
    #         				"message":{"text": ('Hi boss,' 
    #         					+' I\'m collecting info for you, please wait.')}})
    #         elif user_id == '1620821934600986' or user_id == '9350013332670640':
				# requests.post(REPLY_URL + ACCESS_TOKEN, json={"recipient":{"id":user_id},"message":{"text": 'Cho ti, bo may dang tim...'}})
            #logging.warning('Recieved \'%s\' from \'%s\'',message,str(user_id))       
            """Logging"""                 
            # reply(user_id, message)            
            """Reply sender with item onsale"""            
            reply(user_id, message)
            #simpleReply(user_id, message)
        except KeyError as e:	
            if e == 'message':
                pass
        return '200'
    else:
    	#startIndex = len('<Request \'https://todaysales.info/py/server.py?hub.mode=subscribe&hub.challenge=')
    	"""Return challenge for validate webhook"""
        #return str(request)[startIndex:startIndex+10]
    	if request.args['hub.challenge'] != None:
            return request.args['hub.challenge']
        else:
    	    return '200'
#----Start Today Sales Website ------  
@app.route('/')
def home():
    
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/policy')
def policy():
    return render_template('policy.html')

@app.route('/tos')
def tos():
    return render_template('tos.html')

@app.route('/favicon.ico') 
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/favicon.ico')

#----End Today Sales Website----------

#----Start Web API--------------------
 
@app.route('/api/v1.0/products', methods=['GET'])
def products():
    
    """File name is deals_ + datetime with YearMonthDay"""
    daystr = datetime.date.today().strftime('%Y%m%d')
    filename = 'deals_'+daystr+'.jl'
    rootFolder = 'C:\crawlData\\'

    fullFilePath = rootFolder+filename

    """Download deals from S3""" 
    client = boto3.client(
        's3',
        # Hard coded strings as credentials, not recommended.
        aws_access_key_id='AKIAI7AS42P37KNXDXTA',
        aws_secret_access_key='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'
    )
    client.download_file('home-deals', 'deals/'+ filename, fullFilePath)
    
    # signed_url = client.generate_presigned_url('get_object',Params={'Bucket':'home-deals','Key':'deals/'+filename},ExpiresIn=300)
    # return jsonify({'products': signed_url})

    products =[]
    with open(fullFilePath) as file:			
        for line in file:
            try:
               products.append(line) 
            except ValueError as e:
                continue 

    return jsonify({'products': products})
    
#----End Web API--------------------
 
if __name__ == '__main__':
    app.run()
