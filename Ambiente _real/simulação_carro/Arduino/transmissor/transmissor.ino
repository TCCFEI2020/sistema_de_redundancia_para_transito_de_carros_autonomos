
// transmissor

#include <SPI.h>
#include <LoRa.h>
int counter;
void setup()
{
  Serial.begin(9600); // Inicia a porta serial com taxa de 9600bits/s
  while (!Serial) ; // Aguarda a serial ser iniciada
  if (!LoRa.begin(915E6)) { // Testa se o módulo foi iniciado, f = 916MHz
    Serial.println("init failed");
    while (1);
  }
  LoRa.setSpreadingFactor(10);
  LoRa.setTxPower(20);
}

void loop()
{
  // Define e exibe a mensagem que será enviada
  Serial.print("Enviando mensagem:");
  char data[] = "XNBBBB080"; 
  Serial.print(" XNBBBB080");
  Serial.println(counter);

  // Envio da Mensagem
  LoRa.beginPacket(); // Inicia o pacote
  LoRa.print(data); // Escreve e envia a mensagem
  LoRa.print(" ");
  LoRa.print(counter);
  LoRa.endPacket(); // Finaliza o Pacote
  counter++;
  delay (10); // Aguarda 1 segundo para reenviar o pacote
}
