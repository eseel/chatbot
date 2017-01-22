# -*- coding: utf-8 -*-

import os
import sys
import json
import threading # temporizador 
import datetime
import requests
import psycopg2
from flask import Flask, request

# verify_token  webhook
VERIFY = "VERIFY"

# access_token
TOKEN = "TOKEN"


app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    #log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":
        
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                
                sender_id = messaging_event["sender"]["id"]
                recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                
                if messaging_event.get("message"):  # someone sent us a message
                    message_text = messaging_event["message"]["text"]  # the message's text
                    
                    if message_text == "farmacologia":
                        send_message(sender_id, "area de farmacologia")
                        
                    elif message_text == "ag":
                        #schedule_reply()
                        pass
                        
                    else:
                        send_message(sender_id, message_text)
                    
                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message     POSTBACK FUNCIONAL! ()
                    postback = messaging_event["postback"]
                    
                    res_postback(sender_id, postback)
                    
                    
    return "ok", 200



  
@app.route('/test', methods=['POST'])
def rq():
    data = request.get_json()
    #log(data['recipient']['id'])
    
    sender_id = data['recipient']['id']

    elements  = []
    
    for drug in data['lets_take']:
        elements += {
                    "title": drug['name'],
                    "image_url": drug['img'],
                    "subtitle": drug['trademark'],
                    "default_action": {
                        "type": "web_url",
                        "url": "https://anastasia-eseele.c9users.io/",
                        "messenger_extensions": "true",
                        "webview_height_ratio": "tall",
                        "fallback_url": "https://anastasia-eseele.c9users.io/"
                    },
                    "buttons": [
                        {
                            "title": "Informar           ",
                            "type": "postback",
                            "payload": drug['id_postback']+":"+drug['name']                       
                        }
                    ]
                },
    
    params = {
        "access_token": TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    
        
    data = {
    "recipient":{
    "id": sender_id
    }, "message": {
    "attachment": {
        "type": "template",
        "payload": {
            "template_type": "list",
            "top_element_style": "compact",
            "elements": elements
        }
    }
    }
    }
    
    data = json.dumps(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/" + "messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    
    
    return "ok", 200




def res_postback(sender_id, postback):
    try:
        conn = psycopg2.connect("dbname='dbname' user='user' host='ip' password='pass' port='port'")
    except:
        print "I am unable to connect to the database"
    
    cur = conn.cursor()
    print postback["payload"] 
    
    if postback["payload"] == "payload_1":
        generic_reply(sender_id)
    """
    if postback["payload"] == "payload_conf":
        #printit() # TEST DEL TEMPORIZADOR
        print "temporizador apagado..."
    """    
    if "ltk" in postback["payload"] and "taken" not in postback["payload"] and "nottake" not in postback["payload"]: # SI EL STRING DEL PAYLOAD CONTIENE EL PREFIJO LTK
        rep1 = postback["payload"]
        rep2 = rep1.replace('ltk', '')
        #print rep2
        quick_reply(sender_id, rep2)
    #if "yes" in postback["payload"] and "ltk" not in postback["payload"]: 
    if "taken" in postback["payload"]:
        
        tak1 = postback["payload"]
        tak2 = tak1.replace('taken', '')
        print tak2
        
        try:
            cur.execute("UPDATE notifications SET status = 'taken' WHERE consultation="+tak2)
            conn.commit()
            cur.close()
        except:
            print "ERROR IN UPDATE"
        
        send_message(sender_id, "informado")

    #if "no" in postback["payload"] and "ltk" not in postback["payload"]: 
    if "nottake" in postback["payload"]: 
        tak1 = postback["payload"]
        tak2 = tak1.replace('nottake', '')
        print tak2
        
        try:
            cur.execute("UPDATE notifications SET status = 'nottake' WHERE consultation="+tak2)
            conn.commit()
            cur.close()
        except:
            print "ERROR IN UPDATE"
        send_message(sender_id, "informado")

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    #if r.status_code != 200:
        #log(r.status_code)
        #log(r.text)

"""
def schedule_reply():
    now = datetime.datetime.now()
    #log(now)
        
    with open('file_data.json') as data_file:
        file_data = json.load(data_file)
        #log(file_data)
            
    for (key, value) in file_data.items():
        if(key == "next_notification"):
            file_data[key] = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
        if(key == "interval_notification"):
            temp = datetime.datetime.strptime(value, '%H:%M:%S')
            interval_notification = datetime.timedelta(hours = temp.hour, minutes=temp.minute, seconds=temp.second)
        
    update_data = False
        
    if((now - file_data["next_notification"]).total_seconds() > 0):
        
        send_message(file_data["receipient_id"], file_data["message"]);
        
        file_data["next_notification"] = now + interval_notification
        
        update_data = True
        
    #update this in db
    if(update_data == True):

        with open('file_data.json','w') as data_write:
            json.dump(file_data, data_write, default=json_serial_datetime);
"""

"""
def finish_schedule(sender_id): # pasar id del agendamiento y senderid por parámetros  FAIL 
    with open('file_data.json') as data_file:
        file_data = json.load(data_file)
        
    if file_data["receipient_id"] == sender_id:
        threading.Timer(1.0, printit).cancel()
"""


def quick_reply(sender_id, drug_schedule): # Envía el mensaje de Si y No
    #print drug_schedule

    drug_name = drug_schedule.split(":",1)[1] # seleccionamos el nombre del producto
    pbid = drug_schedule.split(":",-2)[-2] # seleccionamos el string antes de los :
    
    drug_message = "Tomaste "+drug_name +"?"
    
    yes = "taken"+pbid
    no = "nottake"+pbid
    
    params = {
        "access_token": TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient":{
            "id":sender_id
        },
        "message":{
            "attachment":{
                "type":"template",
                "payload":{
                    "template_type":"button",
                    "text":drug_message,
                    "buttons":[
                        {
                            "type":"postback",
                            "title":"Si                 ",
                            "payload":yes
                        },
                        {
                            "type":"postback",
                            "title":"No             ",
                            "payload":no
                        }
                    ]
                }          
            }
        }
    }
    data = json.dumps(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/" + "messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        #log(r.status_code)
        log(r.text)

def generic_reply(sender_id): #template que se envía al usuario cuando clickean en farmacología
    params = {
        "access_token": TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "id": sender_id
        },
        "message":{
            "attachment":{
              "type":"template",
              "payload":{
                "template_type":"generic",
                "elements":[
                  {
                    "title":"Bienvenido al area de farmacología",
                    "item_url":"http://www.toth.life",
                    "image_url":"https://yt3.ggpht.com/-mIzD8p85W_g/AAAAAAAAAAI/AAAAAAAAAAA/jsP7nz8OxUQ/s900-c-k-no-mo-rj-c0xffffff/photo.jpg",
                    "subtitle":"Aquí puedes agendar tu consumo de medicamentos!",
                    "buttons":[
                      {
                        "type":"web_url",
                        "url":"https://anastasia-eseele.c9users.io/?user="+ sender_id +"&scheduling=1",
                        "title":"Agendar en web"
                      },
                      {
                        "type":"postback",
                        "title":"Agendar en chat",
                        "payload":"payload_conf"
                      }              
                    ]
                  }
                ]
              }
            }
        }
    }
    data = json.dumps(data)
    r = requests.post("https://graph.facebook.com/v2.6/me/" + "messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)



def log(message):
    print str(message)
    sys.stdout.flush()


def json_serial_datetime(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial + 'Z'
    raise TypeError ("Type not serializable")

""" la función printit se ejecuta cada 1 segundos, por lo que schedule_reply se ejecuta cada 1 segundo.
Como schedule_reply tiene un intervalo definido de 10 segundos, en los otros 9 segundos no se enviarán mensajes  

def printit():
  threading.Timer(1.0, printit).start()
  schedule_reply()

#printit()
"""

if __name__ == '__main__':
    app.run(host=os.getenv('IP', '0.0.0.0'),port=int(os.getenv('PORT', 8080)))
