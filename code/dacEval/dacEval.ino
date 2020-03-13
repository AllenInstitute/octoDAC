/*
DAC8568

Code from:
https://gist.github.com/samhutto/9623934

http://www.mouser.com/ds/2/405/sbas430d-94281.pdf

Vout = (Din/(2^n))*Vref*Gain
Din is straight binary
0 <= Din <= 65535
n = 16
Gain = 2 
=> Vout = (Din/65536)*Vref*2
Internal reference must be enable (disabled by default)

Two modes of operation, static and flexible
In flexible mode, to always have internal reference powered on, write the following to DB register (32 bit)
0b 0XXX 1001 XXXX 101X XXXX XXXX XXXX XXXX  

Data Input Register
0b     0XXX             XXXX            XXXX       XXXX XXXX XXXX XXXX         XXXX
   Prefix Bits(4) Control Bits(4)  Addr. Bits (4)     Data Bits (16)     Feature Bits (4)
*/
#include <SPI.h>

const int syncPin = 10;
// 0XXX 0111 XXXX XXXX XXXX XXXX XXXX XXXX
const unsigned int setResetOut1 = 0b00000111; 
const unsigned int setResetOut2 = 0b00000000;
const unsigned int setResetOut3 = 0b00000000; 
const unsigned int setResetOut4 = 0b00000000;

// 0XXX 1001 XXXX 101X XXXX XXXX XXXX XXXX
const unsigned int setVrefOut1 = 0b00001001; 
const unsigned int setVrefOut2 = 0b00001010;
const unsigned int setVrefOut3 = 0b00000000; 
const unsigned int setVrefOut4 = 0b00000000; 

unsigned int prefix = 0b0000; //shouldn't change
unsigned int control = 0b0011; //0b0010 = write and update all registers, 0b0011 write and update single register
unsigned int address = 0b0000; //channel A = 0b0000
unsigned int data = 0b0101101001011010;
unsigned int feature = 0b0000;
//long output = 0b00000000000000000000000000000000;
unsigned int one;
unsigned int two;
unsigned int three;
unsigned int four;
int rampInc = 1000;

void setup() {
  // set the slaveSelectPin as an output:
  pinMode (syncPin, OUTPUT);
  // initialize SPI:
  SPI.setDataMode(SPI_MODE1);
  SPI.begin();
  delay(200);
  digitalWrite(syncPin,LOW);
  SPI.transfer(setResetOut1);
  SPI.transfer(setResetOut2); 
  SPI.transfer(setResetOut3); 
  SPI.transfer(setResetOut4); 
  digitalWrite(syncPin,HIGH);

  digitalWrite(syncPin,LOW);
  SPI.transfer(setVrefOut1);
  SPI.transfer(setVrefOut2); 
  SPI.transfer(setVrefOut3); 
  SPI.transfer(setVrefOut4); 
  digitalWrite(syncPin,HIGH);

  Serial.begin(9600);
  
}

void loop() {
  /*
  data = 0b1111111111111111;
  for (unsigned int address = 0; address<8; address++)
  {
    DAC8568Write(prefix, control, address, data, feature);
    
  }
  delay(50);
  
  data = 0b0111111111111111;
  for (unsigned int address = 0; address<8; address++)
  {
    DAC8568Write(prefix, control, address, data, feature);
    
  }
  delay(50);
  
  data = 0b0000000000000000;
  for (unsigned int address = 0; address<8; address++)
  {
    DAC8568Write(prefix, control, address, data, feature);
    
  }
  delay(50);

  for (unsigned int output = 0; output < 655; output = output+rampInc)
  {
      DAC8568Write(prefix, control, 0, output, feature);
      delay(10);
  }
*/  

  for (int i = 0; i < 512; i=i+16){
    //data = 65535/i;
    data = i;
  
  // data = 65535/4;
    for (unsigned int address = 0; address<8; address++)
    {
      DAC8568Write(prefix, control, address, data, feature);
      delay(10);
    }
  }
  
}



void DAC8568Write(unsigned int prefix, unsigned int control, unsigned int address, unsigned int data, unsigned int feature) {
  // take the SS pin low to select the chip:
  
  //  send in the address and value via SPI:
  one = (prefix << 4)|control;
  two = (address << 4)|(data >>12);
  three = data >> 4;
  four = (data << 4)|feature;
  //output = (one<<24)|(two<<16)|(three<<8)|four;
  digitalWrite(syncPin,LOW);
  SPI.transfer(one);
  SPI.transfer(two);
  SPI.transfer(three);
  SPI.transfer(four);
  //SPI.transfer(address);
  //SPI.transfer(value);
  // take the SS pin high to de-select the chip:
  digitalWrite(syncPin,HIGH); 
}
