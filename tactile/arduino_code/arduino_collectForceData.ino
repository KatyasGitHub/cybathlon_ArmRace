const int forcePin1 = A0; // Connect the force sensor to analog pin A0
const int forcePin2 = A3;

void setup() {
    Serial.begin(9600); // Start serial communication
}

void loop() {
    int forceValue1 = analogRead(forcePin1); // Read the analog force sensor value
    Serial.print(forceValue1); // Print the value to the Serial Monitor
    Serial.print(",");
    int forceValue2 = analogRead(forcePin2); // Read the analog force sensor value
    Serial.println(forceValue2); // Print the value to the Serial Monitor
    delay(100); 
}

