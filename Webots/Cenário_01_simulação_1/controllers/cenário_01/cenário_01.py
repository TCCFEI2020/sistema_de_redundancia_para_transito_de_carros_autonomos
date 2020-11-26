""" Cenário 1
    Esse cenário tem como objetivo apresentar todos os conceitos do projeto.
    Nele é realizado uma comunicação via RF, o tratamento da mensagem pelo sistema
    e todas as ações necessárias para a dirigibilidade do veículo.
"""
import time
from math import cos, sin, isnan
from vehicle import Driver
from carsystem import DataProcessing, HandleMessage
import numpy as np


class CarAuto(object):
    """Classe que representa um Carro autônomo.

    Attributes

    data_processing : object
    É o objeto que tem a função de tratar e atualizar os dados do sistema.
    HandleMessage : object
    É o objeto que tem a função de desempacotar a mensagem e fornecer todas as
    funções em conjunto com os seus parâmetros.
    driver : object
    Controla todas as funções de direção e os atributos de um veículo.
    gps : object
    É um objeto que simula todas as funções de um gps.
    camera : object
    Simula uma camera acoplada no carro.
    stimeStep : int
    É a unidade básica de tempo usada na simulação.
    receiver : object
    É um objeto que simula um receptor RF.
    display : object
    É um objeto que simula os display com dados do carro.
    speedometer_image: object
    É a imagem de referência para o display.

    rf_communication : bool
    Atributo que mostra o estado da comunicação RF.
    rf_message : list
    Guarda a mensagem recebida pelo receptor RF.
    message_list: list
    Lista de mensagens que estão verificadas e receberam as
    subfunções e parâmetros.
    message_history: list
    Lista de mensagens que já foram liberadas pelo sistema.
    message_history: list
    Lista de mensagens que não são aplicadas ao carro.
    received_massages : list
    Lista de mensagens recebidas ao longo da exposição ao sinal RF.
    direction : list
    Atual direção do carro
    old_direction : list


    functions : dict
    Todas as funções, com suas subfunções e parâmetros que precisam de
    uma ação do sistema do carro.
    driving_actions_process : list
    Todas as funções que estão sendo processadas e aguardam as condições
    necessárias para serem liberadas.
    speed : float
    Velocidade atual do carro.
    gps_speed : float
    Velocidade pelo gps.


    """

    def __init__(self, maximum_coordinate_update_angle=0.15):

        self.data_processing = DataProcessing()
        self.handle_message = HandleMessage()
        self.driver = Driver()

        self.gps = self.driver.getGPS("gps")
        self.camera = self.driver.getCamera("camera")
        self.time_step = int(self.driver.getBasicTimeStep())
        self.receiver = self.driver.getReceiver("receiver")

        self.display = self.driver.getDisplay('display')
        self.speedometer_image = self.display.imageLoad("speedometer.png")

        self.rf_communication = False
        self.rf_message = None
        self.message_list = []
        self.message_history = []
        self.blocked_messages = []
        self.received_massages = []
        self.direction = None
        self.current_direction = None
        self.old_direction = ['', '']
        self.functions = {}
        self.driving_actions_process = []
        self.current_coordinates = (0, 0)
        self.current_coordinate_vector = []
        self.speed = 0
        self.gps_speed = 0
        self.maximum_coordinate_update_angle = maximum_coordinate_update_angle

    def get_time_step(self):
        """Obtém passo da simulação."""
        return self.time_step

    def get_radio_frequency_message(self):
        """
        Verifica se existe alguma comunicação RF.

        Se a condição for verdadeira:
        -rf_message recebe a mensagem e rf_communication é definido como verdadeiro.
        Se a condição for falsa:
        -rf_message não recebe nada, rf_communication é definido como falso e
        received_massages é zerada.
        """

        rc_Queue = self.receiver.getQueueLength()
        if rc_Queue > 0 and rc_Queue:
            if not self.rf_communication:
                print("Communication!")
            self.rf_communication = True
            rf_msg = self.receiver.getData()
            self.rf_message = tuple(rf_msg.decode('utf-8').replace('\x00', ''))
            self.receiver.nextPacket()

        else:
            if self.rf_communication:
                print("Communication broken!")
                self.rf_communication = False
                self.rf_message = None
                self.received_massages = []

    def is_communicating(self):
        """Verifica se existe alguma comunicação estabelecida."""
        return self.rf_communication

    def update_massages(self):
        """Verifica se mensagem  não foi ignorada ou está no histórico,
        se ela não constar em nenhuma dessas listas, a mensagem é adicionada
        na lista de mensagens recebidas.
        """

        if (
            self.rf_message
            and self.rf_message not in self.received_massages
            and self.rf_message not in self.message_history
            and self.rf_message not in self.blocked_messages
        ):

            print('Direção do carro:', self.direction)
            self.received_massages.append(self.rf_message)
            print("Communicating:", self.rf_message)

    def filters_messages(self):
        """Verifica se as mensagens recebidas não estão nas listas de
        bloqueio(message_list,message_history,blocked_messages).
        As mensagens liberadas passam por um sistema de decisão que
        verifica se a mensagem  é para o carro.
        Se a condição for verdadeira:
        -Elas são adicionadas à lista de tratamento(message_list).
        Se a condição for falsa:
        -Elas são adicionadas à lista de bloqueio(blocked_messages).
        """
        if self.direction is None:
            return
        new_messages = set(self.received_massages).difference(
            self.message_list
        )
        new_messages = new_messages.difference(self.message_history)
        new_messages = new_messages.difference(self.blocked_messages)

        minimum_msg_size = self.handle_message.get_minimum_message_size()
        new_messages = {
            msg_ for msg_ in new_messages if len(msg_) > minimum_msg_size
        }

        for message in new_messages:

            if self.handle_message.check_message_direction(
                msg=message, car_direction=self.direction
            ):
                print('Está mensagem é para o carro?', True)
                self.message_list.append(message)

            elif message not in self.blocked_messages:
                self.blocked_messages.append(message)
                print('Está mensagem é para o carro?', False)

    def check_change_direction(self):
        """Verifica se o carro mudou de direção.
        Returns:
        bool: True se for a mesma direção, False se for outra direção.
        """
        if self.direction is None:
            return False

        if self.old_direction != self.direction:
            self.old_direction = self.direction
            return True

        return False

    def reset_message_history(self):
        """Zera o histórico de mensagens."""
        self.message_history = []

    def reset_blocked_messages(self):
        """Zera as mensagens bloqueadas."""
        self.blocked_messages = []

    def new_parameters_and_functions(self):
        """Verifica se existem novas funções e parâmetros para que
        o sistema atue sobre eles.
        Returns:
        bool: True se for verdadeiro, False se for falso."""
        if set(self.message_list).difference(self.driving_actions_process):
            return True

        return False

    def functions_and_parameters(self):
        """Usa o objeto handle_message para desempacotar/decodificar a mensagem recebida,
        e de acordo com o banco de dados obtém todas as subfunções e parâmetros associados
        a ela."""

        process_update = set(self.message_list).difference(
            self.driving_actions_process
        )
        process_update = process_update.difference(self.blocked_messages)

        for message in process_update:
            key = ''.join(message)
            self.handle_message.reset_error_log()
            msg_type, priority = self.handle_message.traffic_object_type(
                message
            )
            if self.handle_message.check_traffic_object_type_error():
                if message not in self.blocked_messages:
                    self.blocked_messages.append(message)
                if message in self.message_list:
                    self.message_list.remove(message)

                continue

            print('Tipo de objeto:', msg_type)
            print('Prioridade:', priority)
            functions_ret = self.handle_message.gets_functions_and_parameters(
                message, msg_type
            )
            error = self.handle_message.message_error
            self.functions[key] = {
                'subfunctions_package': functions_ret,
                'object_code': key[2:6],
                'error': error,
                'priority': priority,
            }

            print(self.functions)
            self.driving_actions_process.append(message)

    def get_functions_and_parameters(self):
        '''Obtém todas a funções que necessitam de uma ação dos sistema.'''
        return self.functions

    def remove_driving_action(self, function_key):
        '''Remove função que já foi tratada pelo sistema.'''
        print(tuple(function_key))
        self.message_history.append(tuple(function_key))
        self.message_list.remove(tuple(function_key))
        self.driving_actions_process.remove(tuple(function_key))
        del self.functions[function_key]

    def required_driving_actions(self):
        """Verifica se o sistema precisa tomar alguma ação de direção ou
        atuar em uma situação.
        Returns:
        bool: True se for verdadeiro, False se for falso.
        """
        if self.driving_actions_process:
            return True

        return False

    def reset_inaccurate_data(self):
        '''Zera os dados imprecisos'''
        angulo = self.driver.getSteeringAngle()
        # if angulo> 0.10 or angulo < -0.10:
        if (
            angulo > self.maximum_coordinate_update_angle
            or angulo < -self.maximum_coordinate_update_angle
        ):
            self.data_processing.reset_coordinates()

    def update_data(self, gps_update_mode='next'):
        """Atualiza todos os dados do sistema obtendo todos os
        dados dos dispositivos do carro."""
        self.gps_speed = self.gps.getSpeed()
        self.current_coordinates = self.gps.getValues()[0:3:2]
        self.speed = self.driver.getCurrentSpeed()

        self.data_processing.update_coordinates(
            np.array(self.gps.getValues())[0:3:2]
        )

        if self.data_processing.valid_gps_samples():

            self.direction = self.data_processing.car_direction()
            self.current_coordinate_vector = (
                self.data_processing.coordinate_list
            )

            if gps_update_mode == 'next':
                self.data_processing.next_coordinate()
            elif gps_update_mode == 'reset':
                self.data_processing.reset_coordinates()

        self.update_display()

    def update_display(self):
        '''Atualiza display do carro.'''
        NEEDLE_LENGTH = 50.0
        self.display.imagePaste(self.speedometer_image, 0, 0)
        current_speed = self.speed
        if not current_speed or isnan(current_speed):
            current_speed = 0.0

        alpha = current_speed / 260.0 * 3.72 - 0.27
        x = -NEEDLE_LENGTH * cos(alpha)
        y = -NEEDLE_LENGTH * sin(alpha)
        self.display.drawLine(100, 95, 100 + int(x), 95 + int(y))
        lat, lon = self.current_coordinates
        gps_text = "GPS: {:10.7f} {:10.7f}".format(lat, lon)
        self.display.drawText(gps_text, 10, 130)
        gps_speed_text = "GPS speed:{:4.4}".format(self.gps_speed * 3.6)
        self.display.drawText(gps_speed_text, 10, 140)

        speed_text = "Speed:{:4.4}".format(current_speed)
        self.display.drawText(speed_text, 120, 140)


def cenario_01(car, function_key, function):
    """Age no sistema de direção do carro de acordo com as funções e
    parâmetros gerados com a interação carro x mensagem.
    Todos os parâmetros são acessíveis, mas o sistema determinístico decide quais
    parâmetros são necessários.
    Nessa simulação apenas a velocidade é usada para provocar uma alteração no carro.
    """

    error = function['error']
    # Verifica se existe algum erro na mensagem
    if error is False:
        subfunctions_package = function['subfunctions_package']
        speed_limit = subfunctions_package['speed_variation']['velocidade']
        speed = int(speed_limit)
        car.driver.setThrottle(0.5)
        car.driver.setCruisingSpeed(speed)
        speedDiff = car.driver.getCurrentSpeed() - speed
        if speedDiff > 0:
            car.driver.setBrakeIntensity(min(speedDiff / speed, 1))
        else:
            car.driver.setBrakeIntensity(0)

        # Condição para avaliar se os ações de direção foram satisfatórias
        if speedDiff <= 1:
            # Retira a função da lista de ações
            car.remove_driving_action(function_key=function_key)


car = CarAuto()
# Velocidade inicial
speed = 60
car.driver.setCruisingSpeed(speed)
car.gps.enable(10)
car.camera.enable(10)
time_step = car.get_time_step()
car.receiver.enable((int(time_step / 2)))
cont = 0
while car.driver.step() != -1:
    cont += 1
    # obtém a  messagem RF
    car.get_radio_frequency_message()

    # Verifica se existe um comunicação RF
    if car.is_communicating():
        # Atualiza a lista mensagens recebidas
        car.update_massages()
        # Filtra as mensagens que precisam de uma ação de direção do veículo.
        car.filters_messages()

    # Verifica se existem novas ações de direção esperando tratamento.
    if car.new_parameters_and_functions():
        # Obtém as subfunções e parâmetros necessários para o sistema de direção.
        car.functions_and_parameters()

    # Verifica se o sistema precisa tomar alguma medida de direção
    if car.required_driving_actions():
        functions = dict(car.get_functions_and_parameters())
        for function_key, function in functions.items():
            # Apenas object_code BBBB está disponível nesta simulação
            if function['object_code'] == 'BBBB':
                cenario_01(car, function_key, function)

    # Verifica se a direção mudou.
    if car.check_change_direction():
        # Zera as mensagens bloqueadas e no histórico.
        car.reset_message_history()
        car.reset_blocked_messages()

    if cont % 100 == 0 and True:
        print('car.driving_actions_process', car.driving_actions_process)
        print('car.message_list', car.message_list)
        print('car.received_massages', car.received_massages)
        print('car.functions', car.functions)
        print('car.message_history', car.message_history)
        print('car.blocked_messages', car.blocked_messages)

    # zera dados necessários
    car.reset_inaccurate_data()

    # Atauliza os dados dos dispositivos
    if cont % 10 == 0:
        car.update_data(gps_update_mode='reset')
