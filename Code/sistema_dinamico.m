%% Parámetros y constantes
Cr = 0.47;
w = [0 0 0];
A = [0   1   0   0   0   0  ;
     0  -Cr  0 -w(3) 0 w(2) ;
     0   0   0   1   0   0  ;
     0  w(3) 0 -Cr   0 -w(1);
     0   0   0   0   0   1  ;
     0 -w(2) 0  w(1) 0  -Cr];


%% Modelo


