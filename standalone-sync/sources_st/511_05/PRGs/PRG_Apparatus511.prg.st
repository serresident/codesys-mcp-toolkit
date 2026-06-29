// @OBJECT_ID: 9f480724-c0be-439f-90b3-2c3ccbb6fbf9
// @DECLARATION
PROGRAM PRG_Apparatus511
VAR
    // Экземпляр функционального блока управления клапаном пара
    fbSteamControl_511 : FB_UniversalSteamValveControl;

    // Переменные для связи с HMI (если они еще не заданы в GVL)
    xEnableTempControl : BOOL;  // Команда с HMI: Включить автоматическое поддержание температуры
    rTempSetpoint_511  : REAL;  // Задание поддерживаемой температуры в аппарате (до 100 °C)
    xResetTempPID      : BOOL;  // Команда сброса ошибки ПИД-регулятора

    // Промежуточная переменная для связи флагов режима
    xSteamAutoMode     : BOOL;  // TRUE = АВТО, FALSE = РУЧНОЙ
END_VAR







// @IMPLEMENTATION
// --- ВЫЗОВ БЛОКА ПОДДЕРЖАНИЯ ТЕМПЕРАТУРЫ АППАРАТА 511 ---

fbSteamControl_511(
    xEnable       := xEnableTempControl,          // Команда оператора на запуск контура
    rTempActual   := GVL.gInputRegs.rTempApp511,  // Текущая температура из аппарата 511 [3, 4]
    rSetpoint     := rTempSetpoint_511,           // Уставка температуры (до 100 °C) [5, 6]
    xReset        := xResetTempPID,               // Сброс ПИД
    rKp           := GVL.gHoldingRegs.rKp_Steam_511,
    rTn           := GVL.gHoldingRegs.rTn_Steam_511,
    rTv           := GVL.gHoldingRegs.rTv_Steam_511,
    rLimitLow     := 0.0,
    rLimitHigh    := 100.0,
    
    // IN_OUT переменные (передаются по ссылке напрямую)
    rValveOut     := GVL.gHoldingRegs.rAutoSet_Steam, // Запись выхода ПИД в авто-задание клапана пара [1, 2]
    xAutoModeCmd  := xSteamAutoMode                   // Получаем команду режима от ФБ
);

// --- СИНХРОНИЗАЦИЯ РЕЖИМОВ УПРАВЛЕНИЯ ---
// Согласно вашей логике, клапан пара (fbValveSteam) работает в ручном режиме 
// когда GVL.gCoils.xManualMode_Steam = TRUE [2].
// Поскольку наш ФБ выдает TRUE для режима АВТО, нам нужно инвертировать этот сигнал:
GVL.gCoils.xManualMode_Steam := NOT xSteamAutoMode;