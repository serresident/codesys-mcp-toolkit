// @OBJECT_ID: 8d81ca1b-e4d0-4e94-b201-9038cef709f6
// @DECLARATION
FUNCTION_BLOCK FB_ModbusToFloatArray
VAR_INPUT
    aDataIn : ARRAY [0..219] OF WORD; // Входной массив (до 120 регистров)
    iQty    : INT := 1;               // Количество FLOAT переменных для обработки (макс 60)
    iMode   : INT := 1;               // Режим: 0=1234, 1=3412 (частый), 2=2143, 3=4321
END_VAR
VAR_OUTPUT
    aDataOut : ARRAY [0..119] OF REAL; // Выходной массив
    xError   : BOOL;                  // Флаг ошибки (если iQty > 60)
END_VAR
VAR
    i : INT;
    uConverter : U_WordToReal;
    wLow : WORD;
    wHigh : WORD;
    wTemp1 : WORD;
    wTemp2 : WORD;
END_VAR









// @IMPLEMENTATION

// Сброс ошибки
xError := FALSE;

// Защита от выхода за пределы массива
IF iQty < 1 OR iQty > 120 THEN
    xError := TRUE;
    RETURN;
END_IF

// Основной цикл
FOR i := 0 TO (iQty - 1) DO
    
    // Получаем пару регистров из массива
    // i*2 - это начало пары (0, 2, 4...)
    wTemp1 := aDataIn[i * 2];     // Первый регистр пары
    wTemp2 := aDataIn[(i * 2) + 1]; // Второй регистр пары

    CASE iMode OF
        // ---------------------------------------------------------
        // Mode 0: 1234 (Big Endian) 
        // Порядок: [HighWord] [LowWord]
        // ---------------------------------------------------------
        0: 
            wHigh := wTemp1;
            wLow  := wTemp2;
            
        // ---------------------------------------------------------
        // Mode 1: 3412 (Middle Little / Word Swap) -> САМЫЙ ЧАСТЫЙ для Modbus
        // Порядок: [LowWord] [HighWord]
        // Регистры меняются местами, байты внутри - нет.
        // ---------------------------------------------------------
        1: 
            wHigh := wTemp2;
            wLow  := wTemp1;

        // ---------------------------------------------------------
        // Mode 2: 2143 (Middle Big / Byte Swap)
        // Порядок: [HighWord swapped] [LowWord swapped]
        // Байты меняются местами внутри каждого слова.
        // ---------------------------------------------------------
        2:
            wHigh := ROL(wTemp1, 8); // Меняем байты местами
            wLow  := ROL(wTemp2, 8);
            
        // ---------------------------------------------------------
        // Mode 3: 4321 (Little Endian)
        // Порядок: [LowWord swapped] [HighWord swapped]
        // Полный разворот: меняются и слова, и байты.
        // ---------------------------------------------------------
        3:
            wHigh := ROL(wTemp2, 8);
            wLow  := ROL(wTemp1, 8);
            
        ELSE
            // По умолчанию используем 3412 (как самый популярный)
            wHigh := wTemp2;
            wLow  := wTemp1;
    END_CASE

    // Сборка DWORD из двух слов
    // Сдвигаем старшее слово на 16 бит влево и добавляем младшее
    uConverter.dwValue := SHL(WORD_TO_DWORD(wHigh), 16) OR WORD_TO_DWORD(wLow);
    
    // Запись результата в выходной массив
    aDataOut[i] := uConverter.rValue;
    
END_FOR