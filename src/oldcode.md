This is the old code which functioned to define the pins and to create the movemotor functions



#include <Arduino.h>

// MAKE SURE TO PUT THE PWM PINS ON THE RIGHT pin attached on the esp
const int pwmpin_left = 25;  // ORANGE IS FOR PWM
const int dirpin_left = 26;  // RED IS FOR DIRECTION CONTROL
const int pwmpin_right = 33;  // orange IS FOR PWM
const int dirpin_right = 32;  // yellow IS FOR DIRECTION CONTROL

int speed = 150;
bool forward = true;

// put function declarations here:

void stopmotor_left();
void runmotor_left(bool direction, int speed);
void stopmotor_right();
void runmotor_right(bool direction, int speed);  




void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.printf("ESP Initialized\n");
  ledcAttach(pwmpin_left, 20000, 8);
  ledcAttach(pwmpin_right, 20000, 8);
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.printf("Running...\n");
  runmotor_left(forward, speed);
  runmotor_right(forward, speed);
  delay(2000);
  stopmotor_left();
  stopmotor_right();
  while(true) {
  }
}



// put function definitions here:
void stopmotor_left()
{
  ledcWrite(pwmpin_left, 0); 
}

void stopmotor_right()
{
  ledcWrite(pwmpin_right, 0); 
}

void runmotor_left(bool direction, int speed)
{
  ledcWrite(pwmpin_left, speed);
  digitalWrite(dirpin_left, direction);
}

void runmotor_right(bool direction, int speed)
{
  ledcWrite(pwmpin_right, speed);
  digitalWrite(dirpin_right, direction);
}