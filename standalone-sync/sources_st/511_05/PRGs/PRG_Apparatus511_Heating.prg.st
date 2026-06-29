// @OBJECT_ID: 7ad46e98-502c-4d9e-a2ee-bf251bb90bbe
// @DECLARATION
PROGRAM PRG_Apparatus511_Heating
VAR
    // Экземпляр нашего блока автоматического нагрева
    fbAutoHeater511 : FB_AutoHeater;

    // Вспомогательная переменная для связи флагов режима клапана
    xSteamAutoMode  : BOOL; 
END_VAR



// @IMPLEMENTATION
// --- Автоматический нагрев аппарата 511 ---
fbAutoHeater511(
// --- Входы управления с HMI ---
xStart        := GVL.gCoils.xStartHeating_511,      // Признак запуска нагрева с панели оператора
xKeepTemp     := GVL.gCoils.xKeepTempHeating_511,   // TRUE = поддерживать температуру после достижения
rTargetTemp   := GVL.gHoldingRegs.rSetTempApp511,   // Уставка целевой температуры (до 100 °C)
// --- Технологические параметры ---
rTempActual   := GVL.gInputRegs.rTempApp511,        // Фактическая температура в емкости
rTolerance    := 0.5,                               // Допуск в градусах
// --- Настройки пид ---
rKp           := GVL.gHoldingRegs.rKp_Steam_511,
rTn           := GVL.gHoldingRegs.rTn_Steam_511,
rTv           := GVL.gHoldingRegs.rTv_Steam_511,
// --- Выходы на исполнительные механизмы (IN_OUT) ---
rValveOut     := GVL.gHoldingRegs.rAutoSet_Steam,   
xAutoModeCmd  := xSteamAutoMode
);