from serial import EIGHTBITS, PARITY_ODD, STOPBITS_ONE
import serial.tools.list_ports
import serial
import time

"""
- Envia byte de inicio
- Espera byte de ACK
- Envia una linea del archivo .hex
- Espera byte de ACK

Nota: Todo funciona bien, se envia una sola linea del 
archivo .hex.
"""

def int_to_bytes(vector): 
    data = []
    i = 0
    for element in vector:
        data.append(vector[i].to_bytes(1,'big'))
        i = i+1
    return data
    
def translate_IntelHex_Line(vector):
    data  = []
    dataBytes = []
    numBytes = vector[1:3]
    data.append(int(numBytes,16))
    Low_ADDRESS_MSB = vector[3:5]
    data.append(int(Low_ADDRESS_MSB,16))
    Low_ADDRESS_LSB = vector[5:7]
    data.append(int(Low_ADDRESS_LSB,16))
    Record_Type = vector[7:9]
    data.append(int(Record_Type,16))

    for i in range(0,int(numBytes,16)):
        a =  vector[9+(i*2):11+(i*2)]
        data.append(int(a,16))

    checksum = 0
    for i in range(0,len(data)):
        checksum = checksum ^ data[i] 
    data.append(checksum)

    #El arreglo del vector es el siguiente
    #data[0] = numBytes
    #data[1] = LowerADDRESS_MSB 
    #data[2] = LowerADDRESS_LSB
    #data[3] = RecordType  
    #data[4] = Inicio de datos.
    #data[4+numBytes] = Checksum. 

    return data

def crc32mpeg2(buf,crc):
    for val in buf:
        crc ^= val << 24
        for _ in range(8):
            crc = crc << 1 if (crc & 0x80000000) == 0 else (crc << 1) ^ 0x104c11db7
    return crc

relativa = "STM32_UART_V2.hex"
archivo = open(relativa,"r")
prueba =[]
crc32 = 0xFFFFFFFF
Total_databytes = 0x0


ports = serial.tools.list_ports.comports(); 
serialInst = serial.Serial()
portList = []
for onePort in ports: 
    portList.append(str(onePort))
    print(str(onePort))
val = input("Select port: COM")

for x in range(0,len(portList)):
    if portList[x].startswith("COM"+str(val)):
        portVar = "COM" + str(val)
        print(portVar)

#Configuracion de UART
serialInst.baudrate = 9600
serialInst.bytesize = EIGHTBITS
#serialInst.parity = PARITY_ODD;
serialInst.stopbits = STOPBITS_ONE
#serialInst.timeout = 2.0
serialInst.port = portVar
serialInst.open()

Tx_Delay = 0.00001 #in seconds
startByte = 15 #0x0F
endByte = 240  #0xF0 
ackByte = 121 #0x79
nackByte = 127 #0x7F
data_frame_byte = 0
CRC_frame_byte = 6
master_NumBytes_frame_byte = 7
master_NumFrames_frame_byte = 8
CRC_3 = 0  #CRC_MSB
CRC_2 = 0  
CRC_1 = 0
CRC_0 = 0  #CRC LSB
master_NumBytes_3 = 0 #MSB
master_NumBytes_2 = 0
master_NumBytes_1 = 0
master_NumBytes_0 = 0 #LSB
Total_dataframes = 0
master_NumFrames_3 = 0 #MSB
master_NumFrames_2 = 0
master_NumFrames_1 = 0
master_NumFrames_0 = 0 #LSB 
master_NumFrames_checksum = 0

startByte = startByte.to_bytes(1,'big')
endByte = endByte.to_bytes(1,'big')
ackByte = ackByte.to_bytes(1,'big')
nackByte = nackByte.to_bytes(1,'big')
data_frame_byte = data_frame_byte.to_bytes(1,'big')
CRC_frame_byte = CRC_frame_byte.to_bytes(1,'big')
master_NumBytes_frame_byte =  master_NumBytes_frame_byte.to_bytes(1,'big')
master_NumFrames_frame_byte = master_NumFrames_frame_byte.to_bytes(1,'big')

send_again_request = 1

serialInst.write(startByte) #indica que comenzará transmision
response = serialInst.read()
error = 0

if (response == ackByte):
    error = 0
elif(response == nackByte):
    error = 2
elif(response != ackByte):
    error = 2

print(error)


while(error != 2):
    vector = archivo.readline()
    data = translate_IntelHex_Line(vector)
    data_in_Bytes = int_to_bytes(data)
    error = 0 #resetea el valor del vector a 0 
    if(data[3] == 0):
        
        Total_dataframes = Total_dataframes + 1
        while(send_again_request == 1):
            #calculo del CRC de los datos (vector data[int[bytes]])
            crc32 = crc32mpeg2(data[4:4+data[0]],crc32)
            Total_databytes += data[0]
            serialInst.write(data_frame_byte)
            time.sleep(Tx_Delay)
            serialInst.write(data_in_Bytes[0]) #Envia num bytes
            time.sleep(Tx_Delay)
            serialInst.write(data_in_Bytes[1]) #Envia ADDRESS MSB
            time.sleep(Tx_Delay)
            serialInst.write(data_in_Bytes[2]) #Envia ADDRESS LSB 
            time.sleep(Tx_Delay)
            #serialInst.write(data_in_Bytes[3]) #Envia Record Type 
            #time.sleep(Tx_Delay)
            for i in range(4,4+data[0]): 
                serialInst.write(data_in_Bytes[i]) #Envia Bytes de datos.
                time.sleep(Tx_Delay)
            serialInst.write(data_in_Bytes[4+data[0]]) #Envia checksum
            time.sleep(Tx_Delay)
            time.sleep(Tx_Delay)
            response = serialInst.read() #Lee respuesta del MSP430
            if(response == ackByte):
                send_again_request = 0
            if(response == nackByte): 
                send_again_request = 1
                error = error + 1
            response = int.from_bytes(response,'big')
            print(data)
            print("Response: ",hex(response))
            print("Numero de frames: ", Total_dataframes)
        send_again_request = 1
    elif(data[3] == 1):
        
        CRC_3 = crc32>>24 & 0xFF
        CRC_2 = crc32>>16 & 0xFF
        CRC_1 = crc32>>8 & 0xFF
        CRC_0 = crc32 & 0xFF
        CRC_checksum = CRC_3 ^ CRC_2 ^ CRC_1 ^ CRC_0 

        master_NumBytes_3 = Total_databytes>>24 & 0xFF
        master_NumBytes_2 = Total_databytes>>16 & 0xFF
        master_NumBytes_1 = Total_databytes>>8 & 0xFF
        master_NumBytes_0 = Total_databytes & 0xFF
        master_NumBytes_checksum = master_NumBytes_3 ^ master_NumBytes_2 ^ master_NumBytes_1 ^ master_NumBytes_0

        master_NumFrames_3 = Total_dataframes>>24 & 0xFF
        master_NumFrames_2 = Total_dataframes>>16 & 0xFF
        master_NumFrames_1 = Total_dataframes>>8 & 0xFF
        master_NumFrames_0 = Total_dataframes & 0xFF
        master_NumFrames_checksum = master_NumFrames_3 ^ master_NumFrames_2 ^ master_NumFrames_1 ^ master_NumFrames_0

        serialInst.write(CRC_frame_byte)
        time.sleep(Tx_Delay)
        serialInst.write(CRC_3.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(CRC_2.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(CRC_1.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(CRC_0.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(CRC_checksum.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        time.sleep(Tx_Delay)
        response = serialInst.read() #Lee respuesta del MSP430
        if(response == ackByte):
            send_again_request = 0
        if(response == nackByte): 
            send_again_request = 1
            error = error + 1
        print("CRC sent: ", hex(crc32))
        response = int.from_bytes(response,'big')
        print("Response: ",hex(response))

        serialInst.write(master_NumBytes_frame_byte)
        time.sleep(Tx_Delay)
        serialInst.write(master_NumBytes_3.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumBytes_2.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumBytes_1.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumBytes_0.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumBytes_checksum.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        time.sleep(Tx_Delay)
        response = serialInst.read() #Lee respuesta del MSP430
        if(response == ackByte):
            send_again_request = 0
        if(response == nackByte): 
            send_again_request = 1
            error = error + 1
        print("Num bytes sent: ", Total_databytes)
        response = int.from_bytes(response,'big')
        print("Response: ",hex(response))

        
        serialInst.write(master_NumFrames_frame_byte)
        time.sleep(Tx_Delay)
        serialInst.write(master_NumFrames_3.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumFrames_2.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumFrames_1.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumFrames_0.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        serialInst.write(master_NumFrames_checksum.to_bytes(1,'big'))
        time.sleep(Tx_Delay)
        time.sleep(Tx_Delay)
        response = serialInst.read() #Lee respuesta del MSP430
        if(response == ackByte):
            send_again_request = 0
        if(response == nackByte): 
            send_again_request = 1
            error = error + 1
        print("Num frames sent: ", Total_dataframes)
        response = int.from_bytes(response,'big')
        print("Response: ",hex(response))
        
        serialInst.write(endByte)

        ##print(hex((Total_databytes>>16)&0xFFFF))
        
        print("------------------------------------------")
        print("------------------------------------------")
        print("Se ha terminado de cargar el programa")
        print("Numero de frames: ", Total_dataframes)
 #       print("CRC: ",hex(crc32&0xFFFFFFFF))
 #       print("CRC_3: ",hex(CRC_3))
 #       print("CRC_2: ",hex(CRC_2))
 #       print("CRC_1: ",hex(CRC_1))
 #       print("CRC_0: ",hex(CRC_0))
        print("CRC: ", hex(crc32&0xFFFFFFFF))
        print("Tamaño de programa (en bytes): ",Total_databytes)
        #print(master_NumBytes_3)
        #print(master_NumBytes_2)
        #print(master_NumBytes_1)
        #print(master_NumBytes_0)
        #print(master_NumBytes_checksum)
        print("------------------------------------------")
        print("------------------------------------------")
        break
    elif(data[3] == 2): 
        print("Intruccion extended segment Address")
    elif(data[3] == 3): 
        print("start segment Address")
    elif(data[3] == 4):
        print("exteded linear Address")
    elif(data[3] == 5): 
        print("Start linear Address")
    #for i in range(0,5):
        #serialInst.write(ackByte)

if (error == 2):
    print("El byte de ACK ha sido incorrecto dos veces consecutivas")

serialInst.close()