// @OBJECT_ID: 0bcac0e8-eed9-4bae-8693-ddac31a98cce
// @DECLARATION
(*Рабочий алгоритм этого блока будет следующим: по переднему фронту сигнала xStart он включает внутренний пид-регулятор, который открывает клапан и начинает нагрев. Если xKeepTemp = FALSE, то как только текущая температура достигает заданной, мы снимаем сигнал разрешения (xEnable) и внутреннего пид-регулятора (нагрев прекращается). Если xKeepTemp = TRUE, то регулятор продолжает поддерживать температуру, пока активен xStart.
*)
FUNCTION_BLOCK FB_AutoHeater
VAR_INPUT
    xStart        : BOOL;   // Признак запуска нагрева (по переднему фронту)
    xKeepTemp     : BOOL;   // TRUE = поддерживать температуру после достижения, FALSE = отключить после нагрева (разовая операция)
    rTempActual   : REAL;   // Текущая температура в аппарате
    rTargetTemp   : REAL;   // Целевая температура, до которой нужно нагреть (или уставка)
    rTolerance    : REAL := 0.5; // Зона чувствительности (нагрев считается завершенным при Т >= уставка - Tolerance)
    // Параметры пид-регулятора
    rKp           : REAL := 1.0;
    rTn           : REAL := 10.0;
    rTv           : REAL := 0.0;
END_VAR
VAR_IN_OUT
    rValveOut     : REAL;   // Управляющее воздействие на клапан (0..100%)
    xAutoModeCmd  : BOOL;   // Выбор режима (TRUE = авто, FALSE = ручной)
END_VAR
VAR_OUTPUT
    xActive       : BOOL;   // Состояние: нагрев в процессе
    xDone         : BOOL;   // Состояние: нагрев успешно завершен (целевая Т достигнута)
END_VAR
VAR
    fbSteamControl : FB_UniversalSteamValveControl;
    xOldStart      : BOOL;  // Память сигнала запуска
    xEnablePID     : BOOL;  // Внутренний сигнал работы пид-регулятора
END_VAR







// @IMPLEMENTATION
// --- 1. Обработка команд и переходов состояний ---
// Детектор переднего фронта запуска: если пришел сигнал Start
IF xStart AND NOT xOldStart THEN
    xActive    := TRUE;   // Начинаем нагрев
    xDone      := FALSE;  // Сбрасываем флаг готовности
    xEnablePID := TRUE;   // Разрешаем работу внутреннего регулятора
END_IF;

// Условие достижения температуры
IF xActive AND (rTempActual >= (rTargetTemp - rTolerance)) THEN
    xDone := TRUE;   // Сигнализируем успешное достижение уставки
    
    // Если НЕ нужно удерживать температуру, выключаем нагрев
    IF NOT xKeepTemp THEN
        xActive    := FALSE;  // Останавливаем процесс
        xEnablePID := FALSE;  // Отключаем ПИД-регулятор
    END_IF;
END_IF;

// Обработка ручного сброса / выключения
IF NOT xStart THEN
    xDone := FALSE; // Сбрасываем статус при снятии Start
    IF xActive THEN
        xActive    := FALSE;
        xEnablePID := FALSE;
    END_IF;
END_IF;

xOldStart := xStart; // Запоминаем состояние фронта

// --- 2. Вызов регулирующего функционального блока ---
fbSteamControl(
    xEnable       := xEnablePID,
    rTempActual   := rTempActual,
    rSetpoint     := rTargetTemp,
    xReset        := FALSE,
    rKp           := rKp,
    rTn           := rTn,
    rTv           := rTv,
    rLimitLow     := 0.0,
    rLimitHigh    := 100.0,
    rValveOut     := rValveOut,
    xAutoModeCmd  := xAutoModeCmd
);