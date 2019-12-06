#!/usr/bin/env python3
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

# For certificate based connection
myMQTTClient = AWSIoTMQTTClient("basicPubSub")
# For Websocket connection
# myMQTTClient = AWSIoTMQTTClient("myClientID", useWebsocket=True)
# Configurations
# For TLS mutual authentication
myMQTTClient.configureEndpoint("a13316mvpq9d7l-ats.iot.us-west-1.amazonaws.com", 8883)
# For Websocket
# myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
# For TLS mutual authentication with TLS ALPN extension
# myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
root = "aws_iot/root-CA.crt"
private_key = "aws_iot/WaterThing.private.key"
cert = "aws_iot/WaterThing.cert.pem"
myMQTTClient.configureCredentials(root, private_key, cert)

myMQTTClient.connect()
myMQTTClient.publish("topic_1", "hello world", 0)
#myMQTTClient.subscribe("myTopic", 1, customCallback)
#myMQTTClient.unsubscribe("myTopic")
myMQTTClient.disconnect()
