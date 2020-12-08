// Receptor

#include <SPI.h>
#include <LoRa.h>
int counter;

void setup() 
{  
  Serial.begin(9600); // Inicia a porta serial com taxa de 9600bits/s
  while (!Serial); // Aguarda a serial ser iniciada
  if (!LoRa.begin(915E6)) { // Testa se o módulo foi iniciado, f = 916MHz
    Serial.println("init failed");
    while (1);
  }
  LoRa.setSpreadingFactor(10); 
}

void loop(){ 
  // Rastreio da mensagem
  
  int packetSize = LoRa.parsePacket();
  if (packetSize) { // Pacote recebido
    // Leitura do Pacote
    Serial.print("Pacote recebido: ");
    while (LoRa.available()) {
      Serial.print((char)LoRa.read()); //Envia a mensagem para a porta serial 
    }
    Serial.println();
    Serial.print(" RSSI: ");
    Serial.print(LoRa.packetRssi());
    Serial.print(" dBm ||");
    Serial.print(" SNR: ");
    Serial.print(LoRa.packetSnr());
    Serial.println(" dB");
   
    
    
  }
  
}
