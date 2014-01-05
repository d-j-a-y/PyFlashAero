'''
Created on Jan 4, 2014

@author: cyborg-x1
'''


import http.client


class file_list_entry(object):
    file_name=''
    directory_name=''
    byte_size=-1
    attribute_Archive=False;
    attribute_Directly=False;
    attribute_Volume=False;
    attribute_System=False;
    attribute_Hidden=False;
    attribute_ReadOnly=False;
    date_sep=()
    time_sep=()
    time=0
    date=0
    def __init__(self, file_name, directory_name, size, attributes, date, time):
        self.file_name=file_name
        self.directory_name=directory_name
        self.byte_size=size
        
        '''TODO saftey of integer transform'''
        attributes=int(attributes)
        date=int(date)
        time=int(time)
        
        self.attribute_Archive=  not not(attributes & 1<<5)
        self.attribute_Directly= not not(attributes & 1<<4)
        self.attribute_Volume=   not not(attributes & 1<<3)
        self.attribute_System=   not not(attributes & 1<<2)
        self.attribute_Hidden=   not not(attributes & 1<<1)
        self.attribute_ReadOnly= not not(attributes & 1<<0)

        self.date=date;
        self.time=time;
                
        self.date_sep=(((date&(0x3F<<9))>>9)+1980,((date&(0x1F<<5))>>5),date&(0x1F))
        self.time_sep=(((time&(0x1F<<11))>>11),((time&(0x3F<<5))>>5),(time&(0x1F))*2)
    
class command(object):
    '''OPCODE - DIR DATE ADDR LENGTH DATA  REQUIRED FWVERSION (Bigger/Smaller)'''
    Get_file_list=                      (100,1,0,0,0,0,'1.00.03',True)
    Get_the_number_of_files=            (101,1,0,0,0,0,'1.00.00',True)
    Get_update_status=                  (102,0,0,0,0,0,'1.00.00',True)
    Get_SSID=                           (104,0,0,0,0,0,'1.00.00',True)
    Get_network_password=               (105,0,0,0,0,0,'1.00.00',True)
    Get_MAC_address=                    (106,0,0,0,0,0,'1.00.00',True)
    Set_browser_language=               (107,0,0,0,0,0,'1.00.00',True)
    Get_the_firmware_version=           (108,0,0,0,0,0,''       ,True)
    Get_the_control_image=              (109,0,0,0,0,0,'2.00.00',True)
    Get_Wireless_LAN_mode=              (110,0,0,0,0,0,'2.00.00',True)
    Set_Wireless_LAN_timeout_length=    (111,0,0,0,0,0,'2.00.00',True)
    Get_application_unique_information= (117,0,0,0,0,0,'2.00.00',True)
    Get_CID=                            (120,0,0,0,0,0,'1.00.03',True)
    Get_data_from_shared_memory=        (130,0,0,1,1,0,'2.00.00',True)
    Set_data_to_shared_memory=          (131,0,0,0,0,0,'2.00.00',True)
    Get_the_number_of_empty_sectors=    (140,0,0,0,0,0,'1.00.03',True)
    Enable_Photo_Share_mode=            (200,0,0,0,0,0,'2.00.00',True)
    Disable_Photo_Share_mode=           (201,0,0,0,0,0,'2.00.00',True)
    Get_Photo_Share_mode_status=        (202,0,0,0,0,0,'2.00.00',True)
    Get_SSID_for_Photo_Share_mode=      (203,0,0,0,0,0,'2.00.00',True)
          
class connection(object):
    '''
    classdocs
    '''
    
    list_directory=100
    fwversion=''
    host=0
    port=0
    timeout=0
    def __init__(self, host, port, timeout):
        '''
        Constructor
        '''
        print("init")
        self.host=host
        self.port=port
        self.timeout=timeout
  
        
    def send_command(self, opcode, directory='', date=-1, addr=-1, data=(), length=-1):
        if(len(opcode)==8):
            url="/command.cgi?op=" + str(opcode[0])
    
            if(opcode[1] and len(directory)==0 ):     
                print("ERROR Oppcode " + str(opcode[0]) + " requires directory")
                return(-1,'')
            elif(opcode[1]):
                url += '&DIR=' + directory
            
            if(opcode[2] and date<0 ):    
                print("ERROR Oppcode " + str(opcode[0]) + " requires date")
                return(-1,'')
            elif(opcode[2]):
                url += '&DATE=' + date
            
            if(opcode[3] and addr<0 ):      
                print("ERROR Oppcode " + str(opcode[0]) + " requires addr")
                return(-1,'')
            elif(opcode[3]):
                url += '&ADDR=' + str(addr)
            
            if(opcode[4] and length==0 ):      
                print("ERROR Oppcode " + str(opcode[0]) + " requires length")
                return(-1,'')
            elif(opcode[4]):
                url += '&LEN=' + str(length)
            
            if(opcode[5] and len(data)==0 ):      
                print("ERROR Oppcode " + str(opcode[0]) + " requires data")
                return(-1,'')
            elif(opcode[5]):
                url += '&DATA=' + data

            #Is it a firmware query?
            if(len(opcode[6])!=0):

                if(len(self.fwversion)==0):
                    (ret, ver)=self.send_command(command.Get_the_firmware_version)
                    if(ret):
                        self.fwversion=ver.decode("utf-8")[9:]
                        print("Firmware is: ")
                        print(self.fwversion)
                    else:
                        print("ERROR: Could not determine firmware version!")
                        return(-1,'')
                    
                if(opcode[7]): #must be bigger than or equal to firmware version
                    if(opcode[6]<self.fwversion):
                        print("ERROR Opcode " + str(opcode[0]) + " not supported in firmware!")
                        return(-1,'')
                else:
                    if(opcode[6]>self.fwversion):
                        print("ERROR Opcode " + str(opcode[0]) + " not supported in firmware!")
                        return(-1,'')
            
                
            #Connect
            connection = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)

            connection.request("GET", url) 
            response=connection.getresponse();
            return (response.status==200,response.read())
        
    def get_file_list(self,directory):
        (ret,lst)=self.send_command(command.Get_file_list,directory)

        
        if(ret>0):
            
            lines=lst.decode("utf-8").split("\r\n")
            if(lines[0]=="WLANSD_FILELIST"):
                lines=lines[1:-1] #skip headline, and current dir at the end
            else:
                return (False,())
            
            
            print(lines)
            outlst=[]
            for file in lines:
                e=file.split(",")
                
                if(len(e)!=6):
                    print("Error file list entry has " +str(len(e)) +" entrie(s) instead of expected 6, skipping entry")
                    continue;
                
                f=file_list_entry(e[1],e[0],e[2],e[3],e[4],e[5])
                outlst.append(f)                
                
            return (True,outlst)
        else:
            return (False,())
            