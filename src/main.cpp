#include <Arduino.h>

// variable declaration
const int pwmpin_left = 25;  
const int dirpin_left = 26;  
const int pwmpin_right = 33;  
const int dirpin_right = 32;  
int speed = 100;
bool forward = false;
char receivedchar;
bool backward = true;

// put function declarations here:
boolean newData = false;
void shownewdata();
void recvonechar();
void stopmotor_left();
void runmotor_left(bool direction, int speed);
void stopmotor_right();
void runmotor_right(bool direction, int speed);  


void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  ledcAttach(pwmpin_left, 20000, 8);
  ledcAttach(pwmpin_right, 20000, 8);
  pinMode(dirpin_left, OUTPUT);
  pinMode(dirpin_right, OUTPUT);
  Serial.printf("ESP Initialized\n");
}

void loop() {
  // put your main code here, to run repeatedly:
  recvonechar();
  shownewdata();
  if (receivedchar == 'w') {
    runmotor_left(forward, speed);
    runmotor_right(forward, speed);
  }
  else if (receivedchar == 's') {
    runmotor_left(backward, speed);
    runmotor_right(backward, speed);
  }
  else if (receivedchar == 'a') {
    runmotor_left(backward, speed);
    runmotor_right(forward, speed);
  }
  else if (receivedchar == 'd') {
    runmotor_left(forward, speed);
    runmotor_right(backward, speed);
  }
  else if (receivedchar == 'x') {
    stopmotor_left();
    stopmotor_right();
  }
}



// put function definitions here:
void recvonechar()
{
  if (Serial.available() > 0) {
    receivedchar = Serial.read();
    newData = true;

  }
}

void shownewdata()
{
  if (newData == true) {
    Serial.println(receivedchar);
    newData = false;
  }
}

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