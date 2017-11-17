#!/usr/bin/python
# coding:utf-8
 
import sys
import time
import signal
import RPi.GPIO as GPIO
import os
import subprocess

# Variáveis para auxiliar no controle do loop principal
# sampling_rate: taxa de amostragem em Hz, isto é, em média,
#   quantas leituras do sonar serão feitas por segundo
# speed_of_sound: velocidade do som no ar a 30ºC em m/s
# max_distance: máxima distância permitida para medição
# max_delta_t: um valor máximo para a variável delta_t,
#   baseado na distância máxima max_distance

cmd = '/bin/ps -ef | grep -i "python /home/pi/Desktop/Identificador_de_objetos/Ultrasonic_Sensor/sensor.py" | grep -v grep | sed -n \'1,2!p\''
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
output, error = process.communicate()

print (output)

if (output):
    print ("Script already running...")
    sys.exit()

os.system("jackd -d alsa > /dev/null 2>&1&")

sampling_rate = 20.0
speed_of_sound = 349.10
max_distance = 4.0
max_delta_t = max_distance / speed_of_sound
radius = 100.0
image_file = "/home/pi/Desktop/Identificador_de_objetos/image.var"

class Sensor (object):
    def __init__(self, TRIG, ECHO):
        self._TRIG = TRIG
        self._ECHO = ECHO

def Pulse(port):
    GPIO.output(port, True)
    time.sleep(0.00001)
    GPIO.output(port, False)
 
# Define a numeração dos pinos de acordo com a placa
GPIO.setmode(GPIO.BOARD)
 
# Função para finalizar o programa de forma segura com CTRL-C
def sigint_handler(signum, instant):
    GPIO.cleanup()
    sys.exit()

def EmmitSound(sensor):
    # Gera um pulso de 10ms em TRIG.
    # Essa ação vai resultar na transmissão de ondas ultrassônicas pelo
    # transmissor do módulo sonar.
    Pulse(sensor._TRIG)
 
    # Atualiza a variável start_t enquanto ECHO está em nível lógico baixo.
    # Quando ECHO trocar de estado, start_t manterá seu valor, marcando
    # o momento da borda de subida de ECHO. Este é o momento em que as ondas
    # sonoras acabaram de ser enviadas pelo transmissor.
    while (GPIO.input(sensor._ECHO) == 0):
      start_t = time.time()
 
    # Atualiza a variável end_t enquando ECHO está em alto. Quando ECHO
    # voltar ao nível baixo, end_t vai manter seu valor, marcando o tempo
    # da borda de descida de ECHO, ou o momento em que as ondas refletidas
    # por um objeto foram captadas pelo receptor. Caso o intervalo de tempo
    # seja maior que max_delta_t, o loop de espera também será interrompido.
    while GPIO.input(sensor._ECHO) == 1 and time.time() - start_t < max_delta_t:
      end_t = time.time()
 
    # Se a diferença entre end_t e start_t estiver dentro dos limites impostos,
    # atualizamos a variável delta_t e calculamos a distância até um obstáculo.
    # Caso o valor de delta_t não esteja nos limites determinados definimos a
    # distância como -1, sinalizando uma medida mal-sucedida.
    if end_t - start_t < max_delta_t:
        delta_t = end_t - start_t
        distance_value = 100*(0.5 * delta_t * speed_of_sound)
        distance_value = round(distance_value, 2)
    else:
        distance_value = -1
 
    # Imprime o valor da distância arredondado para duas casas decimais
    return distance_value
 
    # Um pequeno delay para manter a média da taxa de amostragem
    time.sleep(1/sampling_rate)

# Ativar a captura do sinal SIGINT (Ctrl-C)
signal.signal(signal.SIGINT, sigint_handler)
 
# TRIG será conectado ao pino 18. ECHO ao pino 16.
#TRIG = 16
#ECHO = 18
sensors = []
#sensors.append(Sensor(11,13))
sensors.append(Sensor(16,18))

radius_sensor = Sensor(11,13)

def CalcRadius():
    read = EmmitSound(radius_sensor)
    print ("LEITURA: " + str(read))
    rad = 100
    
    if (read < 30 or read > 190):
        rad = radius
    else:
        rad = read
        
    if (rad > (radius+10)):
        os.system('espeak -v pt -s 250 "depressão encontrada!"')
    elif (rad < (radius-10)):
        os.system('espeak -v pt -s 250 "elevação encontrada!"')
    
    
    if (read < 30 or read > 100):
        rad = 100
    
    return(rad)
        
def ControlRadius():
    rad = 0
    for radius_item in radius_average:
        rad += radius_item
    return (rad/3)
 
# Define TRIG como saída digital
# Define ECHO como entrada digital

print ("Sampling Rate:", sampling_rate, "Hz")
print ("Distances (cm)")


GPIO.setup([sensor._TRIG for sensor in sensors], GPIO.OUT)
GPIO.setup([sensor._ECHO for sensor in sensors], GPIO.IN)
GPIO.setup(radius_sensor._TRIG, GPIO.OUT)
GPIO.setup(radius_sensor._ECHO, GPIO.IN)

radius_count = 0
radius_average = [100,100,0]

os.system('espeak -v pt "Identificação de objetos iniciada"')

while True:
    n = 0
    
    print (radius_count)
    
    GPIO.output(sensor._TRIG, False)
    time.sleep(0.5)
    
    radius_average[radius_count] = CalcRadius()
    radius = ControlRadius()
    
    print (radius_average)
    print ("RADIUS: " + str(radius))
    
    if (radius_count >= 2):
        radius_count = 0
    else:
        radius_count += 1

    for sensor in sensors:
        n += 1
        print "\n", n,
        # Inicializa TRIG em nível lógico baixo
        #for i in range(0, 1):
        GPIO.output(sensor._TRIG, False)
        time.sleep(1.0)
        distance = EmmitSound(sensor)
        if (distance > radius and distance < (radius + 95) and (distance > radius_average[radius_count] + 10 or distance < radius_average[radius_count] - 10)):
            print "Found something!",
            process_date = subprocess.Popen("date +\"%M%S\"".split(), stdout=subprocess.PIPE)
            output_date, error_date = process_date.communicate() 
            image_name = "/home/pi/Desktop/Identificador_de_objetos/Camera_Shot/image" + output_date.rstrip() + str(int(round(distance)))+ ".jpg"
            os.system("raspistill -n -t 280 -o " + image_name)
            os.system("echo " + image_name + " > " + image_file)
        elif (distance == -1):
            print "Out of range",
        print (str(distance) + " cm")
