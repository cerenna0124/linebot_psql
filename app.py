from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import psycopg2
import datetime

#======python的函數庫==========
import  os
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# PSQL URL
db_url=os.getenv('DB_URL')

# PSQL COMMAND
def sql_selectall():
    query='select * from line_bot'
    conn=psycopg2.connect(db_url)
    cursor=conn.cursor()
    cursor.execute(query)
    data=cursor.fetchall()
    conn.commit()
    data=[list(i) for i in res]
    data=[[' | '.join(x)] for x in res]
    return data

def sql_insert(msg):
    t=datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    query=f"insert into line_bot (message,receive_datetime) values('{msg}','{t}')"
    conn=psycopg2.connect(db_url)
    cursor=conn.cursor()
    cursor.execute(query)
    conn.commit()
    
def sql_del_all():
    query="delete from line_bot"
    data_length=len(sql_selectall())
    conn=psycopg2.connect(db_url)
    cursor=conn.cursor()
    cursor.execute(query)
    conn.commit()
    return data_length

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    sql_insert(eval(body.replace('false','False')))
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

#======Postgresql======
# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if '@對話紀錄' in msg:
        datas = sql_selectall()
        text_list=[]
        for each in datas:
          if '@' not in each:
            text_list.append(each)
        data_text = '\n'.join(text_list)
        message = TextSendMessage(text=data_text)
        line_bot_api.reply_message(event.reply_token, message)

    elif '@刪除' in msg:
        records_len = sql_del_all()
        message = TextSendMessage(text=f'Delete {records_len} records')
        line_bot_api.reply_message(event.reply_token, message)

    elif '我起床了' in msg:
        message=TextSendMessage(text='你起床了!')
        line_bot_api.reply_message(event.reply_token, message)

    else:
        message = TextSendMessage(text=msg)
        line_bot_api.reply_message(event.reply_token, message)

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
