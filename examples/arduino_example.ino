/*
 * Example Arduino firmware for OpenTrons Custom Serial Module
 * 
 * This firmware demonstrates the JSON command protocol expected by the
 * OpenTrons custom serial module. It handles basic commands and responds
 * with JSON formatted messages.
 * 
 * Hardware: Arduino Uno, Nano, or compatible
 * Communication: 115200 baud, JSON over serial
 */

#include <ArduinoJson.h>

// Device information
const String DEVICE_NAME = "Arduino Custom Module";
const String FIRMWARE_VERSION = "1.0.0";
const String API_VERSION = "1.0";

// Status variables
bool isConnected = false;
unsigned long startTime;
float temperature = 25.0;
float humidity = 50.0;

// JSON document for parsing commands and building responses
StaticJsonDocument<200> commandDoc;
StaticJsonDocument<300> responseDoc;

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  
  startTime = millis();
  
  // Initialize any sensors or hardware here
  // pinMode(LED_BUILTIN, OUTPUT);
  
  Serial.println("{\"status\":\"ready\",\"message\":\"Arduino Custom Module initialized\"}");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.length() > 0) {
      handleCommand(command);
    }
  }
  
  // Update sensor readings or other periodic tasks
  updateSensorReadings();
  
  delay(100);
}

void handleCommand(String commandString) {
  // Clear previous data
  commandDoc.clear();
  responseDoc.clear();
  
  // Parse JSON command
  DeserializationError error = deserializeJson(commandDoc, commandString);
  
  if (error) {
    sendErrorResponse("Invalid JSON format");
    return;
  }
  
  String command = commandDoc["command"];
  command.toUpperCase();
  
  if (command == "CONNECT") {
    handleConnect();
  } else if (command == "DISCONNECT") {
    handleDisconnect();
  } else if (command == "STATUS") {
    handleStatus();
  } else if (command == "RESET") {
    handleReset();
  } else if (command == "GET_VERSION") {
    handleGetVersion();
  } else if (command == "SET_PARAMETER") {
    handleSetParameter();
  } else if (command == "GET_PARAMETER") {
    handleGetParameter();
  } else if (command == "CUSTOM_MEASUREMENT") {
    handleCustomMeasurement();
  } else if (command == "START_MEASUREMENT") {
    handleStartMeasurement();
  } else if (command == "GET_RESULTS") {
    handleGetResults();
  } else {
    sendErrorResponse("Unknown command: " + command);
  }
}

void handleConnect() {
  isConnected = true;
  responseDoc["status"] = "success";
  responseDoc["message"] = "Connected to " + DEVICE_NAME;
  responseDoc["data"]["device_name"] = DEVICE_NAME;
  responseDoc["data"]["firmware_version"] = FIRMWARE_VERSION;
  sendResponse();
}

void handleDisconnect() {
  isConnected = false;
  responseDoc["status"] = "success";
  responseDoc["message"] = "Disconnected from " + DEVICE_NAME;
  sendResponse();
}

void handleStatus() {
  responseDoc["status"] = "success";
  responseDoc["message"] = "Device status retrieved";
  responseDoc["data"]["connected"] = isConnected;
  responseDoc["data"]["temperature"] = temperature;
  responseDoc["data"]["humidity"] = humidity;
  responseDoc["data"]["uptime"] = (millis() - startTime) / 1000;
  sendResponse();
}

void handleReset() {
  // Reset any parameters or state
  startTime = millis();
  temperature = 25.0;
  humidity = 50.0;
  
  responseDoc["status"] = "success";
  responseDoc["message"] = DEVICE_NAME + " reset successfully";
  sendResponse();
}

void handleGetVersion() {
  responseDoc["status"] = "success";
  responseDoc["message"] = "Version information retrieved";
  responseDoc["data"]["device_name"] = DEVICE_NAME;
  responseDoc["data"]["firmware_version"] = FIRMWARE_VERSION;
  responseDoc["data"]["api_version"] = API_VERSION;
  responseDoc["data"]["build_date"] = __DATE__;
  sendResponse();
}

void handleSetParameter() {
  String paramName = commandDoc["parameter"];
  String paramValue = commandDoc["value"];
  
  if (paramName.length() == 0) {
    sendErrorResponse("Parameter name is required");
    return;
  }
  
  // Handle specific parameters
  if (paramName == "led_state") {
    bool ledState = paramValue == "true" || paramValue == "1";
    digitalWrite(LED_BUILTIN, ledState ? HIGH : LOW);
  }
  
  responseDoc["status"] = "success";
  responseDoc["message"] = "Parameter '" + paramName + "' set to '" + paramValue + "'";
  responseDoc["data"]["parameter"] = paramName;
  responseDoc["data"]["value"] = paramValue;
  sendResponse();
}

void handleGetParameter() {
  String paramName = commandDoc["parameter"];
  
  if (paramName.length() == 0) {
    sendErrorResponse("Parameter name is required");
    return;
  }
  
  // Handle specific parameters
  String paramValue = "unknown";
  if (paramName == "led_state") {
    paramValue = digitalRead(LED_BUILTIN) ? "true" : "false";
  }
  
  responseDoc["status"] = "success";
  responseDoc["message"] = "Parameter '" + paramName + "' retrieved";
  responseDoc["data"]["parameter"] = paramName;
  responseDoc["data"]["value"] = paramValue;
  sendResponse();
}

void handleCustomMeasurement() {
  // Example custom command handling
  int param1 = commandDoc["parameter1"];
  String param2 = commandDoc["parameter2"];
  
  // Simulate some measurement
  float measurement = analogRead(A0) * 5.0 / 1023.0;
  
  responseDoc["status"] = "success";
  responseDoc["message"] = "Custom measurement completed";
  responseDoc["data"]["measurement"] = measurement;
  responseDoc["data"]["parameter1"] = param1;
  responseDoc["data"]["parameter2"] = param2;
  sendResponse();
}

void handleStartMeasurement() {
  int duration = commandDoc["duration"];
  
  // Start measurement process
  // In a real implementation, this might start a timer or begin sampling
  
  responseDoc["status"] = "success";
  responseDoc["message"] = "Measurement started";
  responseDoc["data"]["duration"] = duration;
  sendResponse();
}

void handleGetResults() {
  // Return measurement results
  responseDoc["status"] = "success";
  responseDoc["message"] = "Measurement results retrieved";
  responseDoc["data"]["temperature"] = temperature;
  responseDoc["data"]["humidity"] = humidity;
  responseDoc["data"]["voltage"] = analogRead(A0) * 5.0 / 1023.0;
  sendResponse();
}

void updateSensorReadings() {
  // Simulate changing sensor values
  static unsigned long lastUpdate = 0;
  unsigned long now = millis();
  
  if (now - lastUpdate > 1000) {  // Update every second
    temperature = 25.0 + sin(now / 10000.0) * 5.0;  // ±5°C variation
    humidity = 50.0 + cos(now / 8000.0) * 20.0;     // ±20% variation
    lastUpdate = now;
  }
}

void sendResponse() {
  String responseString;
  serializeJson(responseDoc, responseString);
  Serial.println(responseString);
}

void sendErrorResponse(String message) {
  responseDoc.clear();
  responseDoc["status"] = "error";
  responseDoc["message"] = message;
  sendResponse();
}