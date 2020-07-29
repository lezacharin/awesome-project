import subprocess
import re

# if r'.\modules' not in sys.path: sys.path.insert(0,'.\modules')

# import devices

class window :

	title = ""
	com = ""
	baud = ""
	ip = ""
	pid = ""
	ip_port = 23
	user = ""
	password = ""
	
	def __init__(self, title, com, baud, ip) :
		self.title = title
		self.com = com
		self.baud = baud
		self.ip = ip
		
	def open_serial(self) :
		matchObj = re.match("com(\d+)", self.com, 0)
		if not matchObj :
			print("ERROR: com port mismatch " + str(self.com))
			return 1
		
		ser = matchObj.group(1)
		cmd = "\"c:\\Program Files (x86)\\teraterm\\ttermpro.exe\"" + " /W=" + self.title + " /C=" + str(ser) + " /BAUD=" + str(self.baud)
		self.pid =  subprocess.Popen(cmd, shell=False)
		
	def open_ssh(self) :
		matchObj = re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", self.ip, 0)
		if not matchObj :
			print("ERROR: IP mismatch")
			return 1
		
		ser = matchObj.group(0)
		cmd = "\"c:\\Program Files (x86)\\teraterm\\ttermpro.exe\" " + self.ip + ":" + str(self.ip_port) + " /ssh /auth=password /user=" + self.user + " /passwd=" + self.password + " /W=" + self.title
		self.pid =  subprocess.Popen(cmd, shell=False)
				
	def open_telnet(self) :
		matchObj = re.match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", self.ip, 0)
		if not matchObj :
			print("ERROR: IP mismatch")
			return 1
		
		ser = matchObj.group(0)
		cmd = "\"c:\\Program Files (x86)\\teraterm\\ttermpro.exe\" " + self.ip + ":" + str(self.ip_port) + " /T=1 " + " /W=" + self.title
		print(cmd)
		self.pid =  subprocess.Popen(cmd, shell=False)
				
	def kill(self) :
		try : self.pid.kill()
		except : print("ERROR")
	
	def open_all_serials(setupObj):
		'''
		function will seek all devices containing "com" attribute in OBJ
		OBJ is device_group class
		'''
		tt = {}
		for obj in setupObj.seek_class(None):
			# if isinstance(obj, devices.device_group):
				# obj.seek_class(self,None)
				
			if hasattr(obj, "com"): # serial device
				com = getattr(obj,"com")
				baud = getattr(obj,"baud")
				
				if hasattr(obj, "name"): title = str(getattr(obj,"name"))
				else: title = ""

				tt[obj] = window(title, com, baud ,"")
				tt[obj].open_serial()