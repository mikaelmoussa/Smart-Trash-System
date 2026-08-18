#include <Servo.h>

Servo servoTop;
Servo servoLeft;
Servo servoRight;

const int trigMetal   = 2,  echoMetal   = 3;
const int trigPlastic = 4,  echoPlastic = 5;
const int trigGlass   = 6,  echoGlass   = 7;
const int trigPaper   = A0, echoPaper   = A1;

const int PIN_SERVO_TOP   = 9;
const int PIN_SERVO_LEFT  = 10;
const int PIN_SERVO_RIGHT = 11;

const int CENTER = 90;
const int LEFT   = 10;
const int RIGHT  = 170;
const int SERVO_SPEED = 20;
const int BIN_FULL_CM = 3;

// ── Sensor filter settings ───────────────────────────────
const int   SAMPLES        = 5;     // readings per measurement
const float MIN_DIST_CM    = 2.0;   // HC-SR04 blind zone
const float MAX_DIST_CM    = 400.0; // beyond this = garbage
// ────────────────────────────────────────────────────────

int posTop   = CENTER;
int posLeft  = CENTER;
int posRight = CENTER;

// ── Function declarations ────────────────────────────────
void  moveServo(Servo &servo, int &currentPos, int targetPos);
float singlePing(int trig, int echo);
float getDistance(int trig, int echo);          // ← now uses median
void  reportBin(const char* name, int trig, int echo);
void  checkAllBins();
// ────────────────────────────────────────────────────────

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);

  servoTop.attach(PIN_SERVO_TOP);
  servoLeft.attach(PIN_SERVO_LEFT);
  servoRight.attach(PIN_SERVO_RIGHT);

  pinMode(trigMetal,   OUTPUT); pinMode(echoMetal,   INPUT);
  pinMode(trigPlastic, OUTPUT); pinMode(echoPlastic, INPUT);
  pinMode(trigGlass,   OUTPUT); pinMode(echoGlass,   INPUT);
  pinMode(trigPaper,   OUTPUT); pinMode(echoPaper,   INPUT);

  servoTop.write(CENTER);
  servoLeft.write(CENTER);
  servoRight.write(CENTER);

  Serial.println("READY");
}

// ── One raw ping (returns -1 on timeout) ─────────────────
float singlePing(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH, 30000); // 30ms timeout ≈ 510cm
  if (duration == 0) return -1;

  float dist = duration * 0.034 / 2.0;

  // Reject outside the sensor's valid range
  if (dist < MIN_DIST_CM || dist > MAX_DIST_CM) return -1;

  return dist;
}

// ── Median of SAMPLES valid pings ────────────────────────
float getDistance(int trig, int echo) {
  float readings[SAMPLES];
  int   validCount = 0;

  for (int i = 0; i < SAMPLES; i++) {
    float d = singlePing(trig, echo);
    if (d > 0) readings[validCount++] = d;
    delay(10); // short gap between pings prevents echo overlap
  }

  if (validCount == 0) return -1; // all pings failed → sensor error

  // Bubble-sort valid readings
  for (int i = 0; i < validCount - 1; i++) {
    for (int j = i + 1; j < validCount; j++) {
      if (readings[j] < readings[i]) {
        float tmp = readings[i];
        readings[i] = readings[j];
        readings[j] = tmp;
      }
    }
  }

  // Return median
  return readings[validCount / 2];
}

// ── Servo smooth move ─────────────────────────────────────
void moveServo(Servo &servo, int &currentPos, int targetPos) {
  if (currentPos < targetPos) {
    for (int pos = currentPos; pos <= targetPos; pos++) {
      servo.write(pos); delay(SERVO_SPEED);
    }
  } else {
    for (int pos = currentPos; pos >= targetPos; pos--) {
      servo.write(pos); delay(SERVO_SPEED);
    }
  }
  currentPos = targetPos;
}

// ── Bin report ────────────────────────────────────────────
void reportBin(const char* name, int trig, int echo) {
  float dist = getDistance(trig, echo);
  Serial.print(name);
  Serial.print(":");
  if (dist < 0) {
    Serial.print("ERROR");
  } else if (dist <= BIN_FULL_CM) {
    Serial.print("FULL(");
    Serial.print(dist);
    Serial.print("cm)");
  } else {
    Serial.print("OK(");
    Serial.print(dist);
    Serial.print("cm)");
  }
  Serial.print(" ");
}

void checkAllBins() {
  reportBin("METAL",   trigMetal,   echoMetal);
  reportBin("PLASTIC", trigPlastic, echoPlastic);
  reportBin("GLASS",   trigGlass,   echoGlass);
  reportBin("PAPER",   trigPaper,   echoPaper);
  Serial.println();
}

// ── Main loop ─────────────────────────────────────────────
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    cmd.toUpperCase();

    if (cmd == "ITEM:METAL") {
      if (getDistance(trigMetal, echoMetal) <= BIN_FULL_CM) {
        Serial.println("REJECTED:METAL bin is full!");
      } else {
        moveServo(servoTop,  posTop,  LEFT);   delay(800);
        moveServo(servoLeft, posLeft, LEFT);   delay(800);
        moveServo(servoLeft, posLeft, CENTER); delay(500);
        moveServo(servoTop,  posTop,  CENTER);
        Serial.println("DONE:METAL");
        checkAllBins();
      }
    }

    else if (cmd == "ITEM:PLASTIC") {
      if (getDistance(trigPlastic, echoPlastic) <= BIN_FULL_CM) {
        Serial.println("REJECTED:PLASTIC bin is full!");
      } else {
        moveServo(servoTop,  posTop,  LEFT);    delay(800);
        moveServo(servoLeft, posLeft, RIGHT);   delay(800);
        moveServo(servoLeft, posLeft, CENTER);  delay(500);
        moveServo(servoTop,  posTop,  CENTER);
        Serial.println("DONE:PLASTIC");
        checkAllBins();
      }
    }

    else if (cmd == "ITEM:GLASS") {
      if (getDistance(trigGlass, echoGlass) <= BIN_FULL_CM) {
        Serial.println("REJECTED:GLASS bin is full!");
      } else {
        moveServo(servoTop,   posTop,   RIGHT);  delay(800);
        moveServo(servoRight, posRight, LEFT);   delay(800);
        moveServo(servoRight, posRight, CENTER); delay(500);
        moveServo(servoTop,   posTop,   CENTER);
        Serial.println("DONE:GLASS");
        checkAllBins();
      }
    }

    else if (cmd == "ITEM:PAPER") {
      if (getDistance(trigPaper, echoPaper) <= BIN_FULL_CM) {
        Serial.println("REJECTED:PAPER bin is full!");
      } else {
        moveServo(servoTop,   posTop,   RIGHT);  delay(800);
        moveServo(servoRight, posRight, RIGHT);  delay(800);
        moveServo(servoRight, posRight, CENTER); delay(500);
        moveServo(servoTop,   posTop,   CENTER);
        Serial.println("DONE:PAPER");
        checkAllBins();
      }
    }

    else if (cmd == "CHECKBINS" || cmd == "STATUS") { checkAllBins(); }

    else if (cmd == "T1") {
      Serial.println("SERVO1: LEFT");   moveServo(servoTop, posTop, LEFT);    delay(500);
      Serial.println("SERVO1: RIGHT");  moveServo(servoTop, posTop, RIGHT);   delay(500);
      Serial.println("SERVO1: CENTER"); moveServo(servoTop, posTop, CENTER);
    }
    else if (cmd == "T2") {
      Serial.println("SERVO2: LEFT");   moveServo(servoLeft, posLeft, LEFT);    delay(500);
      Serial.println("SERVO2: RIGHT");  moveServo(servoLeft, posLeft, RIGHT);   delay(500);
      Serial.println("SERVO2: CENTER"); moveServo(servoLeft, posLeft, CENTER);
    }
    else if (cmd == "T3") {
      Serial.println("SERVO3: LEFT");   moveServo(servoRight, posRight, LEFT);    delay(500);
      Serial.println("SERVO3: RIGHT");  moveServo(servoRight, posRight, RIGHT);   delay(500);
      Serial.println("SERVO3: CENTER"); moveServo(servoRight, posRight, CENTER);
    }

    else {
      Serial.print("UNKNOWN CMD: "); Serial.println(cmd);
    }
  }
}