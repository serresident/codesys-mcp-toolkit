// @OBJECT_ID: 3d2ce4b8-1645-47ac-8a08-67d49366f794
// @DECLARATION
TYPE U_WordToReal :
UNION
    dwValue : DWORD; // Используется для битовых операций
    rValue  : REAL;  // Используется для получения результата
END_UNION
END_TYPE