// @OBJECT_ID: 58eab0a1-f642-4bbd-ba35-3845d9d3886b
// @DECLARATION
FUNCTION FC_Write_AO : BOOL
VAR_INPUT
    VAL_IN  : REAL;    // Входное значение (например, от ПИД 0..1000)

    pOutput : POINTER TO ARRAY[0..1] OF WORD; // Адрес физических регистров модуля
END_VAR
VAR
    TMP     : REAL;
    dwValue : DWORD;
	    X1      : REAL:=0;    // Мин. вход (например, 0)
    X2      : REAL:=100;    // Макс. вход (например, 1000)
    Y1      : REAL:=4;    // Мин. ток (например, 4.0)
    Y2      : REAL:=20;    // Макс. ток (например, 20.0)
END_VAR









// @IMPLEMENTATION

// 1. Проверка на нулевой указатель и деление на ноль
IF pOutput = 0 OR (X2 = X1) THEN
    FC_Write_AO := FALSE;
    RETURN;
END_IF;

// 2. Линейное масштабирование (из входного диапазона в 4..20мА)
TMP := (Y2 - Y1) / (X2 - X1) * (VAL_IN - X1) + Y1;

// 3. Преобразование REAL во внутреннее битовое представление DWORD
dwValue := OSCAT_BASIC.REAL_TO_DW(TMP);

// 4. Запись напрямую в память по указателю (разбивка на 2 WORD)
// В ПЛК Абак обычно старшее слово идет первым (зависит от настроек модуля)
pOutput^[0] := OSCAT_BASIC.WORD_OF_DWORD(dwValue, 1); // High Word
pOutput^[1] := OSCAT_BASIC.WORD_OF_DWORD(dwValue, 0); // Low Word

FC_Write_AO := TRUE;