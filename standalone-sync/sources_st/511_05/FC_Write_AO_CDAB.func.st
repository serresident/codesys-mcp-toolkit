// @OBJECT_ID: c5f4f6d9-aef8-4f24-80c9-f3d975bafcdd
// @DECLARATION
FUNCTION FC_Write_AO_CDAB : BOOL
VAR_INPUT
    rValIn   : REAL;    // Входная уставка (0..100)
    pOutput  : POINTER TO ARRAY[0..1] OF WORD; 
    rInMin   : REAL;    
    rInMax   : REAL;    
    rOutMin  : REAL;    
    rOutMax  : REAL;    
END_VAR
VAR
    rScaled  : REAL;
    dwRaw    : DWORD;
	dwCDAB: DWORD;
    pReal    : POINTER TO DWORD;
END_VAR







// @IMPLEMENTATION
// 1. Линейное масштабирование (Scale)
// Формула: Out = ((In - InMin) * (OutMax - OutMin) / (InMax - InMin)) + OutMin
IF (rInMax <> rInMin) THEN
    rScaled := ((rValIn - rInMin) * (rOutMax - rOutMin) / (rInMax - rInMin)) + rOutMin;
ELSE
    rScaled := rOutMin;
END_IF

// 2. Получаем битовое представление REAL как DWORD
pReal := ADR(rScaled);
dwRaw := pReal^;

// 3. Перепаковка в формат CDAB
// Исходный (ABCD): [Byte3][Byte2][Byte1][Byte0]
// Формат CDAB:     [Byte1][Byte0][Byte3][Byte2]
// То есть меняем местами слова (WORD)

dwCDAB := ROL(dwRaw, 16); // Простейший способ поменять слова местами

// 4. Запись результата по указателю
IF pOutput <> 0 THEN
    pOutput^[1] := DWORD_TO_WORD(dwCDAB AND 16#FFFF);        // Младшее слово CDAB (бывшее старшее AB)
    pOutput^[0] := DWORD_TO_WORD(SHR(dwCDAB, 16));           // Старшее слово CDAB (бывшее младшее CD)
    FC_Write_AO_CDAB := TRUE;
ELSE
    FC_Write_AO_CDAB := FALSE;
END_IF