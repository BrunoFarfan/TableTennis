/*
 * -----------------------------
 * IRB2001
 * Modulo: Control de Robots
 * Profesor: David Acuña
 * -----------------------------
 * Programa Base
 * -----------------------------
 */

//-----------------------------------
// Importar librerias
#include "DualVNH5019MotorShield.h"
DualVNH5019MotorShield md;

// Definicion de PINs
#define encoderPinA  18
#define encoderPinB  20
#define enA 9
#define in1 23
#define in2 22

// Variables tiempo
unsigned long time_ant = 0;
const int Period = 10000;   // 10 ms = 100Hz
const float dt = Period *0.000001f;   // Tiempo de muestreo
float voltage_m = 0.0;   // Voltaje que se aplica a motor Pololu

// Variables de los encoders y posicion
volatile long encoderPos = 0;
long newposition;
long oldposition = 0;
long cuentas_actuales = 0;

unsigned long newtime;
float vel;   // Velocidad del motor Pololu en RPM

// Variables de control
const float Kp = 0.5; //0.5;
const float Ki = 0;//2;
const float Kd = 0;//0.7;

long angulo_ref = 0;
long cuentas_ref;

long error_actual = 0;
long error_acumulado = 0;
long error_anterior = 0;

float Voltaje_in = 0;
int pinInput;

// Variables lectura del serial
String message = "";
int valores_iniciales = 10;
int partida = valores_iniciales;
int signo_inicial;

//-----------------------------------
// CONFIGURANDO INTERRUPCIONES
void doEncoderA()
{
  if (digitalRead(encoderPinA) == digitalRead(encoderPinB)) {
    encoderPos = encoderPos + 3;
  } else {
    encoderPos = encoderPos - 2;
  }
}

void doEncoderB()
{
  if (digitalRead(encoderPinA) == digitalRead(encoderPinB)) {
    encoderPos = encoderPos - 2;
  } else {
    encoderPos = encoderPos + 2;
  }
}

//-----------------------------------
// CONFIGURACION
void setup()
{
  // Configuracion de MotorShield
  md.init();

  // Configuracion de encoders
  pinMode(encoderPinA, INPUT);
  digitalWrite(encoderPinA, HIGH);       // Incluir una resistencia de pullup en le entrada
  pinMode(encoderPinB, INPUT);
  digitalWrite(encoderPinB, HIGH);       // Incluir una resistencia de pullup en le entrada

  attachInterrupt(digitalPinToInterrupt(encoderPinA), doEncoderA, CHANGE);  // encoder PIN A
  attachInterrupt(digitalPinToInterrupt(encoderPinB), doEncoderB, CHANGE);  // encoder PIN B

    pinMode(enA, OUTPUT);
    pinMode(in1, OUTPUT);
    pinMode(in2, OUTPUT);
    // Set initial rotation direction
    digitalWrite(in1, LOW); // Dar vuelta el LOW y el HIGH para cambiar la dirección de giro
    digitalWrite(in2, HIGH);

  // Configuracion de Serial Port
  Serial.begin(115200);           // Inicializacion del puerto serial (Monitor Serial)
  Serial.println("start");
}

//-----------------------------------
// LOOP PRINCIPAL
void loop() {
  if ((micros() - time_ant) >= Period)
  {
    newtime = micros();

    //-----------------------------------
    // Ejemplo variable alterando cada 5 segundos
    if ((newtime / 5000000) % 2){
      voltage_m = 12.0;
    }
    else{
      voltage_m = 0.0;
    }

    //-----------------------------------
    // Actualizando informacion de los encoders
    newposition = encoderPos;

    //-----------------------------------
    // Calculando velocidad del motor en unidades de RPM
    float rpm = 31250; // 1920 cuentas por rev. Si encoderPos == 1920, dió una vuelta 
    vel = (float)(newposition - oldposition) * rpm / (newtime - time_ant); //RPM
    oldposition = newposition;

    // Control en base a cuentas:
    
    cuentas_ref = 1920*4*angulo_ref/360; // Vamos a tomar solo un numero entero de cuentas.
                                        // Programar un compensador de error
    cuentas_actuales = encoderPos;                                    
    serialReader(); // Función que majea el serial
    
    Voltaje_in= pid(cuentas_actuales, cuentas_ref, Kp, Ki, Kd, dt);
    if (Voltaje_in >= 0){
      digitalWrite(in1, LOW); // Angulos positivos
      digitalWrite(in2, HIGH);}
    else if (Voltaje_in < 0){
      digitalWrite(in1, HIGH); // Angulos_negativos
      digitalWrite(in2, LOW);
      Voltaje_in = - Voltaje_in;}
    
    pinInput = Voltaje_in/12 * 255; // Ver el tema de los signos
    if (partida > 0){pinInput = 80; partida -=1;}
    analogWrite(enA, pinInput); // Send PWM signal to L298N Enable pin


    //-----------------------------------
    // Voltaje aplicado a motores (modificar aquí para implementar control)
    
    Serial.print("Angulo ref: ") ;Serial.print(angulo_ref); Serial.print(" / "); Serial.print(pinInput);
    Serial.print(" / "); Serial.print(cuentas_ref);Serial.print(" / Cuentas_actuales: "); Serial.print(cuentas_actuales);
    Serial.print(" Kp*Error_act: "); Serial.print(Kp * error_actual);
    Serial.print(" Ki*Error_acum: "); Serial.println(Ki * error_acumulado);

    // Motor Voltage
    
    /* IMPORTANTE: La libreria md (DualVNH5019MotorShield) es para el controlador de Pololu, es un dirver
                   especifico que hay que usar. Es un puente H al final con varias cosas extras. No es 
                   necesario usarlo, podriamos usar un L298N en vez de esta controladora. Si usamos otro
                   puente H, no podríamos usar las funciones de la librería md, aunque no necesitamos
                   muchas. Es por esto, que en el código de los Pololu EN NINGÚN MOMENTO SE DEFINE CUAL 
                   ES EL MOTOR M1 NI M2, porque estas etiquetas corresponden a conexiones físicas en el 
                   controlador de Pololu                   
    */
    
 
    // Reportar datos
    /*
    Serial.print("$,");
    Serial.print(newtime);
    Serial.print(",");
    Serial.print(newposition);
    Serial.print(",");
    Serial.print(vel);
    //Serial.print(",");
    //Serial.print(voltage_m);
    //Serial.print(",");
    Serial.print(", Vueltas: ");
    Serial.print(cuentas_ref);
    Serial.println(",");

    time_ant = newtime; 
    */
  }
}

void serialReader(){
  if (Serial.available()) { // Verifica si hay datos disponibles para leer    
      char receivedData;      
      receivedData = Serial.read(); // Lee un byte de datos      
      
      if (receivedData == '\n') { // Si se recibe un salto de línea, se considera el final del mensaje
        angulo_ref = (String(message)).toInt();
        if (angulo_ref > 50){angulo_ref = 50;}
        if (angulo_ref < -50){angulo_ref = -50;}

        error_acumulado = 0;
        partida = valores_iniciales;
        message = "";}
      else {
        message += receivedData; // Concatena el byte leído al mensaje
            }
      } 
}

double pid(float cuentas_act, float cuentas_ref, float kp, float ki, float kd, float dT) {
  error_actual = (cuentas_ref - cuentas_act); // Agregar - si no funciona bien
  error_acumulado += error_actual * dT;
  float pid_value = kp*error_actual + ki*error_acumulado + kd * (error_actual - error_anterior)/dT;
  error_anterior = error_actual;

  //double PWM_correccion = pid_value;
  
  float Voltaje_correccion= mapfloat(pid_value, -1 * 340, 340, -12, 12);

  if (Voltaje_correccion > 12) {
    Voltaje_correccion= 12;
  }
  
  if (Voltaje_correccion < -12) {
    Voltaje_correccion= -12;
  }
  return Voltaje_correccion;  
}


float mapfloat(long x, long in_min, long in_max, long out_min, long out_max)
{
  return (float)(x - in_min) * (out_max - out_min) / (float)(in_max - in_min) + out_min;
}
