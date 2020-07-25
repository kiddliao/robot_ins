import json
import base64

def Register(RobotID='robot001',VisionID='vision001',user='hi',password='hello'):
    """
    """
    data_dict = {'Command':"Register",
                 'RobotID':RobotID,
                 'VisionID':VisionID,
                 "user":user,
                 "password":password}
    json_data = json.dumps(data_dict)
    return json_data

def rt_Register(Retval,Reason):
    '''
    instant response for register
    :return:
    '''
    data_dict = {"Command":"rt_Register",
                 "Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def OPParas(OpNo,OpStarttime,OpEndtime,OpNumber,OpRed,OpBlue,OpYellow,
            OpBar,OpShape,OpX,OpY,OpWidth,OpHeight,DeviceType,VideoType,
            Ip,Port,Url,TaskID):
    data_dict = {"Command":"OPParas","OpStarttime":OpStarttime,"OpEndtime":OpEndtime,
                 "OpNumber":OpNumber,"OpRed":OpRed,"OpBlue":OpBlue,
                 "OpYellow":OpYellow,"OpBar":OpBar,"OpShape":OpShape,
                 "OpX":OpX,"OpY":OpY,"OpWidth":OpWidth,"OpHeight":OpWidth,
                 "DeviceType":DeviceType,"VideoType":VideoType,
                 "Ip":Ip,"Port":Port,"Url":Url,"TaskID":TaskID}
    json_data = json.dumps(data_dict)
    return json_data

def rt_OPParas(TaskID,Retval,Reason):
    data_dict = {"Command":"rt_OPParas",
                 "TaskID":TaskID,
                 "Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def ack_rt_OPParas(Success,ErrorMessage):
    data_dict = {"Success":Success,
                 "ErrorMessage":ErrorMessage}
    json_data = json.dumps(data_dict)
    return json_data

def Stop(TaskID):
    data_dict = {"Command":"Stop",
                 "TaskID":TaskID}
    json_data = json.dumps(data_dict)
    return json_data

def rt_Stop(Retval,Reason):
    data_dict = {"Command":"rt_Stop",
                 "Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def Inspection(TaskID,InspectType,InspectPeriod,InspectStart,InspectEnd):
    '''
    from robot to analyse centre
    :return:
    '''
    data_dict = {"Command":"Inspection",
                 "TaskID":TaskID,
                 "InspectType":InspectType,
                 "InspectPeriod":InspectPeriod,
                 "InspectStart":InspectPeriod,
                 "InspectEnd":InspectEnd}
    json_data = json.dumps(data_dict)
    return json_data

def ack_Inspection(TaskID,Retval,Reason):
    data_dict = {"Command":"Inspection",
                 "TaskID":TaskID,
                 "Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def rt_Inspection(TaskID,OpNumber,OpRed,OpBlue,OpWhite,OpNone,OpYellow,Image):
    '''
    the coefficient image here is represented as the form of base64, the image
    will be transformed to base64 format in the function
    :param TaskID:
    :param OpNumber:
    :param OpRed:
    :param OpBlue:
    :param OpYellow:
    :param Image: str, 图片的绝对地址
    :return:
    '''
    data_dict = {"Command":"rt_Inspection",
                 "TaskID":TaskID,
                 "OpNumber":OpNumber,
                 "OpRed":OpRed,
                 "OpBlue":OpBlue,
                 "OpYellow":OpYellow,
                 "OpWhite":OpWhite,
                 "OpNone":OpNone}
    if len(Image)<200:
        # try:
        with open(Image,'rb') as file:
            Image64 = base64.b64encode(file.read()).decode()
            # Image64 = str(Image64)
            Image = Image64
        # except:
        #     # with open('base64.txt', 'r') as file:
        #     #     Image64 = file.read().strip()
        #     #     Image64 = 'test'
        #     print("create_json 出错")
            

    # else:
    #     Image64 = Image
    # Image64 = Image
    if type(Image)!=str:
        Image = Image.decode()
    else:
        print("Image is str 🍺🍺🍺-------------------")
    data_dict['Image'] = Image
    # print('data_dict1',data_dict)
    data_dict['contentLength'] = len(str(data_dict))+13+10
    # print('111111111111111111111',data_dict)
    # print('data_dict',data_dict)
    print('---data_dict 转换完成')
    # with open('intermedia.txt','w') as file:
    #     file.write(str(data_dict))
    json_data = json.dumps(data_dict)+'\n'
    #json_data = str(data_dict)
    return json_data

def Event(TaskID,EventNumber,SubEvent,Eventtime,EventPic):
    data_dict = {"Command":"Event",
                 "TaskID":TaskID,
                 "EventNumber":EventNumber,
                 "SubEvent":SubEvent,
                 "Eventtime":Eventtime}

    '''with open(EventPic,'rb') as file:
        EventPic = base64.b64encode(file.read())
        EventPic64 = str(EventPic)'''
    data_dict['EventPic']= EventPic
    data_dict['contentLength'] = len(str(data_dict))+13+10
    json_data = json.dumps(data_dict)
    return json_data

def rt_Event(TaskID,Retval,Reason):
    data_dict = {"Command":"rt_Event",
                 "TaskID":TaskID,
                 "Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def SyncIdentify(PersonInfo):
    data_dict = {"Command":"SyncIdentity",
                 "PersonInfo":str(PersonInfo)}
    json_data = json.dumps(data_dict)
    return json_data

def rt_SyncIdentity(Retval,ErrorCodeList,ErrorReasonList):
    data_dict = {"Command":"rt_SyncIdentity",
                 "Retval,":Retval,
                 "ErrorCodeList":ErrorCodeList,
                 "ErrorReasonList":ErrorReasonList}
    json_data = json.dumps(data_dict)
    return json_data

def StartIdentify(TaskID,DeviceType,VideoType,IP,Port,Url,PersonCount,
                  WaitMinutes):
    data_dict = {"Command":"StartIdentify",
                 "TaskID":TaskID,
                 "DeviceType":DeviceType,"VideoType":VideoType,'IP':IP,
                 "Port":Port,"Url":Url,"PersonCount":PersonCount,
                 "WaitMinutes":WaitMinutes}
    json_data = json.dumps(data_dict)
    return json_data

def ack_StartIdentify(Retval,Reason):
    data_dict = {"Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def rt_StartIdentify(TaskID,Retval,MatchInfo,Reason,DismatchPic):

    data_dict = {"Command":"rt_StartIdentify",
                 "TaskID":TaskID,
                 "Retval":Retval,
                 "MatchInfo":MatchInfo,
                 "Reason":Reason,
                 "DismatchPic":DismatchPic}
    data_dict['contentLength'] = len(data_dict)+23
    json_data = json.dumps(data_dict)
    return json_data

def ack_StopIdentify(Retval,Reason):
    data_dict = {"Retval":Retval,
                 "Reason":Reason}
    json_data = json.dumps(data_dict)
    return json_data

def MessageLength(TaskID, length):
    """
    args:
        TaskID: string, 
        length: int
    """
    data_dict = {"TaskID":TaskID,
                 "length":length}
    json_data = json.dumps(data_dict)
    return json_data