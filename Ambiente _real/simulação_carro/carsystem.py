from settings.data import data_files_path, decoding_path
import pandas as pd
import numpy as np


class DataProcessing(object):
    """Classe que representa um sistema de processamento de dados.

    Attributes

    coordinate_list : list
    Lista que guarda n pares de coordenadas.
    gps_samples : int
    Número de amostras para determinar a direção do carro.
    minimum_slope : float
    Mínima inclinação da reta de amostras de coordenadas para
    que se possa estimar a direção do veículo.
    points_on_axis : range
    Pontos do eixo X da curva de coordenadas.

    """

    def __init__(self, gps_samples=10, minimum_slope=0.3):
        self.coordinate_list = np.empty(shape=[0, 2])
        self.gps_samples = gps_samples
        self.points_on_axis = range(gps_samples, 0, -1)
        self.minimum_slope = minimum_slope

    def update_coordinates(self, coordinates):
        """Atualiza o vetor de coordenadas com o último valor."""
        if len(self.coordinate_list) < self.gps_samples:
            self.coordinate_list = np.vstack(
                (coordinates, self.coordinate_list)
            )

    def valid_gps_samples(self):
        """Verifica se o número mínimo de amostras do gps  foi alcançado.

        Returns:
        bool: True se for verdadeiro, False se for falso."""

        if len(self.coordinate_list) == self.gps_samples:
            return True

        return False

    def reset_coordinates(self):
        """Zera o vetor de coordenadas"""
        self.coordinate_list = np.empty(shape=[0, 2])

    def next_coordinate(self):
        """Elimina a última coordenada da lista"""
        self.coordinate_list = self.coordinate_list[:-1]

    def car_direction(self):
        """Determina a direção do carro usando como base a
        variação de latitude e longitude"""

        def estimate_variation_by_angular_coefficient(slope):
            if abs(slope) <= self.minimum_slope:
                return 'X'
            elif slope > 0:
                return 'P'
            elif slope < 0:
                return 'N'

        # Pontos de latitude
        latitude_samples = self.coordinate_list[:, 0]
        # Pontos de longitude
        longitude_sample = self.coordinate_list[:, 1]

        # Curva feita pelos pontos de latitude
        poli_lat = np.polyfit(self.points_on_axis, latitude_samples, 1)
        # Curva feita pelos pontos de longitude
        poli_long = np.polyfit(self.points_on_axis, longitude_sample, 1)

        # Obtém a inclinação da curva
        latitude_slope = poli_lat[0]
        longitude_slope = poli_long[0]

        # Estima a variação das coordenadas
        lon_var = estimate_variation_by_angular_coefficient(longitude_slope)
        lat_var = estimate_variation_by_angular_coefficient(latitude_slope)

        return lon_var, lat_var


class HandleMessage(object):
    """Classe que representa um sistema de tratamento de mensagens.

    Attributes

    base_direction : list
    Representa a direção base que serve como referência.
    message_error : bool
    Armazena o estado da checagem de erro na mensagem.?

    """

    def __init__(self):
        self.base_direction = None, None
        self.message_error = False
        self.traffic_object_type_error = False
        self.__minimum_message_size = 6

    def check_change_direction(self, current_direction):
        """Verificar se houve alguma mudança na direção

        Args:
        current_direction (list): Coordenadas atuais.
        Returns:
        bool: True se verdadeiro, False se falso.
        """
        # Precisa da correção do gps
        if current_direction != self.base_direction:
            self.base_direction = current_direction
            return True

        return False

    def check_traffic_object_type_error(self):
        """ " Verifica se a determinação do objeto falhou.
        Returns:
        bool: True se for verdadeiro, False se for falso."""
        return self.traffic_object_type_error

    def get_message_error(self):
        """ " Verifica se existe alguma falha na mensagem.
        Returns:
        bool: True se for verdadeiro, False se for falso."""
        return self.message_error

    def get_minimum_message_size(self):
        """ " Obtém o tamanho mínimo da mensagem.
        Returns:
        bool: True se for verdadeiro, False se for falso."""
        return self.__minimum_message_size

    def get_data(self, path, index_col=None, header=[0]):
        """Busca dados no sistema.

        Args:
        path (str): Caminho do arquivo.
        index_col Optional (list): Lista de indexes da coluna.
        header Optional (list): Lista de headers

        Returns:
        pandas.DataFrame: retorna um DataFrame.
        """

        def read_csv(path):
            """Carrega CSV"""
            return pd.read_csv(path, index_col=index_col, header=header)

        def read_sql():
            """Carrega BD"""
            pass

        if path.endswith('.csv'):
            return read_csv(path)
        elif path.endswith('.db'):
            return read_sql(path)
        else:
            pass

    def check_message_direction(self, msg, car_direction):
        """Verifica se a mensagem é para o carro
        Args:
        msg (tuple): Messagem recebida.
        car_direction (list): Direção do carro.
        Returns:
        bool: True se for a mesma direção, False se for outra direção.
        """
        msg_direction = msg[:2]

        if msg_direction == car_direction:
            return True
        elif msg_direction[1] == 'X' and msg_direction[0] == car_direction[0]:
            return True
        elif msg_direction[0] == 'X' and msg_direction[1] == car_direction[1]:
            return True

        return False

    def traffic_object_type(self, msg):
        """Determina o tipo de objeto de trânsito que enviou a mensagem.
        Args:
        msg (tuple): Messagem recebida.

        Returns:
        Tuple:Com o tipo de objeto.
        """
        try:
            type_read = msg[2]
            path = data_files_path['traffic_objects']
            df = self.get_data(path)
            if type_read in df['checking_factor'].values:
                return tuple(
                    df.loc[df['checking_factor'] == type_read].values[0][1:]
                )
            else:
                self.message_error = True
                self.traffic_object_type_error = True
                return None, None
        except:
            self.message_error = True
            self.traffic_object_type_error = True
            return None, None

    def gets_functions_and_parameters(self, msg, msg_type):
        """Desempacota e decodifica  os dados nas tabelas e retorna às subfunções e parâmetros
        Args:
        msg (tuple): Messagem recebida.
        msg_type (tuple)

        Returns:
        dict:Funções e parâmetros.
        """

        def table_parameters(parameter_list, function_name):
            """Obtém os dados que não estão codificados que estão
            na Tabela e na messagem"""

            parameters_processed = {}
            for parameter in parameter_list:
                # desempacota as variáveis
                key, column, data_location = parameter.split(':')
                data = str(msg_row[function_name][column])
                if data_location == 'm':

                    try:
                        data = data.split('_')
                        data = [msg[int(i)] for i in data]
                        value = ''.join(data)
                    except:
                        value = 'Error'
                        self.message_error = True

                elif data_location == 't':
                    value = data

                parameters_processed[key] = value

            return parameters_processed

        def coded_parameters(parameter_list, function_name):
            """Obtém os dados que estão codifidados na mensagem,
            faz decodificação usando de decodificação e gera os parâmetros"""
            if not parameter_list:
                return

            parameters_processed = {}
            for parameter in parameter_list:

                try:
                    key, column = parameter.split(':')
                    path = decoding_path[msg_type]
                    df_code = self.get_data(path, index_col=None, header=[0])
                    data = str(msg_row[function_name][column])
                    data = data.split('_')
                    data = [msg[int(i)] for i in data]
                    data = ''.join(data)
                except:
                    data = 'error'
                    self.message_error = True

                if data in df_code['code_key'].values:
                    value = df_code.loc[df_code['code_key'] == data][
                        function_name
                    ].item()
                else:
                    value = 'NaN'
                parameters_processed[key] = value

            return parameters_processed

        def get_parameters(function_name):
            """Obtém as funções e os parâmetros."""
            tab_list = (
                df_parameters.loc[(function_name, 'table')]
                .dropna()
                .str.split('/')
                .to_list()
            )
            cod_list = (
                df_parameters.loc[(function_name, 'coded')]
                .dropna()
                .str.split('/')
                .to_list()
            )
            tab_list = tab_list[0] if tab_list else tab_list
            cod_list = cod_list[0] if cod_list else cod_list
            d1 = {}
            d1 = table_parameters(tab_list, function_name)
            d2 = coded_parameters(cod_list, function_name)

            if d2:
                d1.update(d2)
            elif d1:
                pass
            else:
                d1 = {}

            return d1

        functions = {}

        # Pega as ações de direção que o objeto de trânsito ativa.

        # ID do objeto de trânsito.
        msg_id = ''.join(msg[3:6])
        path = data_files_path[msg_type]
        df = self.get_data(path, index_col=0, header=[0, 1])
        path2 = data_files_path['search_parameters']
        df_parameters = self.get_data(path2, index_col=[0, 1])
        # Se a messagem não existir no banco de dados não retorna as funções.
        if msg_id not in df.index:

            return {}

        msg_row = df.loc[msg_id]
        # Verifica as funções que o objeto de trânsito ativa.
        active_functions = df.loc[
            msg_id, df.columns.get_level_values(1) == 'active'
        ]
        # Obtém os nomes de todas as funções ativadas pela messagem.
        function_names = [
            j[0] for j in active_functions[active_functions.values].index
        ]
        # Pega os parâmetros das funçoes ativadas.
        path2 = data_files_path['search_parameters']
        df_parameters = self.get_data(path2, index_col=[0, 1])

        for function_name in function_names:
            parameters = get_parameters(function_name)
            functions[function_name] = parameters

        return functions

    def reset_error_log(self):
        '''Reinicia o log de erro para uma nova mensagem'''
        self.message_error = False
        self.traffic_object_type_error = False
