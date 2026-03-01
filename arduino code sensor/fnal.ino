                              #include "HX711.h"
                              #include <Servo.h>
                              
                              // HX711 setup
                              HX711 scale_e(6, 5);   // DT = Pin 6, SCK = Pin 5
                              HX711 scale_f(12,11); // DT = Pin 11, SCK = Pin 12
                              
                              float calibration_factor_f = -300;
                              //float calibration_factor_e = -326;
                              float units=0, units_e=0, units_f=0;
                              char data = '\0';
                              
                              // Ultrasonic pins
                              const int trigPin = 7;
                              const int echoPin = 8;
                              
                              // Sorting counts
                              int count_A = 0;
                              int count_B = 0;
                              
                              // Servo setup
                              Servo myservo1; // Pusher
                              Servo myservo2; // Sorter
                              
                              bool isSorting = false;
                              unsigned long sortingStartTime = 0;
                              int sortingStep = 0;
                              char sortingType = '\0';
                              
                              // Smooth servo movement
                              void smoothMove(Servo& servo, int startAngle, int endAngle, int stepDelay = 5) {
                                  int step = (startAngle < endAngle) ? 1 : -1;
                                  for (int angle = startAngle; angle != endAngle; angle += step) {
                                      servo.write(angle);
                                      delay(stepDelay);
                                  }
                                  servo.write(endAngle); // final position
                              }
                              
                              // Measure distance function
                              long readUltrasonic(int trigPin, int echoPin) {
                                  digitalWrite(trigPin, LOW);
                                  delayMicroseconds(2);
                                  digitalWrite(trigPin, HIGH);
                                  delayMicroseconds(10);
                                  digitalWrite(trigPin, LOW);
                                  long duration = pulseIn(echoPin, HIGH, 30000); // 30ms timeout
                                  long distance = duration * 0.034 / 2; // distance in cm
                                  return distance;
                              }
                              
                              void setup() {
                                  Serial.begin(115200);
                                  Serial.println("HX711 Weighing System");
                              
                                  //scale_e.set_scale(calibration_factor_e);
                                  scale_f.set_scale(calibration_factor_f);
                                  //scale_e.tare();
                                  scale_f.tare();
                                  Serial.println("Calibration complete.");
                              
                                  myservo1.attach(3);  // Pusher
                                  myservo2.attach(10); // Sorter
                              
                                  myservo1.write(110); // Initial pusher position (retracted)
                                  myservo2.write(99);  // Initial sorter position (center)
                              
                                  pinMode(trigPin, OUTPUT);
                                  pinMode(echoPin, INPUT);
                              }
                              
                              void loop() {
                                  unsigned long currentMillis = millis();
                              
                                    // Read weight
                                  //units_e = scale_e.get_units(10);
                                  units_f = scale_f.get_units(10);
                                  //units = ((units_e + units_f) / 2);
                                  if (units_f < 0 || units_f > 1500) units = 0.00;
                              
                                  // Ultrasonic distance reading
                                  long distance = readUltrasonic(trigPin, echoPin);
                                  bool objectDetected = (distance > 0 && distance < 30); // object detected within 30cm
                              
                                  // Serial input for sorting
                                  if (!isSorting) {
                                      if (Serial.available() > 0) {
                                          data = Serial.read();
                                          // Sorting logic for 'A' and 'B'
                                          //if(units > 400 && units < 800)
                                          //{
                                            if (data == 'A') 
                                            {
                                                sortingType = 'A';
                                                isSorting = true;
                                                sortingStep = 1;
                                                sortingStartTime = currentMillis;
                                                while (Serial.available()) Serial.read(); // Clear serial buffer
                                            }
                                          //}
                                          
                                          //else if(units < 400)
                                          //{
                                            else if (data == 'B' ) 
                                            {     
                                                sortingType = 'B';
                                                isSorting = true;
                                                sortingStep = 1;
                                                sortingStartTime = currentMillis;
                                                while (Serial.available()) Serial.read(); // Clear serial buffer
                                            }
                                          //}
                                
                                      }
                                  } else {
                                      // If sorting is in progress, ignore any incoming data
                                      while (Serial.available()) Serial.read(); // Always clear garbage data
                                  }
                              
                                  // Sorting process
                                  if (isSorting) {
                                      switch (sortingStep) {
                                          case 1:  // Push banana slowly
                                              smoothMove(myservo1, 110, 5, 15); // push
                                              sortingStep = 2;
                                              sortingStartTime = currentMillis;
                                              break;
                              
                                          case 2:  // Check if object is detected
                                              if (objectDetected) {
                                                  if (sortingType == 'A') {
                                                      count_A += 1;
                                                      smoothMove(myservo2, 99, 99, 15); // center
                                                  } else if (sortingType == 'B') {
                                                      count_B += 1;
                                                      smoothMove(myservo2, 99, 20, 5); // move to B
                                                  }
                                              }
                                              sortingStep = 3;
                                              sortingStartTime = currentMillis;
                                              break;
                              
                                          case 3:  // Retract pusher slowly
                                              if (currentMillis - sortingStartTime >= 100) {
                                                  smoothMove(myservo1, 5, 110, 15); // retract
                                                  sortingStep = 4;
                                                  sortingStartTime = currentMillis;
                                              }
                                              break;
                              
                                          case 4:  // Reset sorter position
                                              if (currentMillis - sortingStartTime >= 4000) {
                                                  smoothMove(myservo2, myservo2.read(), 99, 15); // reset to center
                                                  isSorting = false;
                                              }
                                              break;
                                      }
                                  }
                                
                              
                                  // Print weight and ultrasonic status
                                  Serial.print("Weight: ");
                                  Serial.print(units_f, 2);
                                  Serial.print(",");
                                  Serial.print("A: ");
                                  Serial.print(count_A);
                                  Serial.print(",");
                                  Serial.print("B: ");
                                  Serial.print(count_B);
                                  Serial.print(",");
                                  Serial.print("Distance: ");
                                  Serial.print(distance);
                                  Serial.print("cm");
                                  Serial.print(",");
                                  Serial.print("UI ");
                                  Serial.print(data);
                                  Serial.print(" w_F: ");
                                  Serial.print(units_f);
                                 
                                  Serial.print(" C_F: ");
                                  Serial.println(calibration_factor_f);

                                    if(Serial.available())
                                          {
                                            char temp = Serial.read();
                                          
                                              
                                              if(temp == 'a')
                                              calibration_factor_f += 1;
                                            else if(temp == 'z')
                                              calibration_factor_f -= 1;
                                          }
        
                                  
                              }
