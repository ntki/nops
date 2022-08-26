#define BAUD 921600
#define LOOP_TIME_US 15

#define SET 0x00
#define RESET 0x20
#define WAIT_US 0x40
#define READ 0x60
#define SET_AS_OUTPUT 0x80
#define SET_AS_INPUT 0xa0

#define PROGRESS_CHUNKSIZE 32
#define PROGRESS_MARK 0x11


unsigned long waitUntil;
int opCounter;

void setup() {
  pinMode(D0, INPUT);
  pinMode(D1, INPUT);
  pinMode(D2, INPUT);
  pinMode(D3, INPUT);
  pinMode(D5, INPUT);
  pinMode(D6, INPUT);
  pinMode(D7, INPUT);
  pinMode(D8, INPUT);
  waitUntil = 0;
  opCounter = 0;
  Serial.begin(BAUD);
  while (!Serial);
}

void loop() {
  unsigned long now = micros();
  if (waitUntil > now) {
    return;
  }
  waitUntil = 0;

  int op = Serial.read();
  if (op == -1)
    return;

  int arg = op & 0x1f;
  switch (op & 0xe0) {
    case SET:
      digitalWrite(arg, HIGH);
      break;
    case RESET:
      digitalWrite(arg, LOW);
      break;
    case WAIT_US:
      waitUntil = now + arg + LOOP_TIME_US;
      break;
    case READ:
      Serial.write(digitalRead(arg));
      break;
    case SET_AS_OUTPUT:
      pinMode(arg, OUTPUT);
      break;
    case SET_AS_INPUT:
      pinMode(arg, INPUT);
      break;
  }

  opCounter++;
  if (opCounter == PROGRESS_CHUNKSIZE) {
    opCounter = 0;
    Serial.write(PROGRESS_MARK);
  }
}
