#include <stdint.h>
#include <stdio.h>


/*
uint8_t Frame_Verify_Checksum(uint8_t data[]){
    uint8_t i = 0;
    uint8_t local_checksum = 0;
    uint8_t received_checksum = 0;
    for(i = 0; i<= data[0]+2; i++){
        local_checksum ^=  data[i];
    }
    
    received_checksum = data[0]+4;
    if(local_checksum == received_checksum){
        return 1;
    }else{
        return 0;
    }
    return local_checksum; 
}*/

uint8_t Frame_Verify_Checksum(uint8_t data[]){
    uint8_t i = 0;
    uint8_t local_checksum = 0;
    uint8_t received_checksum = 0;
    for(i = 0; i<= data[0]+2; i++){
        local_checksum ^=  data[i];
    }
    received_checksum = data[data[0]+3];
    if(local_checksum == received_checksum){
        return 1;
    }else{
        return 0;
    }
}

int main(int argc, char const *argv[])
{
    uint8_t data[] = {0x04, 0x04, 0x68, 0x9E, 0x46, 0x70, 0x47, 0x87};
    uint8_t checksum = 0;
    uint8_t received_checksum = data[data[0]+3]; 
    
    checksum =  Frame_Verify_Checksum(data); 

    printf("%d\n",checksum);
    //printf("%d\n",data[0]+4);  
    

    return 0;
}
