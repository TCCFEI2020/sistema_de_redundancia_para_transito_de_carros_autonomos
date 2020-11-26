import time
from carsystem import DataProcessing, HandleMessage
from settings.devices import serial_port, serial_baud_rate
import serial
import numpy as np

data_processing = DataProcessing(gps_samples=3)
handle_msg = HandleMessage()

simulacao_gps = [tuple([-x, 0, -2 * x]) for x in range(1, 100)]
mensagem_rf_simulada = ('X', 'N', 'B', 'B', 'B', 'B', '0', '8', '0')
conexao = serial.Serial(serial_port, serial_baud_rate)

direction = ()
cont = 0
while True:

    cont += 1
    '''simula uma mensagem'''
    msg = mensagem_rf_simulada

    # mensagem serial via Arduino
    # msg = tuple(conexao.readline().decode('utf-8').strip())

    print('Mensagem:', msg)

    # simula a direção do carro

    print('Direção do carro:', direction)

    data_processing.update_coordinates(np.array(simulacao_gps[cont])[0:3:2])

    if data_processing.valid_gps_samples():
        old_direction = direction
        direction = data_processing.car_direction()
        current_coordinate_vector = data_processing.coordinate_list
        data_processing.next_coordinate()

        message_for_car = handle_msg.check_message_direction(
            msg=msg, car_direction=direction
        )
        print('Está mensagem é para o carro?', message_for_car)

        # Verifica se a messagem é para o carro
        if message_for_car:

            msg_type, priority = handle_msg.traffic_object_type(msg)
            print('Tipo de objeto:', msg_type)
            print('Prioridade:', priority)

            if not handle_msg.check_traffic_object_type_error():
                functions = handle_msg.gets_functions_and_parameters(
                    msg, msg_type
                )
                print(functions)

    time.sleep(2)
    print("=" * 55)
