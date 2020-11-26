"""Controlador do sistema de RF acoplado a placa."""
from controller import Robot
from controller import Emitter

# create the Robot instance.
robot = Robot()
# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())
#em=robot.getDeviceByIndex(0)
emitter=Emitter("emitter")

#Transmite a mensagem RF
while robot.step(timestep) != -1:
    
    emitter.send('PXBBBB045'.encode('utf-8'))
