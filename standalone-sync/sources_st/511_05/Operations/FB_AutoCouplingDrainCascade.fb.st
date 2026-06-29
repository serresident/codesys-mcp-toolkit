// @OBJECT_ID: 2cd08e36-15c9-47b1-a80c-451eef93a439
// @DECLARATION
FUNCTION_BLOCK FB_AutoCouplingDrainCascade
VAR_INPUT
    xStart             : BOOL;   // Триггер запуска стадии
    
    // --- Параметры Диазосоединения ---
    rFlowDiazoActual   : REAL;   // Текущий мгновенный расход диазо (м3/ч)
    rFlowDiazoSetpoint : REAL;   // Заданный мгновенный расход диазо
    
    // --- Параметры pH ---
    rPhActual          : REAL;   // Текущий pH (9.5..12 ед.)
    rPhSetpoint        : REAL;   // Уставка поддерживаемого pH
    
    // --- Условия завершения (Опустошение) ---
    rZeroFlowThreshold : REAL := 0.2;   // Порог "отсутствия расхода" (< 0.2 м3/ч)
    tEmptyDelay        : TIME := T#20S; // Время подтверждения отсутствия расхода
    
    // --- Настройки ПИД ---
    rKp_Diazo          : REAL := 1.0;
    rTn_Diazo          : REAL := 5.0;
    rTv_Diazo          : REAL := 0.0;
    rKp_pH             : REAL := 2.0;
    rTn_pH             : REAL := 10.0;
    rTv_pH             : REAL := 0.0;
END_VAR

VAR_IN_OUT
    rValveOutDiazo     : REAL;   // Задание на клапан диазо (0..100%)
    xAutoModeCmdDiazo  : BOOL;   // Режим АВТО для диазо
    rValveOutSoda      : REAL;   // Задание на клапан соды (0..100%)
    xAutoModeCmdSoda   : BOOL;   // Режим АВТО для соды
END_VAR

VAR_OUTPUT
    xActive            : BOOL;   // Стадия идет
    xDone              : BOOL;   // Стадия успешно завершена
    
    // --- Переменные для HMI ---
    rTimeLeft          : REAL;   // Оставшееся время до завершения (сек)
    rStateCode         : REAL;   // Код текущего состояния (0.0 .. 4.0)
    sStateStr          : STRING; // Текстовая расшифровка состояния
END_VAR

VAR
    fbPidFlowDiazo     : oscat_basic.CTRL_PID;
    fbPidPh            : oscat_basic.CTRL_PID;
    tonEmptyTimer      : TON;
    
    iState             : INT := 0; // Внутренний регистр шага State Machine
    xOldStart          : BOOL;
    xNeedStop          : BOOL;   // Флаг однократного останова оборудования
END_VAR








// @IMPLEMENTATION

// --- ЛОГИКА БЛОКА ---

// 1. Детектор старта (Исправление №1: Явный сброс выходов при старте)
IF xStart AND NOT xOldStart THEN
    iState     := 1;    // Переход в RUNNING
    xActive    := TRUE; // Явное включение
    xDone      := FALSE;// Явный сброс готовности
    xNeedStop  := FALSE;// Явный сброс команды останова
    
    xAutoModeCmdDiazo := TRUE;
    xAutoModeCmdSoda  := TRUE;
END_IF;

// 2. Детектор прерывания оператором
IF NOT xStart AND xOldStart AND (iState = 1 OR iState = 2) THEN
    iState := 4; // Переход в ABORTED
    xNeedStop := TRUE;
END_IF;

// 3. Вызов таймера опустошения
// Таймер работает ТОЛЬКО когда мы находимся на шаге 2 (EMPTYING)
tonEmptyTimer(
    IN := (iState = 2), 
    PT := tEmptyDelay
);

// 4. КОНЕЧНЫЙ АВТОМАТ (STATE MACHINE)
CASE iState OF
    0: // --- IDLE (Ожидание) ---
        sStateStr  := 'ОЖИДАНИЕ: Аппарат готов к запуску';
        rStateCode := 0.0;
        xActive    := FALSE;
        xDone      := FALSE;
        rTimeLeft  := TIME_TO_REAL(tEmptyDelay) / 1000.0; 

    1: // --- RUNNING (Нормальное регулирование) ---
        sStateStr  := 'РАБОТА: Поддержание расхода и pH';
        rStateCode := 1.0;
        xActive    := TRUE;
        xDone      := FALSE;
        rTimeLeft  := TIME_TO_REAL(tEmptyDelay) / 1000.0;
        
        // Условие перехода: расход упал ниже порога
        IF rFlowDiazoActual <= rZeroFlowThreshold THEN
            iState := 2; 
        END_IF;

    2: // --- EMPTYING (Фиксация отсутствия расхода) ---
        sStateStr  := 'ВНИМАНИЕ: Падение расхода, отсчет времени...';
        rStateCode := 2.0;
        xActive    := TRUE;
        
        // Исправление №2: Безопасное вычитание времени (защита от переполнения/отрицательного результата)
        IF tonEmptyTimer.ET < tEmptyDelay THEN
            rTimeLeft := TIME_TO_REAL(tEmptyDelay - tonEmptyTimer.ET) / 1000.0;
        ELSE
            rTimeLeft := 0.0;
        END_IF;
        
        // Возврат в работу: если расход "ожил" (насос снова захватил жидкость)
        IF rFlowDiazoActual > rZeroFlowThreshold THEN
            iState := 1; 
            
        // Успешное завершение: таймер досчитал до конца
        ELSIF tonEmptyTimer.Q THEN
            iState := 3;
            xNeedStop := TRUE; // Даем команду на закрытие клапанов
        END_IF;

    3: // --- DONE (Успешное завершение) ---
        sStateStr  := 'ЗАВЕРШЕНО: Емкость диазосоединения пуста';
        rStateCode := 3.0;
        xActive    := FALSE;
        xDone      := TRUE;
        rTimeLeft  := 0.0;
        
        // Исправление №3: Защита от гонки состояний при быстром повторном старте
        IF NOT xStart AND NOT xOldStart THEN
            iState := 0;
        END_IF;

    4: // --- ABORTED (Прервано оператором) ---
        sStateStr  := 'ПРЕРВАНО: Остановка по команде оператора';
        rStateCode := 4.0;
        xActive    := FALSE;
        xDone      := FALSE;
        rTimeLeft  := 0.0;
        
        // Исправление №3: Защита от гонки состояний при быстром повторном старте
        IF NOT xStart AND NOT xOldStart THEN
            iState := 0;
        END_IF;

END_CASE;

// 5. Вызов ПИД-регуляторов (Работают только на активных шагах 1 и 2)
IF iState = 1 OR iState = 2 THEN
    fbPidFlowDiazo(
        ACT := rFlowDiazoActual, SET := rFlowDiazoSetpoint,
        MAN := FALSE, RST := FALSE, KP := rKp_Diazo, TN := MAX(rTn_Diazo, 1.0),
        TV := rTv_Diazo, LL := 0.0, LH := 100.0
    );
    rValveOutDiazo := fbPidFlowDiazo.Y;

    fbPidPh(
        ACT := rPhActual, SET := rPhSetpoint,
        MAN := FALSE, RST := FALSE, KP := rKp_pH, TN := MAX(rTn_pH, 1.0),
        TV := rTv_pH, LL := 0.0, LH := 100.0
    );
    rValveOutSoda := fbPidPh.Y;
END_IF;

// 6. Однократный безопасный останов
IF xNeedStop THEN
    // Сбрасываем интеграторы ПИД
    fbPidFlowDiazo(MAN := TRUE, SET := 0.0, ACT := 0.0, RST := TRUE);
    fbPidPh(MAN := TRUE, SET := 0.0, ACT := 0.0, RST := TRUE);
    
    // Закрываем клапаны и возвращаем в ручной режим
    rValveOutDiazo    := 0.0;
    xAutoModeCmdDiazo := FALSE;
    rValveOutSoda     := 0.0;
    xAutoModeCmdSoda  := FALSE;
    
    xNeedStop := FALSE; // Сбрасываем триггер останова
END_IF;

xOldStart := xStart;