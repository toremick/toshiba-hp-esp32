from time import sleep
def stateControl(msg):
    function_code = 128
    message = msg.decode("utf-8")
    if message == "on":
        function_value = 48
        control_code = 2
    elif message == "off":
        function_value = 49
        control_code = 1
    mylist = (2,0,3,16,0,0,7,1,48,1,0,2,function_code,function_value,control_code)
    myvalues = bytearray(mylist)
    return myvalues

def setpointVal(msg):
    function_code = 179
    function_value = int(msg)
    control_code = 255 -int(msg)
    mylist = (2,0,3,16,0,0,7,1,48,1,0,2,function_code,function_value,control_code)
    myvalues = bytearray(mylist)
    return myvalues


def getsetpoint():
    function_code = 179
    function_value = 1
    mylist = (2,0,3,16,0,0,6,1,0,1,0,1,function_code,function_value)
    myvalues = bytearray(mylist)
    return myvalues


     
def queryall():
     bootlist = []
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,128,52))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,176,4))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,179,1))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,160,20))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,135,45))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,163,17))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,187,249))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,190,246))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,203,233))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,136,44))
     #bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,134,46))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,144,36))
     bootlist.append((2,0,3,16,0,0,6,1,48,1,0,1,148,32))
     return bootlist    

