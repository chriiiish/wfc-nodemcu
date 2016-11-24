import time
import machine
import network
import json
try:
	from umqtt.robust import MQTTClient
except Exception as err:
	print("ERROR LOADING UMQTT")
	print(err)
	print("TRYING AGAIN IN 10 SECONDS")
	time.sleep(10)
	from umqtt.robust import MQTTClient


# =========================== VARIABLES

clientName = "Unassigned"
mqttServerAddress = "Unassigned"
channelName = "Unassigned"
wifiName = "Unassigned"
wifiPass = "Unassigned"

ledRed = machine.PWM(machine.Pin(5))
ledGreen = machine.PWM(machine.Pin(4))
ledBlue = machine.PWM(machine.Pin(2))
ledPurple = machine.PWM(machine.Pin(14))
ledWhite = machine.PWM(machine.Pin(12))

inSpecial = False

client = None

# /VARIABLES ==========================

# =========================== FUNCTIONS

# Pulls the settings from config.json
def getSettings():
	print("Retrieving Settings from Config File")
	global clientName, mqttServerAddress, channelName, wifiName, wifiPass
	obj = {}
	# Get config file
	try:
		with open("config.json") as json_data:
			obj = json.load(json_data)
	except:
		print("Error loading config.json file")
		showError(ledWhite)
		return False
	
	# Get settings
	try:
		clientName = obj["mqtt_clientid"]
		mqttServerAddress = obj["mqtt_server"]
		channelName = obj["mqtt_channel"]
		wifiName = obj["wifi_name"]
		wifiPass = obj["wifi_pass"]
	except:
		showError(ledBlue)
		print("Error loading values from config.json")
		return False

	return True




# Sets up the Wifi etc.
def setup():
	print("Setting Up Tree")

	showError(ledGreen)

	# Connect to wifi
	wifi_client = network.WLAN(network.STA_IF)
	wifi_station = network.WLAN(network.AP_IF)

	wifi_station.active(False)

	wifi_client.disconnect()
	wifi_client.connect(wifiName, wifiPass)

	while(wifi_client.ifconfig()[0] == '0.0.0.0'):
		time.sleep_ms(100)

	clearError(ledGreen)


# Displays an error (flashes the red LED)
def showError(led):
	led.freq(1)
	led.duty(500)

def clearError(led):
	led.freq(1)
	led.duty(0)

# Handles incoming messages from MQTT
def messageReceived(channel, message):
	print("Received MQTT Message")
	try:
		jso = json.loads(message)
		if (jso["status"] == "request"):
			sendStatus()
		elif (jso["status"] == "colour"):
			if(jso["special"] == True):
				setSpecial()
			else:
				setColours(jso["red"], jso["green"], jso["blue"], jso["purple"], jso["white"])
		else:
			print("Message not handled (%s, %s)" % (channel, message))
	except ValueError as err:
		print("ERROR - Decode Error - Could not decode string %s" % message)
	except KeyError as err:
		print("ERROR - %s" % err)
	except Exception as err:
		print("ERROR - Unhandled")
		print(err)
		return

# Sends the current status to the MQTT server
def sendStatus():
	global client
	
	red = 0
	green = 0
	blue = 0
	purple = 0
	white = 0
	if(inSpecial == False):
		red = min(int(ledRed.duty() / 4), 255)
		green = min(int(ledGreen.duty() / 4), 255)
		blue = min(int(ledBlue.duty() / 4), 255)
		purple = min(int(ledPurple.duty() / 4), 255)
		white = min(int(ledWhite.duty() / 4), 255)

	obj = {
		"status" : "colour",
		"red" : red,
		"green" : green,
		"blue" : blue,
		"purple" : purple,
		"white" : white,
		"special" : inSpecial
	}

	print("Sending Current Status (%d, %d, %d, %d, %d, %s)" % (red,green,blue,purple,white,str(inSpecial)))
	client.publish(channelName, json.dumps(obj))


# Sets the colours on the tree (r/g/b/p/w are out of 255)
def setColours(red, green, blue, purple, white):	
	global ledRed, ledGreen, ledBlue, ledPurple, ledWhite, inSpecial
	print("Setting Tree Colours (%d, %d, %d, %d, %d)" % (red,green,blue,purple,white))
	inSpecial = False

	ledRed.freq(1000)
	ledRed.duty(4 * red)

	ledGreen.freq(1000)
	ledGreen.duty(4 * green)

	ledBlue.freq(1000)
	ledBlue.duty(4 * blue)

	ledPurple.freq(1000)
	ledPurple.duty(4 * purple)

	ledWhite.freq(1000)
	ledWhite.duty(4 * white)

# Does some cool special lights
def setSpecial():
	global ledRed, ledGreen, ledBlue, ledPurple, ledWhite, inSpecial
	print("Setting Tree Colours (SPECIAL)")
	inSpecial = True

	ledWhite.freq(1000)
	ledWhite.duty(1000)

	ledRed.freq(1)
	ledRed.duty(250)

	ledGreen.freq(1)
	ledGreen.duty(500)

	ledBlue.freq(1)
	ledBlue.duty(750)

def clearLeds():
	clearError(ledGreen)
	clearError(ledRed)
	clearError(ledBlue)
	clearError(ledPurple)
	clearError(ledWhite)

# /FUNCTIONS ==========================

def main():
	global client

	clearLeds()

	# Get settings from config.json
	while(getSettings() == False):
		time.sleep(10)
	
	# Connects to Wifi
	setup()

	# Open up the connection to MQTT
	print("Setting Up Connection To MQTT server")
	client = MQTTClient(clientName, mqttServerAddress)
	client.set_callback(messageReceived)

	# print("Waiting for Network")
	# conn = network.WLAN(network.STA_IF)
	# while(conn.ifconfig()[0] == '0.0.0.0'):
	# 	time.sleep(100)

	# print("Network Ready")

	# Try to connect to MQTT server
	print("Attempting to connect to MQTT server")
	try:
		client.connect()
	except:
		print("Failed. Network info:")
		print(network.WLAN(network.STA_IF).ifconfig())
	client.subscribe(channelName)
	print("Connected and Subscribed to %s channel" % channelName)


	# Listen to MQTT
	while(True):
		print("")
		print("Listening to channel")
		client.wait_msg();

if __name__ == '__main__':
	main()
