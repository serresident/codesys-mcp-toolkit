// @OBJECT_ID: c5ea459a-3d8c-4dff-9b4c-b4e64976f6c9
// @DECLARATION
PROGRAM PRG_Apparatus511_CascadeDrain
VAR
    // Экземпляр последней версии блока (с конечным автоматом)
    fbCascadeDrain511 : FB_AutoCouplingDrainCascade;
    
    // Вспомогательные переменные для инверсии ручного/автоматического режимов
    xDiazoAutoMode    : BOOL;
    xSodaAutoMode     : BOOL;
END_VAR








// @IMPLEMENTATION

// --- 1. ВЫЗОВ АЛГОРИТМА СЛИВА С ПОДДЕРЖАНИЕМ pH ---
fbCascadeDrain511(
    // Управление
    xStart             := GVL.gCoils.xStartCoupling_511,       
    
    // Параметры Диазосоединения
    rFlowDiazoActual   := GVL.gInputRegs.IR_FlowDiazo,         // Мгновенный расход [1]
    rFlowDiazoSetpoint := GVL.gHoldingRegs.rSetFlowDiazo_511,  // Уставка расхода [1]
    
    // Параметры pH
    rPhActual          := GVL.gInputRegs.rPhApp511,            // Показания pH-метра [1]
    rPhSetpoint        := GVL.gHoldingRegs.rSetPh_511,         // Целевая уставка pH [1]
    
    // Настройки условия завершения (конвертация UINT секунд в TIME)
    rZeroFlowThreshold := GVL.gHoldingRegs.rZeroFlowThreshold_511, 
    tEmptyDelay        := UDINT_TO_TIME(UINT_TO_UDINT(GVL.gHoldingRegs.uiEmptyDelaySec_511) * 1000), 
    
    // Настройки ПИД
    rKp_Diazo          := GVL.gHoldingRegs.rKp_Diazo_511,
    rTn_Diazo          := GVL.gHoldingRegs.rTn_Diazo_511,
    rKp_pH             := GVL.gHoldingRegs.rKp_pH_511,
    rTn_pH             := GVL.gHoldingRegs.rTn_pH_511,

    // Прямая связь с авто-заданиями физических клапанов (IN_OUT)
    rValveOutDiazo     := GVL.gHoldingRegs.rAutoSet_Diazo,     // [3]
    xAutoModeCmdDiazo  := xDiazoAutoMode,
    
    rValveOutSoda      := GVL.gHoldingRegs.rAutoSet_Soda,      // [3]
    xAutoModeCmdSoda   := xSodaAutoMode
);

// --- 2. СИНХРОНИЗАЦИЯ РЕЖИМОВ (Ручной/Авто) ---
// В физической логике клапанов TRUE = Ручной режим, поэтому инвертируем команду от блока
GVL.gCoils.xManualMode_Diazo := NOT xDiazoAutoMode;
GVL.gCoils.xManualMode_Soda  := NOT xSodaAutoMode;

// --- 3. ПЕРЕДАЧА СТАТУСОВ КОНЕЧНОГО АВТОМАТА НА HMI ---
// Булевые лампочки состояния процесса
GVL.gCoils.xCouplingActive_511 := fbCascadeDrain511.xActive; 
GVL.gCoils.xCouplingDone_511   := fbCascadeDrain511.xDone;   

// Числовые коды, оставшееся время и текст
GVL.gInputRegs.rTimeLeft_511   := fbCascadeDrain511.rTimeLeft;  // Оставшиеся секунды при падении расхода
GVL.gInputRegs.rStateCode_511  := fbCascadeDrain511.rStateCode; // 0.0, 1.0, 2.0, 3.0, 4.0
GVL.sStateStr_511              := fbCascadeDrain511.sStateStr;  // Расшифровка этапа