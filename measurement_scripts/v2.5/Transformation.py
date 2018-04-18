class Transformation:
	def __init__(self, mode):
		self.mode = mode #decides type of conversion to be done, which type of sensors are involved here, hall-effect or something else
	def transform(self, current_raw):
		if(self.mode == 1): # for hall effecet sensor
			self.current =  current_raw/0.1
			return self.current

