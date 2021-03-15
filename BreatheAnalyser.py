# ==========================================================================================================================
# To create python kivy script to build live breathe analyser gauge.
# ==========================================================================================================================

# Module Imports
import random
import sys
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from math import cos, radians, sin
from kivy.core.text import Label
from kivy.graphics import *
from kivy.properties import *
from kivy.uix.image import CoreImage, Image
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.graphics.instructions import *

# set Background display & Window Size
Window.clearcolor = (1, 1, 1, 1)
Window.size = (350, 550)

# declaration Instructions
_position = tuple('pos size min max'.split())
_background = tuple('sectors sector_width shadow_color'.split())
_full_dial = tuple('tick subtick dial_color display_first display_last value_font_size'.split())
_label = tuple('label label_radius_ratio label_angle_ratio label_icon label_icon_scale label_font_size'.split())
info_list = tuple('sectors shadow full_dial values label needle'.split())


class PulseMeter(Widget):

	min = NumericProperty(0)
	max = NumericProperty(100)
	
	tick = NumericProperty(10)
	subtick = NumericProperty(0)

	display_first = BooleanProperty(True)
	display_last = BooleanProperty(True)

	start_angle = NumericProperty(-90, min=-360,max=360)
	end_angle = NumericProperty(135, min=-360,max=360)

	dial_color = StringProperty('#ffffff')
	text_color = StringProperty('#00ff00')

	label = StringProperty('')
	label_icon = StringProperty('')
	label_icon_scale = NumericProperty(0.5, min=0, max=1)
	label_font_size = NumericProperty(15, min=1)
	value_font_size = NumericProperty(15, min=1)

	label_radius_ratio = NumericProperty(0.3, min=-1, max=1)
	label_angle_ratio = NumericProperty(0.5, min=0, max=1)
    
	sectors = ListProperty()
	sector_width = NumericProperty(0, min=0)
	thickness = NumericProperty(1.5, min=0)

	shadow_color = StringProperty('#f20000')
	value = NumericProperty(0)

	def __init__(self, **kwargs):
		super(PulseMeter, self).__init__(**kwargs)
		self.a = self.b = self.r2 = self.r = self.centerx = self.centery = 0
		self._shadow = None

		add = self.canvas.add
		for info in info_list:
			ig = InstructionGroup()
			setattr(self, '_%sIG' % info, ig)
			add(ig)

		self.extendedTouch = False
		bind = self.bind
		for eventList, fn in (
				(_position, self._position), 
				(_background, self._background),
				(_full_dial, self._setfull_dial),
				(_label, self._label),
		):
			for event in eventList:
				bind(**{ event: fn })

	def _sectors(self):
		self._sectorsIG.clear()
		add = self._sectorsIG.add
		l = self.sectors[:]
		if not l: return
		r = self.r
		centerx = self.centerx
		centery = self.centery
		d = r + r
		a = self.a
		b = self.b
		v0 = l.pop(0)
		a0 = -(a * v0 + b)
		sw = self.sector_width
		if sw:
			r -= sw
		else:
			centerx -= r
			centery -= r
			dd = (d, d)

		while l:
			color = l.pop(0)
			v1 = l.pop(0) if l else self.max
			a1 = -(a * v1 + b)
			add(Color(rgba=get_color_from_hex(color)))
			if sw:
				add(Line(circle=(centerx, centery, r, a0, a1), width=0, cap='none', close='false'))
			else:
				add(Ellipse(pos=(centerx, centery), size=dd, angle_start=a0, angle_end=a1))
			a0 = a1

	def _setshadow(self):
		self._shadowIG.clear()
		self._shadow = None
		if not self.shadow_color: return
		add = self._shadowIG.add
		add(Color(rgba=get_color_from_hex(self.shadow_color if self.value > 80 else( '#00FF00' if self.value <= 40 else '#FFA500' )  )))
		self._shadow = Line(width=2.4, cap='none')
		add(self._shadow)
		if not self._shadow: return
		a0 = -(self.a * self.min + self.b)
		a1 = -(self.a * self.value + self.b)
		self._shadow.circle = (self.centerx, self.centery, self.r-3, a0, a1)
	
	def _values(self):
		self._valuesIG.clear()
		add = self._valuesIG.add
		centerx = self.centerx
		centery = self.centery
		r = self.r
		values = [Label(str(i), bold=True, font_size=self.value_font_size)
					  for i in range(self.min, self.max + 1, self.tick)]
		if len(values) <= 1:return
		for _ in values: _.refresh()

		theta0 = self.start_angle
		theta1 = self.end_angle
		if theta0 == theta1:
			theta1 += 360
		deltaTheta = radians((theta1 - theta0) / float(len(values) - 1))
		theta = radians(theta0)
		r_3 = r - 3
		r_8 = r - 8
		subtick = int(self.subtick)
		if subtick:
			subDeltaTheta = deltaTheta / subtick
		else:
			subDeltaTheta = None 
			
		for value in values:
			first = value is values[0]
			last = value is values[-1]
			c = cos(theta)
			s = sin(theta)
			r_1 = r - 1
			if not first and not last or first and self.display_first or last and self.display_last:
				add(Color(rgba=get_color_from_hex('#3a9fbf')))
				add(Line(points=(
					centerx + r_1 * s , centery + r_1 * c ,
					centerx + r_3 * s  , centery + r_3 * c ,
					),
					width=2))
				
				
			if first or last:
				t = value.texture  
				tw, th = t.size
				add(Rectangle(pos=(centerx + r_8 * s - tw, centery + r_8 * c - th ),size=(tw + 5.75, th+2),texture=t))
				
			# Subtick
			if subDeltaTheta and not last:
				subTheta = theta + subDeltaTheta
				for n in range(subtick):
					subc = cos(subTheta)
					subs = sin(subTheta)
					add(Color(rgba=get_color_from_hex('#3a9fbf')))
					add(Line(points=(
						centerx + r * subs, centery + r * subc,
						centerx + r_3 * subs, centery + r_3 * subc),
							 width=1.75))
					subTheta += subDeltaTheta
			theta += deltaTheta

	def _label(self, *t):
		self._labelIG.clear()
		if not self.label and not self.label_icon:
			return

		theta = self.start_angle + self.label_angle_ratio * (self.end_angle - self.start_angle)
		c = cos(radians(theta)) 
		s = sin(radians(theta))
		r = self.r
		r1 = r * self.label_radius_ratio /2
		if self.label_icon:
			label = CoreImage(self.label_icon)
			t = label.texture
			iconSize = max(t.size)
			scale = r * self.label_icon_scale / float(iconSize)
			tw, th = t.size
			tw *= scale
			th *= scale
		else:
			label = Label(text=self.label, markup=True, bold=True, font_size=self.label_font_size)
			label.refresh()
			t = label.texture
			tw, th = t.size
			
		# Defining colors to the range of values 
		
		if self.value > 80 : self.text_color = self.shadow_color
		elif self.value <= 40 and self.value != 0: self.text_color = '#00ff00'  
		elif self.value == 0: self.text_color = '#696969'
		else: self.text_color = '#FFA500' 
		
		
		self._labelIG.add(Color(rgba=get_color_from_hex(self.text_color)   ))
		self._labelIG.add(
			Rectangle(
				pos=(self.centerx + r1 * s - tw, self.centery + r1 * c - th), size=(tw * 2, th * 2),
				texture=t))

	def _needle(self, *t):
		self._needleIG.clear()
		add = self._needleIG.add
		add(PushMatrix())
		self.rotate = Rotate(origin=(self.centerx, self.centery))
		add(self.rotate)

		if self.value < self.min: self.value = self.min
		elif self.value > self.max: self.value = self.max
		add(PopMatrix())
		self.on_value()
		
	def _background(self, *t):
		self._sectors()
		self._setshadow()

	def _setfull_dial(self, *t):
		self._full_dialIG.clear()
		add = self._full_dialIG.add
		centerx = self.centerx
		centery = self.centery
		r = self.r
		theta0 = self.start_angle
		theta1 = self.end_angle
		add(Color(rgba=get_color_from_hex(self.dial_color)))
		if theta0 == theta1:add(Line(circle=(centerx, centery, r), width=0.5))
		else: add(Line(circle=(centerx, centery, r, theta0, theta1), width=0.5))
			
		# to draw values in the Dial
		self._values()

	def _position(self, *args):
		sa = self.start_angle
		ea = self.end_angle
		
		r = self.r = min(self.size) / 2
		self.r2 = r * r
		x, y = self.pos
		width, height = self.size
		self.centerx = x + width / 2
		self.centery = y + height / 2

		theta0 = sa
		theta1 = ea
		if theta0 == theta1: theta1 += 360
		self.a = (float(theta0) - theta1) / (self.max - self.min)
		self.b = -theta0 - self.a * self.min

		
		self._background()
		self._setfull_dial()
		self._label()
		self._needle()
		
	def on_value(self, *t):
		self.rotate.angle = self.a * self.value + self.b
		self._setshadow()



class BreatheAnalyser(App):

	val = NumericProperty(1)

	def __init__(self, **kwargs):
		App.__init__(self)
		super(BreatheAnalyser, self).__init__(**kwargs)
		self.clockRunning = True
		Clock.schedule_interval(self.set_speed, self.val)
	
		
	def set_init(self, *t, **kwargs):
		ids = self.root.ids
		self.clockRunning = True
		ids.speed.value = 0
		ids.speed.label = "0"
		
		if self.val > 10:Clock.unschedule(self.set_speed, self.set_init)
		
	def set_speed(self,*t, **kwargs):
		ids = self.root.ids
		if self.clockRunning:
			self.val += 1
			self.clockRunning = False
			value = random.randint(20,110)
			ids.speed.value = int(value) * 1
			ids.speed.label = str(int(value) * 1)
			Clock.schedule_interval(self.set_init, self.val)
					

BreatheAnalyser().run()
