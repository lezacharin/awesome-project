import sys
import re
import random
import time
import os
import traceback
#import netifaces
import netaddr
import threading
import smtplib

# sys.path.append('.\modules')
if r'.\modules' not in sys.path: sys.path.insert(0,'.\modules')

import devices

# ######################################################################		
# ######################################################################		
# ######################################################################		
# 							GENERICS
# ######################################################################		
# ######################################################################		
# ######################################################################		

class test_list(devices.UTILITY):

	def __init__(self, name, setupObj, testObj_list):
		'''
		use testObj_list = [] for empty list init
		'''
		devices.UTILITY.__init__(self)
		self.setupObj = setupObj
		self.tests = testObj_list
		self.name = name

	def print_info(self):
		devices.UTILITY.print_info(self)
		for test in self.tests:
			test.print_info()

	def run(self, setupObj, exp):
		for testObj in self.tests:
			testObj.run(self.setupObj, exp)

	def get_stats(self):
		stats_dict = {}  # [name] = [seeds, secs, passed, fail, not_run, unknown]

		for testObj in self.tests:
			name = testObj.name
			seeds = testObj.stats["seeds"]
			secs = testObj.stats["secs"]
			passed = testObj.stats["pass"]
			failed = testObj.stats["fail"]
			not_run = testObj.stats["not_run"]
			unknown = testObj.stats["unknown"]
			stats_dict[name] = [seeds, secs, passed, failed, not_run, unknown]

		# print("DICT = " + str(stats_dict))
		return stats_dict

	def print_stats(self):
		stats_dict = self.get_stats()

		name_width = 35
		width = 10
		subject_list = ["Name", "Seeds", "Time [sec]", "Pass", "Fail", "Not run", "Unknown"]

		print()
		print("Cumulative test list results")
		# print()

		# title
		print("-" * (((name_width + 3) + ((len(subject_list) - 1) * (width + 3)) + 1)))

		for position in range(0, len(subject_list)):
			string = str(subject_list[position])
			if position == 0:
				print("| " + string.ljust(name_width + 1), end='')
			else:
				print("| " + string.ljust(width + 1), end='')
		print("|")

		print("-" * (((name_width + 3) + ((len(subject_list) - 1) * (width + 3)) + 1)))

		for key in stats_dict:
			print("| " + key.ljust(name_width + 1), end='')
			value_list = stats_dict[key]
			for position in range(0, len(value_list)):
				string = str(value_list[position])
				print("| " + string.rjust(width) + " ", end='')
			print("|")

		print("-" * (((name_width + 3) + ((len(subject_list) - 1) * (width + 3)) + 1)))

class testcase(devices.UTILITY):

	def __init__(self, unit):
		devices.UTILITY.__init__(self)
		self.unit = unit
		self.name = ""

		# RF testing args
		self.check_rf = False
		self.min_rf = 0.0
		self.max_rf = 0.0
		self.delay_rf_check = 180.0
		
		# power testing arguments
		self.check_power = False
		self.min_power = 0.0
		self.max_power = 0.0
		self.delay_power_check = 180.0

		# run config
		self.selected = False
		self.stop_on_fail = False
		self.count_to_fail = 1 # in which fail count should the run stop
		
		# stats after run
		self.stats = {}
		self.stats["pass"] = 0
		self.stats["fail"] = 0
		self.stats["not_run"] = 0
		self.stats["unknown"] = 0
		self.stats["seeds"] = 0
		self.stats["secs"] = 0
		
	def check(self, setupObj):
		'''
		Verifies this testcase is to be runned for this setup
		'''
		
		# place holder for test specific method
		
		return True #Yes
	
	def checkattr(self):
		'''
		verifies that the testcase has the necessary attributes 
		'''
		return True #Yes

	def run(self, setupObj, exp):
		matchObj_secs = re.match(r'(\d+)s', exp, 0)
		matchObj_seeds = re.match(r'(\d+)', exp, 0)

		if matchObj_secs:
			seeds = None
			secs = int(matchObj_secs.group(1))
		elif matchObj_seeds:
			seeds = int(matchObj_seeds.group(1))
			secs = None
		else:
			print("ERROR: Unsupported EXP value")
			return 1  # error
		
		if not self.checkattr():
			log = ""
			log = self.printnlog("ERROR: missing attributes for test", log)
			self.write_log(log)
			self.stats["unknown"] += 1
			self.stats["seeds"] += 1
			self.print_stats()
			return 1
	
		result = self.run_body(setupObj, seeds, secs)
		self.print_stats()
		return result

	def clear_stats(self):
		self.stats["pass"] = 0
		self.stats["fail"] = 0
		self.stats["not_run"] = 0
		self.stats["unknown"] = 0
		self.stats["seeds"] = 0
		self.stats["secs"] = 0

	def print_stats(self):
		name_width = 35
		width = 10
		subject_list = ["Name", "Seeds", "Time [sec]", "Pass", "Fail", "Not run", "Unknown"]

		print()
		print("Cumulative test results")

		# title
		print("-" * ((name_width + 3) + ((len(subject_list) - 1) * (width + 3)) + 1))

		for position in range(0, len(subject_list)):
			string = str(subject_list[position])
			if position == 0:
				print("| " + string.ljust(name_width + 1), end='')
			else:
				print("| " + string.ljust(width + 1), end='')
		print("|")

		print("-" * ((name_width + 3) + ((len(subject_list) - 1) * (width + 3)) + 1))

		print("| " + self.name.ljust(name_width + 1), end='')
		value_list = [self.stats["seeds"], self.stats["secs"], self.stats["pass"], self.stats["fail"],
					  self.stats["not_run"], self.stats["unknown"]]
		for position in range(0, len(value_list)):
			string = str(value_list[position])
			print("| " + string.rjust(width) + " ", end='')
		print("|")

		print("-" * ((name_width + 3) + ((len(subject_list) - 1) * (width + 3)) + 1))
	
	def write_log(self, string):
		name = self.name.replace(" ", "_")
		log_file = os.path.join("c:", os.environ["HOMEPATH"], "Desktop\\logs\\atp\\%s_%s_%s.txt" % (self.unit, name, int(time.time())))
		log = devices.LOGGER(log_file, use_timestamps=False)
		log.append(string)

	def print_test_info(self, seed):
		log = ""
		print("")
		log = self.printnlog("-" * len(self.name), log)
		log = self.printnlog("Iteration: " + str(seed), log)
		log = self.printnlog("-" * len(self.name), log)
		# print("")
		return log
		
	def random_countdown(self, min, max, prefix="", echo=True):
		log = ""
		cooldown_time = round(random.uniform(min, max), 3)
		log = self.printnlog("%sSleeping for %0.3f [sec]" % (prefix, cooldown_time), log)
		
		try:
			while True:
				if echo: print(".", end="")
				if cooldown_time > 1: 
					time.sleep(1)
					cooldown_time -= 1
				else: 
					time.sleep(cooldown_time)
					break
					
		except KeyboardInterrupt:
			print("")
			log = self.printnlog("CTRL-C, aborting count", log)
		
		finally:
			if echo: print("")
			return log
			
	def sanity_test(self, setupObj):
		log = ""
		log = self.printnlog("Starting sanity tests", log)
		
		result = False #OK
		for obj in setupObj.seek_class(None): # all objects
			if hasattr(obj, "sanity_test"):
				error, inerlog = obj.sanity_test()
				result |= error # will become true if error
				log += inerlog
		
		log = self.printnlog("Sanity tests complete", log)
		return [result, log]
		
	def network_test(self, setupObj, retries=30):
		if not self.check_network: return [False, ""] # N/A
		
		log = ""
		log = self.printnlog("Starting networking test", log)
		net_dict = {} # net_dict[component] = [ (ip1, netmask1), (ip2, netmask2) ... (ipn, netmaskn) ]
		
		# ##########################
		# CHECK PC INETFACES
		# ##########################
		
		net_dict['pc'] = []
		nics = netifaces.interfaces()
		for nic in nics:
			ifaces = netifaces.ifaddresses(nic)
			for key in ifaces:
				if key == netifaces.AF_INET:  # IPv4
					iface = ifaces[key]
					for item in iface:
						if item['addr'] == '127.0.0.1': 
							continue # local host
						net_dict['pc'].append((item['addr'], item['netmask']))
						
		# ##########################
		# CHECK FSM INETFACES
		# ##########################
		
		for fsm in setupObj.seek_class(devices.FSM):
			net_dict[fsm] = []
			if (fsm.boot_state != fsm._sbl) and (fsm.boot_state != fsm._unknown): # boot to linux
				for key in fsm.network:
					net_dict[fsm].append(fsm.network[key]) # ip, netmask
										
		# ##########################
		# CHECK IMX INETFACES
		# ##########################
		
		for imx in setupObj.seek_class(devices.IMX):
			net_dict[imx] = []
			if (imx.boot_state != imx._uboot) and (imx.boot_state != imx._unknown): # boot to linux
				for key in imx.network:
					net_dict[imx].append(imx.network[key]) # ip, netmask
		
		# ##########################
		# CHECK UE INETFACES
		# ##########################
		
		for ue in setupObj.seek_base(devices.UE):
			net_dict[ue] = []
			
			# print("UE_BOOT_STATE: %s" % ue.boot_state)
			
			if hasattr(ue, "_uboot"):
				if (ue.boot_state == ue._uboot):
					continue # not in linux
					
			if hasattr(ue, "_reset"):
				if (ue.boot_state == ue._reset):
					continue # not in linux
					
			if hasattr(ue, "_unknown"):
				if (ue.boot_state == ue._unknown):
					continue # not in linux
			
			# in linux
			for key in ue.network:
				net_dict[ue].append(ue.network[key]) # ip, netmask
		
		# ##########################
		# PING ALL TO ALL
		# ##########################
		
		for key in net_dict: 
			string = "NET_DICT[%s]: %s" % (key, net_dict[key])
			log += "%s\n" % string
		
		key_list = [*net_dict]
		test_failed = False
		
		for index_1 in range(0, len(key_list)): 
			for index_2 in range(0, len(key_list)): 
				
				if index_1 == index_2: continue # don't ping yourself
				
				# print("KEY_1: %s" % key_list[index_1])
				# print("KEY_2: %s" % key_list[index_2])
				
				ifaces_1 = net_dict[key_list[index_1]]
				ifaces_2 = net_dict[key_list[index_2]]
								
				for iface_1 in ifaces_1:
					for iface_2 in ifaces_2:
						
						ip_1, netmask_1 = iface_1
						ip_2, netmask_2 = iface_2
						
						# print("IP_1: %s, MASK_1: %s" % (ip_1, netmask_1))
						# print("IP_2: %s, MASK_2: %s" % (ip_2, netmask_2))
						
						if netaddr.IPNetwork("%s/%s" % (ip_1, netmask_1)) == netaddr.IPNetwork("%s/%s" % (ip_2, netmask_2)):
							
							# ##########################
							# PING ALL FROM PC
							# ##########################
		
							if key_list[index_1] == "pc":
								string = "PING: PC to %s %s " % (key_list[index_2].name, ip_2)
								log += "%s" % string
								print(string, end='')
								
								try:
									for retry in range(0,retries):
										string = "."
										log += "%s" % string
										print(string, end='')
										response = os.system("ping -n 1 -w 1 %s" % ip_2)						
										if response == 0:					
											string = " OK"
											log += "%s\n" % string
											print(string)
											break
										else:
											if retry == (retries - 1): 
												string = " ERROR"
												log += "%s\n" % string
												print(string)
												test_failed = True # last chance
											time.sleep(1)
								
								except KeyboardInterrupt:
									string = "\nCTRL-C pressed, aborting"
									log += "%s\n" % string
									print(string)
									test_failed = True # last chance
									
							# ##########################
							# PING ALL FROM FSM, IMX
							# ##########################
							
							elif (isinstance(key_list[index_1], devices.FSM) or isinstance(key_list[index_1], devices.IMX)) :
								if key_list[index_2] == 'pc': 
									dest_name = 'PC'
								else:
									dest_name = key_list[index_2].name
								
								string = "PING: %s to %s %s " % (key_list[index_1].name, dest_name, ip_2)
								print(string, end='')
								log += "%s" % string
								
								try:
									for retry in range(0,retries):
										string = "."
										print(string, end='')
										log += "%s" % string
										dev = key_list[index_1]
										result = dev.send_waitn("ping %s -c 1 -W 1\n" % ip_2, ["1 packets received", "0 packets received", "#"], 3, echo=False)
										if result[0] == 1: 
											string = " OK"
											log += "%s\n" % string
											print(string)
											break
										else:
											if retry == (retries - 1): 
												string = " ERROR"
												log += "%s\n" % string
												print(string)
												print(result[1])
												log += "%s\n" % result[1]
												test_failed = True # last chance
											time.sleep(1)
											
								except KeyboardInterrupt:
									string = "\nCTRL-C pressed, aborting"
									log += "%s\n" % string
									print(string)
									test_failed = True # last chance
							
							# ##########################
							# PING ALL FROM UE
							# ##########################
							
							elif (isinstance(key_list[index_1], devices.UE_ALTAIR) or isinstance(key_list[index_1], devices.UE_GCT)) :
								if key_list[index_2] == 'pc': 
									dest_name = 'PC'
								else:
									dest_name = key_list[index_2].name
								
								string = "PING: %s to %s %s " % (key_list[index_1].name, dest_name, ip_2)
								print(string, end='')
								log += "%s" % string
								
								try:
									for retry in range(0,retries):
										string = "."
										print(string, end='')
										log += "%s" % string
										dev = key_list[index_1]
										result = dev.send_waitn("ping %s -c 1 -W 1\n" % ip_2, ["1 packets received", "0 packets received", "#"], 3, echo=False)
										if result[0] == 1: 
											string = " OK"
											log += "%s\n" % string
											print(string)
											break
										else:
											if retry == (retries - 1): 
												string = " ERROR"
												log += "%s\n" % string
												print(string)
												print(result[1])
												log += "%s\n" % result[1]
												test_failed = True # last chance
											time.sleep(1)
								
								except KeyboardInterrupt:
									string = "\nCTRL-C pressed, aborting"
									log += "%s\n" % string
									print(string)
									test_failed = True # last chance
						
		print("Networking test complete")
		return (test_failed, log)
	
	def power_test(self, setupObj):
		if not (self.check_power): return [False, ""] # N/A
		
		log = ""
		print("")
		log = self.printnlog("Starting Power test", log)
		
		self.random_countdown(self.delay_power_check, self.delay_power_check) # for countdown on screen of fixed time
		
		# calculate all PSU power
		power_sum = 0
		for psuObj in setupObj.seek_base(devices.EXTERNAL_PSU):
			
			if type(psuObj) is devices.KIKUSUI_PCR:	
				power_key = "P_RMS"
			elif type(psuObj) is devices.LAMBDA_GEN: 
				power_key = "power"
			else:
				log = self.printnlog("Error: PSU has no power measurment", log)
				return [True, log] # error
			
			while True:	# robust until value is returned
				dict = psuObj.get_power()
				result = dict[psuObj, power_key][0]
				if result != "":
					power_sum += result
					break
				else:
					log = self.printnlog("Failed to get power from %s" % psuObj.name, log)
		
		if ((power_sum > self.max_power) or (power_sum < self.min_power)):
			log = self.printnlog("Power is off limit: allowed between %s to %s, measured is %s" % (self.min_power, self.max_power, power_sum),log)
			return [True, log] # error
		
		log = self.printnlog("Power test complete", log)

		return [False, log] # OK

	def rf_test(self, setupObj):
		if not (self.check_rf): return [False, ""] # N/A
		if setupObj.seek_base(devices.AGILENT_4418B_POWER_METER) == []: return [False, ""] # N/A
		
		log = ""
		print("")
		log = self.printnlog("Starting RF test", log)
		
		self.random_countdown(self.delay_rf_check, self.delay_rf_check) # for countdown on screen of fixed time
		
		# calculate all PSU power
		rf_sum = 0
		for obj in setupObj.seek_base(devices.AGILENT_4418B_POWER_METER):
			
			while True:	# robust until value is returned
				dict = obj.get_power()
				result = dict[obj, "power"][0]
				if result != "":
					rf_sum += result
					break
				else:
					log = self.printnlog("Failed to get power from %s" % obj.name, log)
		
		if ((rf_sum > self.max_rf) or (rf_sum < self.min_rf)):
			log = self.printnlog("RF power is off limit: allowed between %s to %s, measured is %s" % (self.min_rf, self.max_rf, rf_sum),log)
			return [True, log] # error
		
		log = self.printnlog("RF test complete", log)

		return [False, log] # OK
		
	def power_cycle(self, setupObj, min_time, max_time, boot=True):
		log = ""
		for obj in setupObj.seek_base(devices.EXTERNAL_PSU): 
			error, inerlog = obj.off()
			log += inerlog
			if error: return [True, log] # error
				
		log += self.random_countdown(min_time, max_time)

		for obj in setupObj.seek_base(devices.EXTERNAL_PSU): 
			if (hasattr(obj,"volt")): log = self.printnlog("V=%f" % obj.volt, log)
			if (hasattr(obj,"curr")): log = self.printnlog("I=%f" % obj.curr, log)
			if (hasattr(obj,"freq")): log = self.printnlog("F=%f" % obj.freq, log)
			log += "\n"
			
			error, inerlog = obj.on()
			log += inerlog
			if error: return [True, log] # error
			
		if boot:
			inerlog = self.printnlog("Booting setup", log)
			error, inerlog = setupObj.boot()
			if error: 
				log += inerlog
				return [True, log] # error
			
		return [False, log] # OK
	
	def masters_to_linux(self, setupObj):
		for fsm in setupObj.seek_class(devices.FSM):
			if (fsm.boot_type == fsm._unknown) or (fsm.boot_type == fsm._sbl):
				fsm.boot_type = fsm._linux_b0 # default
							
		for imx in setupObj.seek_class(devices.IMX):
			if (imx.boot_type == imx._unknown) or (imx.boot_type == imx._uboot):
				imx.boot_type = imx._linux_b0 # default
	
		for xlp in setupObj.seek_class(devices.XLP):
			if (xlp.boot_type == xlp._unknown) or (xlp.boot_type == xlp._xloader) or (xlp.boot_type == xlp._uboot):
				xlp.boot_type = xlp._linux_b0 # default
		return True
	
	def stop_on_fail_method(self):
		SERVER = "fs8.airspan.com"
		FROM = "dguser@airspan.com"
		TO = ["ddekel@Airspan.com", "swolfperez@Airspan.com", "asharon@Airspan.com"] # must be a list
		SUBJECT = "%s stopped on fail" % self.name
		TEXT = "unit is: %s" % self.unit
		# Prepare actual message
		# keep all empty lines and tabs as is until the comment "here."
		message = """From: %s\r\nTo: %s\r\nSubject: %s\r\n\

		%s
		""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
		# here.
		server = smtplib.SMTP(SERVER)
		server.sendmail(FROM, TO, message)
		server.quit()	
		
		val = input("Stopped on fail - Press any key to continue test")

class reboot_thread(devices.UTILITY, threading.Thread):

	def __init__(self, name, obj, father):
		# print("Constructing a THREAD: %s %s\n" % (name, str(obj)), end='')
		threading.Thread.__init__(self)
		devices.UTILITY.__init__(self)
		self.name = name
		self.obj = obj
		self.err = False
		self.result = -1
		self.father = father
		self.log = ""

	def run(self):		
		try:
			inerlog = self.father.random_countdown(self.father.min_time, self.father.max_time, prefix="%s " % self.obj.name, echo=False)
			self.log += inerlog
			
			error = self.obj.reboot()
			if error:
				self.result = 1 # error
				return
				
			self.result, inerlog = self.obj.boot()
			self.log += inerlog
			
			return
			
		except:
			self.err = True
			self.log = self.printnlog(traceback.format_exc(), self.log)
			return
		
# ######################################################################		
# ######################################################################		
# ######################################################################		
# 							BASIC TESTS
# ######################################################################		
# ######################################################################		
# ######################################################################		

class random_result_test(testcase):

	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Random result test"

	def run_body(self, setupObj, seeds, secs):

		if secs != None: end_time = int(time.time()) + secs
		seed = 0

		try:
		
			while True:
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
				
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog

				run_result = random.randint(0, 3)

				print("RESULT = " + str(run_result))
				# print("SELF = " + str(self))
				# print("STATS = " + str(self.stats))

				print("")
				
				if run_result == 0:
					print("TEST PASSED !!!")
					self.stats["pass"] += 1
				elif run_result == 1:
					print("TEST FAILED !!!")
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
				else:
					print("TEST UNKNOWN !!!")
					self.stats["unknown"] += 1

				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)
				
		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")

		except:
			print(traceback.format_exc())
		# self.print_stats()
		return 0  # ok

class master_cpu_ddr_test(testcase):
	
	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Master CPU DDR test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 25  # cooldown time between cycles
		
	def check(self, setupObj):
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
	
		if len(setupObj.seek_class(devices.FSM)) > 0: return True # apply
		# if len(setupObj.seek_class(devices.IMX)) > 0: return True # apply
		return False # don't apply
		
	def run_body(self, setupObj, seeds, secs):
			
		if secs != None: end_time = int(time.time()) + secs
		seed = 0
		
		try:
			while True:
				log = ""
								
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
				
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				for fsm in setupObj.seek_class(devices.FSM):
					string = "Setting %s boot_type to SBL" % fsm.name
					print(string)
					log += "%s\n" % string
					fsm.boot_type = fsm._sbl
				
				for imx in setupObj.seek_class(devices.IMX):
					string = "Setting %s boot_type to UBOOT" % imx.name
					print(string)
					log += "%s\n" % string
					imx.boot_type = imx._uboot
					
				while True:
					error, inerlog = self.power_cycle(setupObj, self.min_time, self.max_time)
					if error:
						log += inerlog
						log = self.printnlog("Failed to power cycle", log)
					else:
						break
				
				failed_flag = False
				unknown_flag = False
				for fsm in setupObj.seek_class(devices.FSM):
					string = "\nChecking %s" % fsm.name
					print(string)
					log += "%s\n" % string
					
					# Long memory test
					# Testing data lines at 00000000 size=20000000
					# Done
					# Testing addr lines at 00000000 size=20000000
					# Done
					# Testing "own addr" at 00000000 size=20000000
					# Filling direct data
					# ................................................................
					# Checking direct data base=00000000 size=1fffffff

					# Filling negated data
					# ................................................................
					# Checking negated data

					# Done
					# DDR is OK
									
					result = fsm.send_waitn("ddrtest long\n", [r"SBL\d+"], 60, echo=True)
					log += "%s\n" % str(result[1])
					
					print("")
					log += "\n"
					
					if result[0] != 1:  # timeout or error
						string = "UNKNOWN !!!"
						print(string)
						log += "%s\n" % string
						self.write_log(log)
						self.stats["unknown"] += 1
						# self.stats["seeds"] += 1
						# self.stats["secs"] += (int(time.time()) - start_time)
						unknown_flag = True
						continue
					
					if not re.search(r"Testing data lines at \S+ size=\S+\n\rDone", result[1], 0):
						string = "FAILED !!!"
						print(string)
						log += "%s\n" % string
						self.write_log(log)
						self.stats["fail"] += 1
						# self.stats["seeds"] += 1
						# self.stats["secs"] += (int(time.time()) - start_time)
						failed_flag = True
						continue
		
					if not re.search(r"Testing addr lines at \S+ size=\S+\n\rDone", result[1], 0):
						string = "FAILED !!!"
						print(string)
						log += "%s\n" % string
						self.write_log(log)
						self.stats["fail"] += 1
						# self.stats["seeds"] += 1
						# self.stats["secs"] += (int(time.time()) - start_time)
						failed_flag = True
						continue
		
					if not re.search(r"DDR is OK", result[1], 0):
						string = "FAILED !!!"
						print(string)
						log += "%s\n" % string
						self.write_log(log)
						self.stats["fail"] += 1
						# self.stats["seeds"] += 1
						# self.stats["secs"] += (int(time.time()) - start_time)
						failed_flag = True
						continue
				
				for imx in setupObj.seek_class(devices.IMX):
					string = "\nTBD - Checking %s" % imx.name
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
					
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag: 
					print("TEST FAILED !!!") 
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
				if unknown_flag: print("TEST UNKNOWN !!!")
				if (not failed_flag) and (not unknown_flag): 
					print("TEST PASSED !!!")
					self.stats["pass"] += 1
				
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)
				
		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print(traceback.format_exc())

		# self.print_stats()
		return 0  # ok
	
class slave_cpu_ddr_test(testcase):
	
	class MYTHREAD(devices.UTILITY, threading.Thread):

		def __init__(self, name, obj):
			threading.Thread.__init__(self)
			devices.UTILITY.__init__(self)
			self.name = name
			self.obj = obj
			self.err = False
			self.result = -1
			self.log = ""

		def run(self):
			self.err = False
			try: # we come here after releasing from reset. so we wait for boot to end in parallel.
				self.obj.boot()
				self.result, self.log = self.obj.check_ddr()
			except:
				print(traceback.format_exc())
				self.err = True

	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Slave CPU DDR test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 25  # cooldown time between cycles
		
	def check(self, setupObj):
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
	
		if len(setupObj.seek_class(devices.DAN)) > 0: return True # apply
		# if len(setupObj.seek_class(devices.UE)) > 0: return True # apply
		return False # don't apply
		
	def run_body(self, setupObj, seeds, secs):
		
		power_cycle_done = False

		if secs != None: end_time = int(time.time()) + secs
		seed = 0
		
		try:
			while True:								
				threads = []
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
				
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				if not power_cycle_done:
					for dan in setupObj.seek_class(devices.DAN):
						log = self.printnlog("Setting %s boot_type to UMOM" % dan.name, log)
						dan.boot_type = dan._uboot
					while True:
						error, inerlog = self.power_cycle(setupObj, self.min_time, self.max_time)
						if error:
							log += inerlog
							log = self.printnlog("Failed to power cycle", log)
						else:
							power_cycle_done = True
							break

				for dan in setupObj.seek_class(devices.DAN):
					threads.append(self.MYTHREAD(dan.name + "DDR test", dan))
					dan.reset(True)
					time.sleep(0.5) # neccesery to prevent race for same XLP
					dan.boot_type = dan._uboot
					dan.reset(False)					

				for ue in setupObj.seek_class(devices.UE): print ("/nTBD - Checking %s DDRs" % ue.name)
				
				failed_flag = False
				unknown_flag = False
				notrun_flag = False
				
				for thread in threads: thread.start()
				
				while True: # poll untill all threads die
					found_alive = False
					
					for thread in threads:
						thread.join(1) # check once a second the thread status
						if thread.is_alive(): 
							found_alive = True
							break
				
					if not found_alive: break
				
				for thread in threads:
					log = self.printnlog("thread result is: %s"% thread.result, log)
					if thread.result == -1:
						log = self.printnlog("NOT RUN", log)
						notrun_flag = True
						continue
					if thread.result == 1:
						log = self.printnlog("UNKNOWN!", log)
						unknown_flag = True
						continue
					elif thread.result == 2:
						log = self.printnlog("FAIL!", log)
						failed_flag = True
						continue
								
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if notrun_flag: 
					self.stats["not_run"] += 1
					print("TEST FAILED !!!")
				if failed_flag:
					self.stats["fail"] += 1
					print("TEST FAILED !!!")
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
				if unknown_flag: 
					self.stats["unknown"] += 1
					print("TEST UNKNOWN !!!")
				if (not failed_flag) and (not unknown_flag) and (not notrun_flag): 
					print("TEST PASSED !!!")
					self.stats["pass"] += 1
				
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)
				
		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print(traceback.format_exc())

		return 0  # ok

class suicide_test(testcase):
	
	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "System suicide test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 25  # cooldown time between cycles
		
		# network testing arguments
		self.check_network = True
		
	def check(self, setupObj):
		if setupObj.seek_class(devices.SUICIDE) == []: return False
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		return True
	
	def run_body(self, setupObj, seeds, secs):
		
		if secs != None: end_time = int(time.time()) + secs
		seed = 0
		
		try:
			
			power_cycle_required = True
			
			while True:
			
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
				
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				if power_cycle_required: # power cycle and boot - assure success !!! robust recovery
					while True:
						error, inerlog = self.power_cycle(setupObj, 1, 1)
						if error:
							log += inerlog
							log = self.printnlog("Failed to power cycle", log)
						else:
							power_cycle_required = False
							break
				
				flag = False
				for suicide in setupObj.seek_class(devices.SUICIDE):
					string = "\nCommiting suicide through %s" % suicide.fatherObj.name
					log += "%s\n" % string
					if suicide.suicide():
						flag = True
						break
				
				if flag:
					log = self.printnlog("TEST UNKNOWN !!!", log)
					self.write_log(log)
					self.stats["unknown"] += 1
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					power_cycle_required = True
					continue
											
				log = self.printnlog("Booting setup", log)
				result, inerlog = setupObj.boot()
				if result:
					log += inerlog
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					power_cycle_required = True
					continue
				
				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.network_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True

				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)
												
		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print(traceback.format_exc())

		# self.print_stats()
		return 0  # ok

class power_cycle_test(testcase):

	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Staggered power cycle test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 25  # cooldown time between cycles
		
		# network testing arguments
		self.check_network = True
	
	def check(self, setupObj):
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		return True
		
	def run_body(self, setupObj, seeds, secs):
		
		if secs != None: end_time = int(time.time()) + secs
		seed = 0

		try:
		
			while True:
				log = ""
			
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				while True:
					error, inerlog = self.power_cycle(setupObj, self.min_time, self.max_time, boot=False)
					if error:
						log += inerlog
						log = self.printnlog("Failed to power cycle", log)
					else:
						break
								
				error, inerlog = setupObj.boot()
				if error:
					log += inerlog
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue

				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.network_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True				
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag: 
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)
				
		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class master_cpu_reboot_test(testcase):
	
	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Stagered master CPU reboot test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 30  # cooldown time between cycles
		self.check_network = True # network testing arguments		
	
	def check(self, setupObj):
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		return True
		
	def run_body(self, setupObj, seeds, secs):

		if secs != None: end_time = int(time.time()) + secs
		seed = 0

		try:
			
			power_cycle_required = True
			while True:
				
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				# Power cycle
				if power_cycle_required: # power cycle and boot - assure success !!! robust recovery
					while True:
						error, inerlog = self.power_cycle(setupObj, 1, 1)
						if error:
							log += inerlog
							log = self.printnlog("Failed to power cycle", log)
						else:
							power_cycle_required = False
							break
				
				
				# ################################
				# Threaded reboot + boot to all CPUs
				# ################################
				
				print("")
				threads = []
				ignore_list = []
				
				for fsm in setupObj.seek_class(devices.FSM):
					if (fsm.boot_type == fsm._unknown) or (fsm.boot_type == fsm._sbl):
						fsm.boot_type = fsm._linux_b0 # default
						
					ignore_list.append(fsm)
					thread = reboot_thread("%s reboot" % fsm.name, fsm, self)
					threads.append(thread)
				
				for imx in setupObj.seek_class(devices.IMX):
					if (imx.boot_type == imx._unknown) or (imx.boot_type == imx._uboot):
						imx.boot_type = imx._linux_b0 # default
					
					ignore_list.append(imx)
					thread = reboot_thread("%s reboot" % imx.name, imx, self)
					threads.append(thread)
				
				for xlp in setupObj.seek_class(devices.XLP):
					if (xlp.boot_type == xlp._unknown) or (xlp.boot_type == xlp._xloader) or (xlp.boot_type == xlp._uboot):
						xlp.boot_type = xlp._linux_b0 # default
					
					ignore_list.append(xlp)
					thread = reboot_thread("%s reboot" % xlp.name, xlp, self)
					threads.append(thread)
				
				for thread in threads:
					thread.start()
				
				found_alive = True
				while found_alive: # poll until all threads die
					found_alive = False
					for thread in threads:
						thread.join(1) # check once a second the thread status
						if thread.is_alive(): 
							found_alive = True
							break
				
				test_failed = False
				
				for thread in threads:
					print("INFO: Thread exit status of " + thread.name + " is " + str(thread.result))
					if thread.result != 0:
						log += thread.log
						print("ERROR: Thread exit status")
						print ("ERROR: Boot sequence failed, exiting")
						log += str(thread.result)
						test_failed = True
				
				for thread in threads:
					if thread.err:
						print("ERROR: Thread exception at" + thread.name)
						print ("ERROR: Boot sequence failed, exiting")
						test_failed = True
						
				if test_failed:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					power_cycle_required = True
					continue
				
				# ################################
				# END - Threaded reboot + boot to all CPUs
				# ################################
											
				print("")
				
				# for ue in setupObj.seek_base(devices.UE):
					# ue.boot_state = ue._unknown # not sure that all required operations performed
				
				log = self.printnlog("Continue boot", log)
				result, inerlog = setupObj.boot(ignore_obj_list=ignore_list) # boot slaves
				if result != 0:
					log += inerlog
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.network_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True			
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)

		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class au587_booter_switch_id_test(testcase):

	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Booter switch ID test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 5  # cooldown time between cycles
	
	def check(self, setupObj):
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		if (self.unit != "AU587") and (self.unit != "AU587_IMX"): return False
		return True
		
	def run_body(self, setupObj, seeds, secs):

		if secs != None: end_time = int(time.time()) + secs
		seed = 0
		
		for imx in setupObj.seek_class(devices.IMX):
			imx.boot_type = imx._uboot
		
		try:
		
			while True:
				
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog

				while True:
					error, inerlog = self.power_cycle(setupObj, self.min_time, self.max_time)
					if error:
						log += inerlog
						log = self.printnlog("Failed to power cycle", log)
					else:
						break
				
				failed_flag = False
				for imx in setupObj.seek_class(devices.IMX):
					result = imx.send_waitn("mdio read 0x13 0x3\n", ["0x1152"], 2)
					for line in result[1].split("\n"): print(line)
					if result[0] != 1: 
						print("ERROR: failed to read ID")
						failed_flag = True
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)

		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class sanity_test(testcase):

	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Sanity test"
		# self.min_time = 1  # cooldown time between cycles
		# self.max_time = 1  # cooldown time between cycles
		
		# network testing arguments
		self.check_network = False
	
	def check(self, setupObj):
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		return True
		
	def run_body(self, setupObj, seeds, secs):
		if secs != None: end_time = int(time.time()) + secs
		seed = 0
				
		try:
			log = ""
			
			while True:
					error, inerlog = self.power_cycle(setupObj, 1, 1)
					if error:
						log += inerlog
						log = self.printnlog("Failed to power cycle", log)
					else:
						break
				
			while True:
				
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				start_time = int(time.time())

				log += self.print_test_info(seed)
				
				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True				

				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True				
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")

				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)

		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class slave_cpu_reboot_test(testcase):
	
	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Stagered slave CPU reboot test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 30  # cooldown time between cycles
	
		# network testing arguments
		self.check_network = True
	
	def check(self, setupObj): # test if the te
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		if setupObj.seek_base(devices.DAN) == [] and setupObj.seek_base(devices.UE) == []: return False
		return True
		
	def run_body(self, setupObj, seeds, secs):

		if secs != None: end_time = int(time.time()) + secs
		seed = 0

		try:
			
			power_cycle_required = True
			while True:
				
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				self.masters_to_linux(setupObj)

				# Power cycle
				if power_cycle_required: # power cycle and boot - assure success !!! robust recovery
					while True:
						error, inerlog = self.power_cycle(setupObj, 1, 1)
						if error:
							log += inerlog
							log = self.printnlog("Failed to power cycle", log)
						else:
							power_cycle_required = False
							break
								
				# ################################
				# Threaded reboot + boot to all CPUs
				# ################################
				
				print("")
				threads = []
				
				for ue in setupObj.seek_base(devices.UE):
					if (ue.boot_type == ue._unknown) or (ue.boot_type == ue._reset) or (ue.boot_type == ue._uboot): # currently compatible to ALTAIR and GCT UEs 
						ue.boot_type = ue._linux_bx # default
																
					thread = reboot_thread("%s reboot" % ue.name, ue, self)
					threads.append(thread)
					
				for dan in setupObj.seek_class(devices.DAN):
					if (dan.boot_type == dan._unknown) or (dan.boot_type == dan._reset) or (dan.boot_type == dan._uboot):
						dan.boot_type = dan._linux # default
																
					thread = reboot_thread("%s reboot" % dan.name, dan, self)
					threads.append(thread)
				
				for thread in threads:
					thread.start()
				
				found_alive = True
				while found_alive: # poll untill all threads die
					found_alive = False
					for thread in threads:
						thread.join(1) # check once a second the thread status
						if thread.is_alive(): 
							found_alive = True
							break
				
				test_failed = False
				
				for thread in threads:
					print("INFO: Thread exit status of " + thread.name + " is " + str(thread.result))
					if thread.result != 0:
						log += thread.log
						print("ERROR: Thread exit status")
						print ("ERROR: Boot sequence failed, exiting")
						log += str(thread.result)
						test_failed = True
				
				for thread in threads:
					if thread.err:
						print("ERROR: Thread exception at" + thread.name)
						print ("ERROR: Boot sequence failed, exiting")
						test_failed = True
						
				if test_failed:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					power_cycle_required = True
					continue
				
				# ################################
				# END - Threaded reboot + boot to all CPUs
				# ################################
											
				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.network_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True			
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)

		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class slave_cpu_reset_test(testcase):
	
	class reset_thread(devices.UTILITY, threading.Thread):

		def __init__(self, name, obj, father):
			# print("Constructing a THREAD: %s %s\n" % (name, str(obj)), end='')
			threading.Thread.__init__(self)
			devices.UTILITY.__init__(self)
			self.name = name
			self.obj = obj
			self.err = False
			self.result = -1
			self.father = father
			self.log = ""

		def run(self):
						
			try:
				inerlog = self.father.random_countdown(self.father.min_time, self.father.max_time, prefix="%s " % self.obj.name, echo=False)
				self.log += inerlog
				
				error = self.obj.reset(True)
				time.sleep(1)
				error = self.obj.reset(False)
				if error: 
					self.result = 1 # error
					return
					
				self.result, inerlog = self.obj.boot()
				self.log += inerlog
				return
				
			except:
				self.err = True
				self.log = self.printnlog(traceback.format_exc(), self.log)
				return
		
	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Stagered slave CPU reset test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 30  # cooldown time between cycles
	
		# network testing arguments
		self.check_network = True
	
	def check(self, setupObj): # test if the te
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False
		if setupObj.seek_base(devices.DAN) == [] and setupObj.seek_base(devices.UE) == []: return False
		return True
		
	def run_body(self, setupObj, seeds, secs):

		if secs != None: end_time = int(time.time()) + secs
		seed = 0

		try:
			
			power_cycle_required = True
			while True:
				
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				log = ""
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				self.masters_to_linux(setupObj)
				
				# Power cycle
				if power_cycle_required: # power cycle and boot - assure success !!! robust recovery
					while True:
						error, inerlog = self.power_cycle(setupObj, 1, 1)
						if error:
							log += inerlog
							log = self.printnlog("Failed to power cycle", log)
						else:
							power_cycle_required = False
							break
								
				# ################################
				# Threaded reboot + boot to all CPUs
				# ################################
				
				print("")
				threads = []
				
				for ue in setupObj.seek_base(devices.UE):
					if (ue.boot_type == ue._unknown) or (ue.boot_type == ue._reset) or (ue.boot_type == ue._uboot): # currently compatible to ALTAIR and GCT UEs 
						ue.boot_type = ue._linux_bx # default
																
					thread = self.reset_thread("%s reset" % ue.name, ue, self)
					threads.append(thread)
					
				for dan in setupObj.seek_class(devices.DAN):
					if (dan.boot_type == dan._unknown) or (dan.boot_type == dan._reset) or (dan.boot_type == dan._uboot):
						dan.boot_type = dan._linux # default
																
					thread = self.reset_thread("%s reset" % dan.name, dan, self)
					threads.append(thread)
				
				for thread in threads:
					thread.start()
				
				found_alive = True
				while found_alive: # poll untill all threads die
					found_alive = False
					for thread in threads:
						thread.join(1) # check once a second the thread status
						if thread.is_alive(): 
							found_alive = True
							break
				
				test_failed = False
				
				for thread in threads:
					print("INFO: Thread exit status of " + thread.name + " is " + str(thread.result))
					if thread.result != 0:
						log += thread.log
						print("ERROR: Thread exit status")
						print ("ERROR: Boot sequence failed, exiting")
						log += str(thread.result)
						test_failed = True
				
				for thread in threads:
					if thread.err:
						print("ERROR: Thread exception at" + thread.name)
						print ("ERROR: Boot sequence failed, exiting")
						test_failed = True
						
				if test_failed:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					power_cycle_required = True
					continue
				
				# ################################
				# END - Threaded reset + boot to Slave CPUs
				# ################################
											
				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.network_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True			
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)

		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class slave_cpu_power_enable_test(testcase):
	
	class power_en_thread(devices.UTILITY, threading.Thread):
		
		def __init__(self, name, obj, father):
			# print("Constructing a THREAD: %s %s\n" % (name, str(obj)), end='')
			threading.Thread.__init__(self)
			devices.UTILITY.__init__(self)
			self.name = name
			self.obj = obj
			self.err = False
			self.result = -1
			self.father = father
			self.log = ""

		def run(self):
			# print("Starting thread " + self.name + "\n", end='')
			# self.print_info()
			
			try:
				inerlog = self.father.random_countdown(self.father.min_time, self.father.max_time, prefix="%s " % self.obj.name, echo=False)
				self.log += inerlog
				
				# self.log = self.printnlog("%s: Power cycling" % self.obj.name, self.log)
				error = self.obj.power_en(False)
				time.sleep(1)
				error = self.obj.power_en(True)
				if error: 
					# self.log = self.printnlog("failed to power cycle %s " % self.obj.name, self.log)
					self.result = 1 # error
					return
					
				# self.log = self.printnlog("Booting %s" % self.obj.name, self.log)
				self.result, inerlog = self.obj.boot()
				self.log += inerlog
				
				# print("Exiting thread %s\n" % self.name, end='')
				return
				
			except:
				self.err = True
				self.log = self.printnlog(traceback.format_exc(), self.log)
				return

	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Stagered slave CPU Power_en test"
		self.min_time = 0  # cooldown time between cycles
		self.max_time = 15  # cooldown time between cycles
	
		# network testing arguments
		self.check_network = True
	
	def check(self, setupObj): # test if the te
		if setupObj.seek_base(devices.EXTERNAL_PSU) == []: return False

		for obj in setupObj.seek_base(devices.DAN): 
			if hasattr(obj,"power_en"): return True
		
		for obj in setupObj.seek_base(devices.UE): 
			if hasattr(obj,"power_en"): return True

		return False # no Slave with Power_en option found 
		
	def run_body(self, setupObj, seeds, secs):
		log = ""

		if secs != None: end_time = int(time.time()) + secs
		seed = 0

		try:
			
			power_cycle_required = True
			while True:
				
				if (seed != 0) and (seed != seeds): self.print_stats()
				
				if (seeds != None) and (seed >= seeds):
					print("Seeds end point reached, exiting")
					break

				if (secs != None) and (int(time.time()) >= end_time):
					print("Time end point reached, exiting")
					break
					
				seed += 1
				start_time = int(time.time())

				inerlog = self.print_test_info(seed)
				log += inerlog
				
				self.masters_to_linux(setupObj)

				# Power cycle
				if power_cycle_required: # power cycle and boot - assure success !!! robust recovery
					while True:
						error, inerlog = self.power_cycle(setupObj, 1, 1)
						if error:
							log += inerlog
							log = self.printnlog("Failed to power cycle", log)
						else:
							power_cycle_required = False
							break
								
				# ################################
				# Threaded reboot + boot to all CPUs
				# ################################
				
				print("")
				threads = []
				
				for ue in setupObj.seek_base(devices.UE):
					if (ue.boot_type == ue._unknown) or (ue.boot_type == ue._reset) or (ue.boot_type == ue._uboot): # currently compatible to ALTAIR and GCT UEs 
						ue.boot_type = ue._linux_bx # default
																
					thread = self.power_en_thread("%s Power_en" % ue.name, ue, self)
					threads.append(thread)
					
				for dan in setupObj.seek_class(devices.DAN):
					if (dan.boot_type == dan._unknown) or (dan.boot_type == dan._reset) or (dan.boot_type == dan._uboot):
						dan.boot_type = dan._linux # default
																
					thread = self.power_en_thread("%s Power_en" % dan.name, dan, self)
					threads.append(thread)
				
				for thread in threads:
					thread.start()
				
				found_alive = True
				while found_alive: # poll untill all threads die
					found_alive = False
					for thread in threads:
						thread.join(1) # check once a second the thread status
						if thread.is_alive(): 
							found_alive = True
							break
				
				test_failed = False
				
				for thread in threads:
					print("INFO: Thread exit status of " + thread.name + " is " + str(thread.result))
					if thread.result != 0:
						log += thread.log
						print("ERROR: Thread exit status")
						print ("ERROR: Boot sequence failed, exiting")
						log += str(thread.result)
						test_failed = True
				
				for thread in threads:
					if thread.err:
						print("ERROR: Thread exception at" + thread.name)
						print ("ERROR: Boot sequence failed, exiting")
						test_failed = True
						
				if test_failed:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					power_cycle_required = True
					continue
				
				# ################################
				# END - Threaded reboot + boot to all CPUs
				# ################################
											
				failed_flag = False
				
				error, inerlog = self.sanity_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.network_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True
				
				error, inerlog = self.power_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True			
				
				error, inerlog = self.rf_test(setupObj)
				if error:
					log += inerlog
					failed_flag = True	
				
				print("")
				
				if failed_flag:
					log = self.printnlog("TEST FAILED !!!", log)
					self.write_log(log)
					self.stats["fail"] += 1
					if self.stop_on_fail and (self.stats["fail"] >= self.count_to_fail): self.stop_on_fail_method()
					self.stats["seeds"] += 1
					self.stats["secs"] += (int(time.time()) - start_time)
					continue
				
				print("TEST PASSED !!!")
				self.stats["pass"] += 1
				self.stats["seeds"] += 1
				self.stats["secs"] += (int(time.time()) - start_time)

		except KeyboardInterrupt:
			print("\nCTRL-C, test aborted")
			
		except:
			print("errors occurred")
			print(traceback.format_exc())
			return {}  # ERROR

		# self.print_stats()
		return 0  # ok

class ex_test(testcase):
	def __init__(self, unit):
		testcase.__init__(self, unit)
		self.name = "Ex_test"
		self.min_time = 1  # cooldown time between cycles
		self.max_time = 2  # cooldown time between cycles
	
	def run_body(self, setupObj, seeds=True, secs=True):
		oven_obj = setupObj.seek_class(devices.WALTOW_EZ_ZONE_CONTROLLER)
		while True:
			oven_obj[0].set_temp(80)
			time.sleep(10)
			oven_obj[0].set_temp(-55)
			time.sleep(20)

	def check(self, setupObj):
		if len(setupObj.seek_class(devices.FSM)) > 0: return True # apply
		return False

# EMMC stress test

# ESIM test

# USIM test
	
# ######################################################################		
# ######################################################################		
# ######################################################################		
# 							COMPOSITE TESTS
# ######################################################################		
# ######################################################################		
# ######################################################################		

class delayed_power_cycle_test(power_cycle_test):
	
	def __init__(self, unit):
		power_cycle_test.__init__(self, unit)
		self.name = "Delayed 3h power cycle test"
		self.min_time = 3 * 60 * 60  # cooldown time between cycles
		self.max_time =  3 * 60 * 60  # cooldown time between cycles

class delayed_30m_power_cycle_test(power_cycle_test):
	
	def __init__(self, unit):
		power_cycle_test.__init__(self, unit)
		self.name = "Delayed 30m power cycle test"
		self.min_time = 30 * 60   # cooldown time between cycles
		self.max_time = 30 * 60  # cooldown time between cycles
