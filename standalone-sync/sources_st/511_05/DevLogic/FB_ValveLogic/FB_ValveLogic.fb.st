// @OBJECT_ID: b69ae05e-2751-46ad-b908-1efa69733278
// @DECLARATION
(*
    Название: FB_ValveLogic
    Автор: Gemini Industrial AI
    Версия: 1.1.0
    Описание: Управление клапаном с прямой записью REAL значения через указатель.
*)
FUNCTION_BLOCK FB_ValveLogic
VAR_INPUT
    xModeManual     : BOOL;             // Переключатель: TRUE - Ручной, FALSE - Авто
    xEnableLog      : BOOL := TRUE;     // Разрешить текстовое логирование
    rMinLimit       : REAL := 0.0;      // Нижний предел уставки
    rMaxLimit       : REAL := 100.0;    // Верхний предел уставки (например, 100%)
END_VAR

VAR_OUTPUT
    sStatus         : STRING(80);       // Диагностика на русском языке
    rActualSetpoint : REAL;             // Текущая выбранная уставка
    xError          : BOOL;             // Флаг ошибки указателей
END_VAR

VAR
    (* Указатели *)
    pSetMan         : POINTER TO REAL;  // Ссылка на ручную переменную (HMI)
    pSetAuto        : POINTER TO REAL;  // Ссылка на авто переменную (PID)
    pOutReal        : POINTER TO REAL;  // Ссылка на выходную переменную REAL
    
END_VAR








// @IMPLEMENTATION
// 1. Проверка инициализации основного выходного указателя
IF pOutReal = 0 THEN
    xError := TRUE;
    sStatus := 'ОШИБКА: Целевой адрес OutReal не назначен!';
    RETURN; // Прекращаем выполнение, чтобы не вызвать исключение
END_IF

// 2. Выбор источника данных в зависимости от режима
IF xModeManual THEN
    // Режим РУЧНОЙ
    IF pSetMan <> 0 THEN
        rActualSetpoint := pSetMan^;
        xError := FALSE;
        IF xEnableLog THEN sStatus := 'Режим: РУЧНОЙ. Уставка с HMI.'; END_IF
    ELSE
        xError := TRUE;
        sStatus := 'Ошибка: Пустой указатель на ручную уставку!';
    END_IF
ELSE
    // Режим АВТО
    IF pSetAuto <> 0 THEN
        rActualSetpoint := pSetAuto^;
        xError := FALSE;
        IF xEnableLog THEN sStatus := 'Режим: АВТО. Управление от ПЛК.'; END_IF
    ELSE
        xError := TRUE;
        sStatus := 'Ошибка: Пустой указатель на авто-уставку!';
    END_IF
END_IF

// 3. Обработка ТАУ (ограничение диапазона)
rActualSetpoint := LIMIT(rMinLimit, rActualSetpoint, rMaxLimit);

// 4. Прямая запись в память по адресу, если нет ошибок
IF NOT xError THEN
    pOutReal^ := rActualSetpoint;
END_IF