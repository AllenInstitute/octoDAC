/*
Standalone code for octoDAC shield, using TI DAC7568C.
12-bit, 8 channel analog out programmed over SPI from Arduino Uno.

Note : 14- and 16-bit DACs have equivalent footprints, communication,
and can be operated with same code.  

Connections:
octoDAC shield (https://oshpark.com/shared_projects/x0xVWBGH)
or...
Arduino Pin		7568 Pin (16 pin package)
D13				SCLK (16)
D11				DIN (15)
D10				SYNC (2)
D9*				LDAC (1) 
D8*				CLR (9)

* Optional connections:  
- If synchronous mode is desired (default), pull LDAC to ground.
- If CLR pin is not used, pull CLR to ground

Code basis from:
https://gist.github.com/samhutto/9623934
http://www.mouser.com/ds/2/405/sbas430d-94281.pdf

Modified and extended here by PRN

Operation:

Vout = (Din/(2^n))*Vref*Gain
Din is straight binary supplied over SPI bus
Vref = 2.50v, supplied internally. 
0 <= Din <= 65535
n = 16 (extra LSBs are ignored by DAC) 
Gain = 2 (= 2 for 7568C; = 1 for 7568A)
=> Vout = (Din/65536)*Vref*Gain

Internal reference must be enabled in Startup (disabled by default).
External reference is possible, accessed by test pad on shield.

Outputs in datasheet given A->H; equivalent on board as CHAN1 -> CHAN8




From previous code block : 
Two modes of operation, static and flexible
In flexible mode, to always have internal reference powered on, write the following to DB register (32 bit)
0b 0XXX 1001 XXXX 101X XXXX XXXX XXXX XXXX  

Data Input Register
0b     0XXX             XXXX            XXXX       XXXX XXXX XXXX XXXX         XXXX
   Prefix Bits(4) Control Bits(4)  Addr. Bits (4)     Data Bits (16)     Feature Bits (4)
   
   
   
Features desired:

Set given register value via integer over USB
Set all registers to 0 w/ clear code register (pseudo-shutter close)
Return registers to last value (pseudo-shutter open)

Synchronous update should be OK


Commands:
x SHORT - set channel x to value SHORT.  x = 0-8.
s BOOL  - set pseudo-shutter open (1) or closed (0)
y       - return ID string 'octoDAC'
   
*/

#include <SPI.h>

bool verbose = true;

const int syncPin = 10;
const int clearPin = 8;
const int ldacPin = 9;

// Serial variables
String inputString = "";         // a string to hold incoming data
bool stringComplete = false;  // whether the string is complete
short setVal = 0;
bool inputOK = false;
volatile int digitCount = 0;

const int minAllowedChannelID = 48; // greater than or equal to this value; '0'
const int maxAllowedChannelID = 56; // less than or equal to this value; '8'

unsigned int dacChannel = 0;
const int nDacChannels = 8;
unsigned int dacValues[nDacChannels] = {0};
bool dacShutterState = true;

// Software reset
// 0XXX 0111 XXXX XXXX XXXX XXXX XXXX XXXX
const unsigned int setResetOut1 = 0b00000111; 
const unsigned int setResetOut2 = 0b00000000;
const unsigned int setResetOut3 = 0b00000000; 
const unsigned int setResetOut4 = 0b00000000;

// Set Vref to 'internal'
// 0XXX 1001 XXXX 101X XXXX XXXX XXXX XXXX
const unsigned int setVrefOut1 = 0b00001001; 
const unsigned int setVrefOut2 = 0b00001010;
const unsigned int setVrefOut3 = 0b00000000; 
const unsigned int setVrefOut4 = 0b00000000; 

// Configure clear code register
// Set to clear to 0 scale.
// 0XXX 0101 XXXX XXXX XXXX XXXX XXXX XX00
const unsigned int setClrScl1 = 0b00000101; 
const unsigned int setClrScl2 = 0b00000000;
const unsigned int setClrScl3 = 0b00000000; 
const unsigned int setClrScl4 = 0b00000000; 

// Data inputs
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


void setup() {
  // set the slaveSelectPin as an output:
  pinMode(syncPin, OUTPUT);
  pinMode(clearPin, OUTPUT);
  pinMode(ldacPin, OUTPUT);
  
  // initialize SPI:
  SPI.setDataMode(SPI_MODE1);
  SPI.begin();
  delay(200);
  
  // Software reset of DAC
  digitalWrite(syncPin,LOW);
  SPI.transfer(setResetOut1);
  SPI.transfer(setResetOut2); 
  SPI.transfer(setResetOut3); 
  SPI.transfer(setResetOut4); 
  digitalWrite(syncPin,HIGH);

  // Set reference to internal
  digitalWrite(syncPin,LOW);
  SPI.transfer(setVrefOut1);
  SPI.transfer(setVrefOut2); 
  SPI.transfer(setVrefOut3); 
  SPI.transfer(setVrefOut4); 
  digitalWrite(syncPin,HIGH);
  
  // Set clear scale to 0
  digitalWrite(clearPin, LOW);
  digitalWrite(syncPin,LOW);
  SPI.transfer(setClrScl1);
  SPI.transfer(setClrScl2); 
  SPI.transfer(setClrScl3); 
  SPI.transfer(setClrScl4); 
  digitalWrite(syncPin,HIGH);

  Serial.begin(9600);
  
}

void loop() {
  
if (stringComplete) {
	
	char firstChar = char(inputString[0]);
  
	//Serial.println(int(firstChar));

  switch (firstChar) {

    //case ('0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8') :
	case ('0') :
	case ('1') : 
	case ('2') : 
	case ('3') : 
	case ('4') : 
	case ('5') : 
	case ('6') : 
	case ('7') : 
	case ('8') :
	// input is '0' through '8'

    
		dacChannel = firstChar - minAllowedChannelID;
		//Serial.println(dacChannel);
		serialInputToShort();
		
		dacValues[dacChannel] = setVal;
		//Serial.println(setVal);
		
		DAC8568Write(prefix, control, dacChannel, dacValues[dacChannel], feature);
	break;	

	case ('s') :
		// 's'
		// Set shutter state
		if (inputString[2] == 48) {
			// '0'
            dacShutterState = false;
        }
        else if (inputString[2] == 49) {
			// '1'
            dacShutterState = true;
        }
        else {
			// Incorrect character
            Serial.println(15, HEX);
        }
		
		toggleShutter();
	break;

	case ('y') :
		// Send device ID over serial
		Serial.println("octoDAC");
    break;

	case ('?') :
		// Query device state
		// State depends on next character

        switch (inputString[2]) {

          case ('s'):

          // Return current shutter state
            if (dacShutterState){
              Serial.println('1');            
            }
            else {
              Serial.println('0');
            }

		  break;
            
        }
    break;
	
	default :
		// Command not recognized. Return error character 0x15.
	      Serial.println(15, HEX);
	break;
	
	}
	
    
    inputString = "";
    stringComplete = false;
    
  }
  
}




void DAC8568Write(unsigned int prefix, unsigned int control, unsigned int address, unsigned int data, unsigned int feature) {
	// take the SS pin low to select the chip:
	digitalWrite(syncPin,LOW);

	//  send in the address and value via SPI:
	one = (prefix << 4)|control;
	two = (address << 4)|(data >>12);
	three = data >> 4;
	four = (data << 4)|feature;

	//output = (one<<24)|(two<<16)|(three<<8)|four;
	SPI.transfer(one);
	SPI.transfer(two);
	SPI.transfer(three);
	SPI.transfer(four);

	//SPI.transfer(address);
	//SPI.transfer(value);

	// take the SS pin high to de-select the chip:
	digitalWrite(syncPin,HIGH); 

	if (verbose) {
		Serial.print("Set DAC channel ");
		Serial.print(address);
		Serial.print(" to ");
		Serial.println(dacValues[address]);
	}
  
}

void serialEvent() {

  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
      //Serial.println("Input:");
    /*  Serial.println(inputString);
      Serial.println("Size:");
      Serial.println(inputString.length()-1);
      */
    }
  }
}

void serialInputToShort() {
        //Serial.println(inputString);
        setVal = 0;
        inputOK = false;
        digitCount = 0;
        for (int i = 2; i < inputString.length(); i++) {

          if ((inputString[i] >= 48) & (inputString[i] < 58)) {
            setVal = setVal*10;
            setVal = setVal + (inputString[i] - 48);
			//Serial.println(setVal);
            digitCount++;
          } // if is valid ascii numeral
        } // for loop over valid characters

        if (digitCount == (inputString.length()-(1+2))) {
          inputOK = true;
        }
}

void toggleShutter() {
	// Change shutter state based on dacShutterState variable.
	// Off - set all DAC values to 0;
	// On - set all DAC values to dacValues[i] value;
	
	if (dacShutterState) {
		Serial.println("Shutter open");
		for (int i = 0; i < nDacChannels; i++){
			
			DAC8568Write(prefix, control, i, dacValues[i], feature);
			
		}
	}
	
	else {
		Serial.println("Shutter closed");
		
		// Cycle clearPin
		digitalWrite(clearPin, HIGH);
		digitalWrite(clearPin, LOW);
		
		}
	}
	
	
	
