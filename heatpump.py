from machine import UART
global uart
uart = UART(1, 9600)
uart.init(9600,bits = 8,parity = 0,stop = 1,rx = 32,tx = 33,)

from umqtt.simple import MQTTClient
import uasyncio as asyncio
import time
from time import sleep
import machine
import hpfuncs



# exec(open('./nyser.py').read(),globals())
topic_prefix = "varmepumpe"

mqtt_server = '192.168.2.30'
client_id ='hpesp32-1'
topic_sub_setp = b"varmepumpe/setpoint"
topic_sub_state = b"varmepumpe/controlstate"
topic_sub_doinit = b"varmepumpe/doinit"
topics = [topic_sub_setp, topic_sub_state, topic_sub_doinit]





def int_to_signed(intval):
    if intval > 127:
        return (256-intval) * (-1)
    else:
        return intval






#mqtt stuff
def sub_cb(topic, msg):
    runwrite = True

    print(topic, msg)
    if topic == topic_sub_setp:
        try:
            values = hpfuncs.setpointVal(msg)
        except Exception as e:
            runwrite = False
            
    elif topic == topic_sub_state:
        try:
            values = hpfuncs.stateControl(msg)
        except Exception as e:
            runwrite = False
    elif topic == topic_sub_doinit:
        myvals = hpfuncs.queryall()
        print("initial read")
        for i in myvals:
            uart.write(bytearray(i))
            sleep(0.2)
        
        print("initial read done")
        runwrite = False

    if runwrite == True:
        print(values)
        uart.write(values)
        


def connect_and_subscribe():
    try:
        global client_id, mqtt_server, topic_sub
        client = MQTTClient(client_id, mqtt_server)
        client.set_callback(sub_cb)
        client.connect()
        client.subscribe(topic_sub_setp)
        client.subscribe(topic_sub_state)
        client.subscribe(topic_sub_doinit)
        
        print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, str(topics)))
        return client
    except Exception as e:
        print("sender: ", e)

def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(10)
    #machine.reset()

try:
    client = connect_and_subscribe()
except Exception as e:
    print("start av connect_and_subscribe: ", e)
    restart_and_reconnect()


async def sender():
    try:
        while True:
            client.check_msg()
            await asyncio.sleep(1)
    except Exception as e:
        print("sender: ",e )        

async def firstrun():
    firstrun = False
    await asyncio.sleep(5)
    if firstrun == False:
        client.publish('varmepumpe/doinit', "firstrun")
        print("running firstrun")
        firstrun = True


async def receiver():
    
    sreader = asyncio.StreamReader(uart)
    try:
        while True:
            data = await sreader.read(17)
            if data is not None:
                #print(data)
                formdata = ""
                for i in data:
                    formdata = formdata + str(int(i)) + " "
                print(formdata)
                print(len(data))
                
                if len(data) > 12:
                    client.publish('varmepumpe/debug/fullstring', str(data))
                    #client.publish('varmepumpe/debug/nummer12', str(data[12]))
                    if len(data) == 17:
                        if(str(data[14]) == "187"):
                            roomtemp = int_to_signed(int(data[15]))
                            client.publish('varmepumpe/roomtemp', str(roomtemp), retain=True, qos=1)
                        if(str(data[14]) == "179"):
                            setpoint = int(data[15])
                            client.publish('varmepumpe/setpoint', str(setpoint), retain=True, qos=1)
                        if(str(data[14]) == "128"):
                            onoff = int(data[15])
                            client.publish('varmepumpe/onoff', str(onoff), retain=True, qos=1)
                        if(str(data[14]) == "160"):
                            fanmode = int(data[15])
                            client.publish('varmepumpe/fanmode', str(fanmode), retain=True, qos=1)
                        if(str(data[14]) == "163"):
                            swingmode = int(data[15])
                            client.publish('varmepumpe/swingmode', str(swingmode), retain=True, qos=1)
                        if(str(data[14]) == "176"):
                            mode = int(data[15])
                            client.publish('varmepumpe/mode', str(mode), retain=True, qos=1) 
                        if(str(data[14]) == "190"):
                            print("her er utetemp: ")
                            print(str(data[15]))
                            outdoortemp = int_to_signed(int(data[15]))
                            client.publish('varmepumpe/outdoortemp', str(outdoortemp), retain=True, qos=1)
                    elif len(data) == 15:
                        if(str(data[12]) == "190"):
                            outdoortemp = int_to_signed(int(data[13]))
                            client.publish('varmepumpe/outdoortemp', str(outdoortemp), retain=True, qos=1)
                        elif(str(data[12]) == "187"):
                            roomtemp = int_to_signed(int(data[13]))
                            client.publish('varmepumpe/roomtemp', str(roomtemp), retain=True, qos=1)        
    except Exception as e:
        print("reciever: " , e)
        restart_and_reconnect()


loop = asyncio.get_event_loop()
loop.create_task(receiver())
loop.create_task(sender())
loop.create_task(firstrun())
loop.run_forever()