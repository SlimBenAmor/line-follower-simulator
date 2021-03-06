# -*- coding: utf-8 -*-
import math
import time
import os
import pygame 
import numpy as np
from matplotlib import image
from pygame.draw import line

black = (0, 0, 0)
blue = (0, 0, 255)
red = (255, 0, 0)
white = (255,255,255)
fps_sim = 50
fps_draw = 20
fps_draw_ratio = math.ceil(fps_sim/fps_draw)
fps_text_ratio = 2

MAX_SPEED =100
MIN_SPEED =-MAX_SPEED
P_TERM = 50 #3.5
I_TERM = 0
D_TERM = 12 #12
integral = 0
previous_line_pos = 0


def pid_control_task(sensors_values):
	global previous_line_pos,integral
	current_line_pos = 0
	for i,sensor in enumerate(sensors_values):
		current_line_pos += (i-2)*sensor
	proportional = current_line_pos
	derivative = current_line_pos - previous_line_pos
	integral += proportional
	previous_line_pos = current_line_pos
	power = (proportional * (P_TERM) ) + (integral*(I_TERM)) + (derivative*(D_TERM))

	speed_right = MAX_SPEED-power  
	speed_left  = MAX_SPEED+power 
	speed_left = max(min(speed_left,MAX_SPEED),MIN_SPEED)
	speed_right = max(min(speed_right,MAX_SPEED),MIN_SPEED)
	return speed_left,speed_right

def deg_to_rad(theta):
	return (theta%360)/180*math.pi
def rad_to_deg(theta):
	return ( theta%(2*math.pi))/math.pi*180


class Robot:
	# Constructor
	def __init__(self, x, y, R, yaw, scale, sensor_dist=0.85, sensor_gap=10):
		self.px = x 	
		self.py = y
		self.radius = R*scale
		self.yaw = deg_to_rad(yaw)
		self.scale = scale
		self.wheel_w = self.radius/8
		self.wheel_r = 3*self.wheel_w
		self.sensor_dist = sensor_dist*self.radius
		self.sensor_r = scale
		self.sensor_gap = sensor_gap  # in degree
		self.dist = 0
		self.vl = 0
		self.vr = 0
		self.sensor_pos_list = []
		for angle in range(-self.sensor_gap*2,self.sensor_gap*2+1,self.sensor_gap):
			self.sensor_pos_list.append(self.rotate_points([[self.px+self.sensor_dist,self.py]],deg_to_rad(angle+yaw))[0])

	def rotate_points(self,points_list,theta):
		for p in points_list:
			p[0],p[1] = self.px+math.cos(theta)*(p[0]-self.px) + math.sin(theta)*(p[1]-self.py),self.py-math.sin(theta)*(p[0]-self.px) + math.cos(theta)*(p[1]-self.py)
		return points_list
	
	def draw(self, screen):
		pygame.draw.circle(screen,blue,(self.px, self.py),self.radius,2)
		pygame.draw.circle(screen,blue,(self.px, self.py),self.sensor_dist,1)
		# pygame.draw.rect(screen, blue, [ ( self.px-self.wheel_r, self.py-self.radius-self.wheel_w ), ( 2*self.wheel_r, self.wheel_w) ], 1)
		# pygame.draw.rect(screen, blue, [ ( self.px-self.wheel_r, self.py+self.radius), ( 2*self.wheel_r, self.wheel_w) ], 1)
		pygame.draw.polygon(screen, blue, self.rotate_points([[self.px-self.wheel_r, self.py+self.radius], [self.px+self.wheel_r, self.py+self.radius], [self.px+self.wheel_r, self.py+self.radius+self.wheel_w], [self.px-self.wheel_r, self.py+self.radius+self.wheel_w]],self.yaw),2)
		pygame.draw.polygon(screen, blue, self.rotate_points([[self.px-self.wheel_r, self.py-self.radius-self.wheel_w], [self.px+self.wheel_r, self.py-self.radius-self.wheel_w], [self.px+self.wheel_r, self.py-self.radius], [self.px-self.wheel_r, self.py-self.radius]],self.yaw),2)
		for sensor in self.sensor_pos_list:
			pygame.draw.circle(screen,red,sensor,self.sensor_r,0)

	def update (self):
		v = (self.vr+self.vl)/2
		self.px = self.px+math.cos(self.yaw)*v/fps_sim
		self.py = self.py-math.sin(self.yaw)*v/fps_sim
		self.dist += v/fps_sim
		if (self.vr!=self.vl):
			R = (self.radius+self.wheel_w/2)*(self.vr+self.vl)/(self.vl-self.vr)
			if (R!=0):
				self.yaw = self.yaw+v/R/fps_sim
			else:
				self.yaw = self.yaw+self.vl/(self.radius+self.wheel_w/2)/fps_sim
		for i,angle in enumerate(range(-self.sensor_gap*2,self.sensor_gap*2+1,self.sensor_gap)):
			self.sensor_pos_list[i] = self.rotate_points([[self.px+self.sensor_dist,self.py]],deg_to_rad(angle)+self.yaw)[0]

	def manual_control(self,event):
		if (event.type == pygame.KEYDOWN):  
			if (event.key==pygame.K_UP):
				self.vr += MAX_SPEED/2
				self.vl += MAX_SPEED/2
			if (event.key==pygame.K_RIGHT):
				self.vr += MAX_SPEED/2
				self.vl -= MAX_SPEED/2
			if (event.key==pygame.K_LEFT):
				self.vr -= MAX_SPEED/2
				self.vl += MAX_SPEED/2
			if (event.key==pygame.K_DOWN):
				self.vr -= MAX_SPEED/2
				self.vl -= MAX_SPEED/2
		if (event.type == pygame.KEYUP):  
			if (event.key==pygame.K_UP):
				self.vr -= MAX_SPEED/2
				self.vl -= MAX_SPEED/2
			if (event.key==pygame.K_RIGHT):
				self.vr -= MAX_SPEED/2
				self.vl += MAX_SPEED/2
			if (event.key==pygame.K_LEFT):
				self.vr += MAX_SPEED/2
				self.vl -= MAX_SPEED/2
			if (event.key==pygame.K_DOWN):
				self.vr += MAX_SPEED/2
				self.vl += MAX_SPEED/2

		
	def automatic_control(self,sensors_values):
		self.vl,self.vr = pid_control_task(sensors_values)



def main():
	pygame.init()
	clock = pygame.time.Clock()
	screen = pygame.display.set_mode((1080, 720), pygame.HWSURFACE)
	base_dir = os.path.dirname(__file__)
	filename = os.path.join(base_dir, 'circuit_1.png')
	image = pygame.image.load(filename).convert_alpha()
	img_arr = pygame.surfarray.array2d(image)
	img_arr[img_arr < -1] = 1
	img_arr = np.maximum(img_arr, 0)
	screen = pygame.display.set_mode(img_arr.shape, pygame.HWSURFACE)
	font = pygame.font.SysFont(None, 24)
	screen.blit(image, (0, 0))
	pygame.display.flip()

	line_follower = Robot(200, 180, 30, 20, 1)  # initial position for circuit_1
	# line_follower = Robot(230, 480, 30, 90, 1)  # initial position for circuit_2
	max_shift = math.ceil(MAX_SPEED/fps_draw)+line_follower.radius+line_follower.wheel_w+2
	rect_update_list = [pygame.Rect(line_follower.px-max_shift,line_follower.py-max_shift,2*max_shift,2*max_shift),pygame.Rect(10,10,90,55)]
	
	cnt_draw = 0
	cnt_text = 0
	done = False
	pos_2_value = lambda s:img_arr[int(s[0]),int(s[1])]
	while done == False:
		sensor_list = list(map(pos_2_value,line_follower.sensor_pos_list))
		# print(list(sensor_list),line_follower.px,line_follower.py,rad_to_deg(line_follower.yaw),line_follower.vl,line_follower.vr)
		line_follower.automatic_control(sensor_list)  # Comment for manual control
		line_follower.update()
		
		if (cnt_draw%fps_draw_ratio==0):
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done=True				
				# line_follower.manual_control(event)	 # Comment for automatic control
						
			screen.blit(image, (0, 0))			
			line_follower.draw(screen)
			rect_update_list[0].update(line_follower.px-max_shift,line_follower.py-max_shift,2*max_shift,2*max_shift)
			if (cnt_text%fps_text_ratio==0):
				screen.blit(font.render("left: "+str(line_follower.vl), True, black), (10,10))
				screen.blit(font.render("right: "+str(line_follower.vr), True, black), (10,25))
				screen.blit(font.render("dist: "+str(int(line_follower.dist)), True, black), (10,40))
				cnt_text = 0
				pygame.display.update(rect_update_list)				
			else:
				pygame.display.update(rect_update_list[0])
			cnt_text += 1		
			cnt_draw = 0
		cnt_draw += 1
		clock.tick(fps_sim)  # Comment to accelerate simulation
	pygame.quit() 

if __name__ == "__main__":
	main()	

		