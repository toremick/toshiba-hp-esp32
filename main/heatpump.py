from main import hpfuncs
#import hpfuncs

from machine import UART
global uart
uart = UART(1, 9600)
uart.init(9600,bits = 8,parity = 0,stop = 1,rx = 32,tx = 33,timeout = 10, timeout_char=50)

from main.robust import MQTTClient
import uasyncio as asyncio
import time
from time import sleep
import machine

topic_prefix = "varmepumpe"
mqtt_server = '192.168.2.30'
client_id ='hpesp32-1'

topic_sub_setp = b"varmepumpe/setpoint/set"
topic_sub_state = b"varmepumpe/state/set"
topic_sub_fanmode = b"varmepumpe/fanmode/set"
topic_sub_swingmode = b"varmepumpe/swingmode/set"
topic_sub_mode =  b"varmepumpe/mode/set"
topic_sub_doinit = b"varmepumpe/doinit"
topics = [topic_sub_setp, topic_sub_state, topic_sub_doinit, topic_sub_fanmode, topic_sub_mode, topic_sub_swingmode]

def int_to_signed(intval):
    if intval > 127:
        return (256-intval) * (-1)
    else:
        return intval

#mqtt stuff
def sub_cb(topic, msg):
    runwrite = True
    hpfuncs.logprint(str(topic) + " -- " + str(msg))
################################################ 
#setpoint
    if topic == topic_sub_setp:
        try:
            values = hpfuncs.setpointVal(int(float(msg)))
        except Exception as e:
            hpfuncs.logprint(e)
            runwrite = False
################################################        
# state
    elif topic == topic_sub_state:
        try:
            values = hpfuncs.stateControl(msg)
            if values == False:
                runwrite = False
        except Exception as e:
            hpfuncs.logprint(e)
            runwrite = False
################################################        
# swingstate
    elif topic == topic_sub_swingmode:
        try:
            values = hpfuncs.swingControl(msg)
            if values == False:
                runwrite = False
        except Exception as e:
            hpfuncs.logprint(e)
            runwrite = False
################################################        
# mode
    elif topic == topic_sub_mode:
        try:
            values = hpfuncs.modeControl(msg)
            if values == False:
                runwrite = False
        except Exception as e:
            hpfuncs.logprint(e)
            runwrite = False
################################################
# fanmode
    elif topic == topic_sub_fanmode:
        try:
            values = hpfuncs.fanControl(msg)
            if values == False:
                runwrite = False
        except Exception as e:
            hpfuncs.logprint(e)
            runwrite = False
################################################
# do init
    elif topic == topic_sub_doinit:
        myvals = hpfuncs.queryall()
        hpfuncs.logprint("initial read")
        for i in myvals:
            uart.write(bytearray(i))
            sleep(0.2)
        hpfuncs.logprint("initial read done")
        runwrite = False
################################################ 
    if runwrite == True and values != False:
        #print(values)
        for i in values:
            hpfuncs.logprint("writing: " + str(i))
            uart.write(bytearray(i))
            sleep(0.2)

        
def chunkifyarray(vals):
    val_length = len(vals)
    start = 0
    rest_size = val_length
    myresult = []
    while rest_size > 14:
        lengde= int(vals[start+6])
        chunk_size = lengde + 8
        chunk_end = start + int(vals[start+6]) + 8
        myresult.append(vals[start:chunk_end])
        start = (start + chunk_size) 
        rest_size = rest_size - chunk_size
    return myresult

def connect_and_subscribe():
    try:
        global client_id, mqtt_server, topic_sub
        client = MQTTClient(client_id, mqtt_server)
        client.set_callback(sub_cb)
        client.connect()
        for i in topics:
            client.subscribe(i)
            hpfuncs.logprint("Subscribing to: " + str(i))
        hpfuncs.logprint("Connected to MQTT Server : " + str(mqtt_server))
        return client
    except Exception as e:
        hpcunfs.logprint(e)
        restart_and_reconnect()
       

def restart_and_reconnect():
    hpfuncs.logprint('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(10)
    machine.reset()

try:
    client = connect_and_subscribe()
except Exception as e:
    hpfuncs.logprint(e)
    restart_and_reconnect()


async def sender():
    try:
        while True:
            client.check_msg()
            await asyncio.sleep(1)
    except Exception as e:
        hpfuncs.logprint(e )        

async def firstrun():
    firstrun = False
    await asyncio.sleep(10)
    if firstrun == False:
        client.publish('varmepumpe/doinit', "firstrun")
        hpfuncs.logprint("init firstrun")
        firstrun = True


async def receiver():
    
    sreader = asyncio.StreamReader(uart)
    try:
        while True:
            serdata = await sreader.read(2048)
            if serdata is not None:
                readable = list()
                for i in serdata:
                    readable.append(str(int(i)))
                
                hpfuncs.logprint("length of data: " + str(len(readable)))
                
                chunks = chunkifyarray(readable)

                for data in chunks:
                    hpfuncs.logprint(data)
                    client.publish('varmepumpe/debug/fullstring', str(data))
                    if len(data) == 17:
                        if(str(data[14]) == "187"):
                            roomtemp = int_to_signed(int(data[15]))
                            client.publish('varmepumpe/roomtemp', str(roomtemp), qos=1)
                        if(str(data[14]) == "179"):
                            setpoint = int(data[15])
                            client.publish('varmepumpe/setpoint/state', str(setpoint), qos=1)
                        if(str(data[14]) == "128"):
                            state = hpfuncs.inttostate[int(data[15])]
                            client.publish('varmepumpe/state/state', str(state), qos=1)
                        if(str(data[14]) == "160"):
                            fanmode = hpfuncs.inttofanmode[int(data[15])]
                            client.publish('varmepumpe/fanmode/state', str(fanmode), qos=1)
                        if(str(data[14]) == "163"):
                            swingmode = hpfuncs.inttoswing[int(data[15])]
                            client.publish('varmepumpe/swingmode/state', str(swingmode), qos=1)
                        if(str(data[14]) == "176"):
                            mode = hpfuncs.inttomode[int(data[15])]
                            client.publish('varmepumpe/mode/state', str(mode), qos=1) 
                        if(str(data[14]) == "190"):
                            outdoortemp = int_to_signed(int(data[15]))
                            client.publish('varmepumpe/outdoortemp', str(outdoortemp), qos=1)
                    elif len(data) == 15:
                        if(str(data[12]) == "190"):
                            outdoortemp = int_to_signed(int(data[13]))
                            client.publish('varmepumpe/outdoortemp', str(outdoortemp), qos=1)
                        elif(str(data[12]) == "187"):
                            roomtemp = int_to_signed(int(data[13]))
                            client.publish('varmepumpe/roomtemp', str(roomtemp), qos=1)        
    except Exception as e:
        hpfuncs.logprint(e)
        #restart_and_reconnect()

loop = asyncio.get_event_loop()
loop.create_task(receiver())
loop.create_task(sender())
loop.create_task(firstrun())
loop.run_forever()
