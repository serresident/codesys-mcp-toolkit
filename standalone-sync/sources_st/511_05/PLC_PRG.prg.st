// @OBJECT_ID: 4c4237aa-22c6-43a4-ae1d-3ca0359860c2
// @DECLARATION
PROGRAM PLC_PRG // Antigravity Sync Test
VAR
    fbElemerREM         : fbElemerREM;
    
    (* Переменные из вкладки Modbus Generic Serial Slave I/O Mapping *)
    Hmi_Flow_Regs    AT %IW67  : ARRAY[0..1] OF WORD; (* Канал 0 (Мгновенный расход) *)
    Hmi_Volume_Regs  AT %IW63  : ARRAY[0..3] OF WORD; (* Канал 1 (Накопленный объем) *)
    xModbusCommError    : BOOL;                 (* Системный флаг ошибки связи с прибором *)
    xHmiResetCmd        : BOOL;                 (* Сигнал сброса сумматора с HMI-панели *)
    
    (* Выходные очищенные технологические переменные *)
    rCurrentFlowRate    : REAL;                 (* Мгновенный расход в систему, куб.м/ч *)
    lrAccumulatedVol    : LREAL;                (* Точный накопленный объем, куб.м *)
    sOperatorMessage    : STRING(255);          (* Сообщение для текстовой строки на панели *)

    fbWater             : FB_WaterLoading;      (* Наш исправленный ФБ дозирования *)
    
    // ============================================================
    // ПЕРЕМЕННЫЕ ДЛЯ ТЕСТИРОВАНИЯ И СИМУЛЯЦИИ СУММАТОРА
    // ============================================================
    xSimEnable          : BOOL := FALSE;        (* Включить режим симуляции (True = подмена датчиков) *)
    rSimFlowSpeed       : REAL := 20.0;         (* Скорость потока при открытом клапане, куб.м/ч *)
    rSimTotalStorage    : REAL := 125.45;       (* Внутренний виртуальный накопительный счетчик куб.м *)
    
    fbSimClock          : TON;                  (* Генератор тактов времени для подсчета объема *)
    rDeltaVolume        : REAL;                 (* Математический шаг приращения за 1 такт *)
    // ============================================================
END_VAR








// @IMPLEMENTATION
// ================================================================
// 1. ЧТЕНИЕ РЕАЛЬНЫХ ДАННЫХ ИЗ ПОЛЕВЫХ ПРИБОРОВ
// ================================================================
gvl.gInputRegs.IR_TotalSoda := F_ElemerREM_Volume(pBuf := ADR(%IW65));
gvl.gInputRegs.IR_FlowSoda  := F_ElemerREM_Flow(pBuf := ADR(%IW69));
gvl.gInputRegs.rTempApp511  := F_GetReal_BADC(pBuf := ADR(%IW57));


// ================================================================
// 2. ДИНАМИЧЕСКИЙ СИМУЛЯТОР РАСХОДОМЕРА ВОДЫ
// ================================================================
// Тактовый генератор: срабатывает каждые 100 мс (0.1 секунды) для плавности хода счета
fbSimClock(IN := xSimEnable AND NOT fbSimClock.Q, PT := T#100ms);

IF xSimEnable THEN
    // ЕСЛИ СИМУЛЯЦИЯ ВКЛЮЧЕНА:
    
    // Имитируем поведение потока в зависимости от команды на клапан
    IF gvl.gCoils.xWaterValve_AutoReq THEN
        // Клапан открыт автоматикой -> задаем симуляционный расход
        gvl.gInputRegs.IR_FlowWater := rSimFlowSpeed; 
        
        // Расчет приращения сумматора за 100мс: (куб.м/ч * 0.1с) / 3600с
        IF fbSimClock.Q THEN
            rDeltaVolume := (rSimFlowSpeed * 0.1) / 3600.0;
            rSimTotalStorage := rSimTotalStorage + rDeltaVolume;
        END_IF;
    ELSE
        // Клапан закрыт -> поток прекращается
        gvl.gInputRegs.IR_FlowWater := 0.0;
    END_IF;

    // ПОДМЕНЯЕМ значение сумматора результатом симуляции для ФБ дозирования
    gvl.gInputRegs.IR_TotalWater := rSimTotalStorage;

ELSE
    // ЕСЛИ СИМУЛЯЦИЯ ВЫКЛЮЧЕНА (РАБОЧИЙ РЕЖИМ):
    
    // Читаем физический прибор с адреса %IW71 и %IW75
    gvl.gInputRegs.IR_TotalWater := F_ElemerREM_Volume(pBuf := ADR(%IW71));
    gvl.gInputRegs.IR_FlowWater  := F_ElemerREM_Flow(pBuf := ADR(%IW75));
    
    // Мягко синхронизируем симулятор, чтобы при включении тумблера счет не прыгал назад/вперед
    rSimTotalStorage := gvl.gInputRegs.IR_TotalWater;
END_IF;


// ================================================================
// 3. ВЫЗОВ И ПРОВЕРКА ФУНКЦИОНАЛЬНОГО БЛОКА ЗАГРУЗКИ ВОДЫ
// ================================================================
fbWater(
    rTotalVolume := gvl.gInputRegs.IR_TotalWater,        // Сюда идет либо физический объем, либо симуляция
    rDose        := gvl.gHoldingRegs.rWaterDose,         // Заданная уставка дозы (куб.м)
    rDeadband    := 0.05,                                // Упреждение закрытия (0.05 куб.м)
    xStart       := gvl.gCoils.xWaterStart,              // Команда Старт/Стоп
    xMode        := gvl.gCoils.xWaterValve_AutoMode,     // Флаг режима АВТО клапана
    xAutoControl := gvl.gCoils.xWaterValve_AutoReq       // Управление клапаном (выход на открытие)
);

    gvl.gInputRegs.rWaterLoaded:=fbWater.rLoaded;
    gvl.gInputRegs.rWaterStatus:=fbWater.rStatus;