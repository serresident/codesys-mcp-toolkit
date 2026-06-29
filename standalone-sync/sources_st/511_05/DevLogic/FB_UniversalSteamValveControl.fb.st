// @OBJECT_ID: c71aff23-84cd-4c4a-b310-a13f0d6eda39
// @DECLARATION
FUNCTION_BLOCK FB_UniversalSteamValveControl
VAR_INPUT
    xEnable       : BOOL;   // Переключатель контура (ВКЛ/ВЫКЛ) [1]
    rTempActual   : REAL;   // Текущая температура [1]
    rSetpoint     : REAL;   // Уставка температуры [1]
    xReset        : BOOL;   // Сброс ошибки ПИД [1]
    
    // Настройки ПИД (передаются снаружи для универсальности)
    rKp           : REAL;   
    rTn           : REAL;   
    rTv           : REAL;   
    rLimitLow     : REAL;   
    rLimitHigh    : REAL;   
END_VAR

VAR_IN_OUT
    // Переменные IN_OUT изменяют внешнюю переменную по ссылке
    rValveOut     : REAL;   // Управляющее воздействие на клапан (0-100% или иное) [3]
    xAutoModeCmd  : BOOL;   // Команда режима: TRUE = АВТО, FALSE = РУЧНОЙ
END_VAR

VAR_OUTPUT
    xStatusActive : BOOL;   // Статус работы контура [1]
END_VAR

VAR
    fbPID         : oscat_basic.CTRL_PID; // Экземпляр ПИД из библиотеки Oscat [1]
    xOldEnable    : BOOL;   // Для детектора фронта [1]
    rInternalY    : REAL;   // Промежуточная переменная для выхода PID
END_VAR









// @IMPLEMENTATION

// --- ЛОГИКА ---

// 1. Управление режимами (детектирование изменения xEnable)
IF xEnable AND NOT xOldEnable THEN
    // ВКЛЮЧЕНИЕ:
    xStatusActive := TRUE;       // [2]
    xAutoModeCmd  := TRUE;       // Переводим внешний флаг в режим АВТО
    
ELSIF NOT xEnable AND xOldEnable THEN
    // ВЫКЛЮЧЕНИЕ:
    xStatusActive := FALSE;      // [2]
    xAutoModeCmd  := FALSE;      // Снимаем флаг АВТО (переход в ручной)
    rValveOut     := 0.0;        // Обнуляем выход на клапан [2]
END_IF;

xOldEnable := xEnable;

// 2. Вызов ПИД-регулятора
fbPID(
    ACT := rTempActual,          // [2]
    SET := rSetpoint,            // [2]
    MAN := NOT xStatusActive,    // Если не активен, ПИД в ручном режиме (MAN=TRUE) [2]
    RST := xReset,               // [2]
    KP  := rKp,                  // [2]
    TN  := MAX(rTn, 1.0),        // Защита от деления на 0, как в источнике [2]
    TV  := rTv,                  // [3]
    LL  := rLimitLow,            // [3]
    LH  := rLimitHigh            // [3]
);

// 3. Передача значения из ПИД во внешнюю переменную через IN_OUT
// Обновляем выход только если контур активен, чтобы не перебивать ручное управление при выключенном блоке
IF xStatusActive THEN
    rValveOut := fbPID.Y;        // [3]
END_IF;