// @OBJECT_ID: 4a778488-a136-43da-a5b5-63d2fca365f4
// @DECLARATION
PROGRAM PRG_Valves
VAR

    // Экземпляры логики управления для каждого клапана
    fbValveDiazo : FB_ValveLogic;
    fbValveSoda  : FB_ValveLogic;
    fbValveSteam : FB_ValveLogic;

    // Флаг для однократной инициализации указателей
    xInitDone    : BOOL := FALSE;
    // Экземпляр функционального блока для клапана подачи воды
    fbWaterValve : FB_ValveS_Compact;
    


END_VAR








// @IMPLEMENTATION
// --- 1. ОДНОКРАТНАЯ ИНИЦИАЛИЗАЦИЯ (Привязка адресов) ---
IF NOT xInitDone THEN
    
    // Привязка для клапана Диазосоединения
    fbValveDiazo.Init(
        pManualVar := ADR(gvl.gHoldingRegs.rValveManSet_Diazo),       // Уставка с HMI
        pAutoVar   := ADR(gvl.gHoldingRegs.rAutoSet_Diazo),     // Уставка от ПИД/Логики
        pOutputVar := ADR(gvl.gHoldingRegs.AO1_CmdValveDiazo)       // Физический выход (M2)
    );

    // Привязка для клапана Едкого натра (Соды)
    fbValveSoda.Init(
        pManualVar := ADR(gvl.gHoldingRegs.rValveManSet_Soda), 
        pAutoVar   := ADR(gvl.gHoldingRegs.rAutoSet_Soda), 
        pOutputVar := ADR(gvl.gHoldingRegs.AO2_CmdValveSoda)        // Физический выход (M2)
    );

    // Привязка для клапана Пара
    fbValveSteam.Init(
        pManualVar := ADR(gvl.gHoldingRegs.rValveManSet_Steam), 
        pAutoVar   := ADR(gvl.gHoldingRegs.rAutoSet_Steam), 
        pOutputVar := ADR(gvl.gHoldingRegs.AO3_CmdValveSteam)       // Физический выход (M2)
    );

    xInitDone := TRUE;
END_IF;

// --- 2. ЦИКЛИЧЕСКИЙ ВЫЗОВ ЛОГИКИ ---

// Управление клапаном Диазосоединения
fbValveDiazo(
    xModeManual :=gvl.gCoils.xManualMode_Diazo,
    rMinLimit   := 0.0,
    rMaxLimit   := 100.0
);

// Управление клапаном Едкого натра
fbValveSoda(
    xModeManual := gvl.gCoils.xManualMode_Soda,
    rMinLimit   := 0.0,
    rMaxLimit   := 100.0
);

// Управление клапаном Пара
fbValveSteam(
    xModeManual := gvl.gCoils.xManualMode_Steam,
    rMinLimit   := 0.0,
    rMaxLimit   := 100.0
);


// Вызов блока управления водяным клапаном
fbWaterValve(
    xMode        := gvl.gCoils.xWaterValve_AutoMode,
    xManControl  := gvl.gcoils.xWaterValve_HmiOpen,
    xAutoControl := gvl.gcoils.xWaterValve_AutoReq,
    xOutControl  => gvl.gInputs.xWaterValve_Out
);