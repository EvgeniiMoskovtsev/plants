#include <IRremote.h>
#include "DHT.h"

#define DHTPIN 2 
#define IR_RECEIVE_PIN 4
#define IR_EMITTER_PIN 6

IRsend irsend(IR_EMITTER_PIN);
DHT dht(DHTPIN, DHT11);

unsigned int decreaseTemp[]= {
  9000,4400,550,600,500,600,500,600,550,600,500,600,550,600,500,600,550,1700,550,1700,550,1700,550,1700,550,1700,550,1700,550,1700,550,1700,550,600,500,1750,500,600,550,1700,550,600,500,1750,500,600,550,600,500,1700,550,600,550,1700,550,550,550,1700,550,600,550,1700,500,1750,500,600,550
};
unsigned int inreaseTemp[] = {
  900,4500,500,600,550,600,500,650,500,600,500,650,500,600,500,650,500,1700,550,1700,500,1750,500,1750,500,1750,500,1750,500,1750,500,1700,550,600,550,550,550,600,500,1750,500,600,550,1700,550,600,500,600,550,1700,550,1700,500,1750,500,600,550,1700,550,600,500,1750,500,1750,500,600,550
};
unsigned int power[] = {
  8900,4450,550,600,500,600,550,600,500,600,550,600,500,600,550,600,500,1700,550,1700,550,1700,550,1700,550,1700,550,1700,550,1700,550,1700,550,550,550,600,500,600,550,1700,550,1700,550,1700,550,600,500,600,550,1700,550,1700,500,1750,500,600,550,600,500,600,550,1700,550,1700,550,600,500
};
unsigned int fanSpeed[] = {
  8950,4450,500,600,550,550,550,600,500,600,550,600,500,600,550,600,500,1750,500,1750,500,1750,500,1750,500,1750,500,1700,550,1700,550,1700,550,600,500,600,550,1700,550,1700,550,600,500,1750,500,600,550,600,500,1750,500,1700,550,600,500,600,550,1700,550,600,500,1750,500,1750,500,600,550
};

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t)) {
    Serial.println("E"); // Ошибка
  } else {
    Serial.print(t);
    Serial.print(",");
    Serial.println(h);
  }

  if (Serial.available() > 0) {
    char command = Serial.read();
    switch (command) {
      case 'P': 
        irsend.sendRaw(power, sizeof(power) / sizeof(power[0]), 18); 
        break;
      case 'I': 
        irsend.sendRaw(inreaseTemp, sizeof(inreaseTemp) / sizeof(inreaseTemp[0]), 18); 
        break;
      case 'D': 
        irsend.sendRaw(decreaseTemp, sizeof(decreaseTemp) / sizeof(decreaseTemp[0]), 18); 
        break;
      case 'S':
        irsend.sendRaw(fanSpeed, sizeof(fanSpeed) / sizeof(fanSpeed[0]), 18); 
        break;
    }
  }

  delay(2000);
}

