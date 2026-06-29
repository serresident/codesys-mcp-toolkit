// @OBJECT_ID: 733d5e5a-4ad1-4a84-973a-cf97214e756a
// @DECLARATION
{attribute 'pack_mode' := '1'}
TYPE Coils :
STRUCT
// --- Режимы работы (команды из HMI) ---
xManualMode_Diazo   : BOOL;        // 1. Ручной режим Diazo
xManualMode_Soda    : BOOL;        // 2. Ручной режим Soda
xManualMode_Steam   : BOOL;        // 3. Ручной режим Steam
// --- Управление водой имитатором ---
xWaterValve_AutoMode : BOOL;       // 4. TRUE=Автоматический режим, FALSE=Ручной
xWaterValve_HmiOpen  : BOOL;       // 5. Открытие по кнопке из HMI (в ручном режиме)
xWaterValve_AutoReq  : BOOL;       // 6. Запрос на открытие от автоматики
// --- Сигналы запуска ---
xWaterStart          : BOOL;       // 7. Запуск дозы воды из HMI
xStartHeating_511    : BOOL;       // 8. Запуск прогрева
// --- Сигналы и статусы стадии промывки (Cascade Drain) ---
xStartCoupling_511   : BOOL;       // 9. Запуск с HMI: признак запуска стадии промывки
xCouplingActive_511  : BOOL;       // 10. Статус для HMI: признак "работа идет"
xCouplingDone_511    : BOOL;       // 11. Статус для HMI: признак "успешно готово"
// --- Режим удержания температуры ---
xKeepTempHeating_511 : BOOL;       // 12. TRUE = удержание температуры после нагрева, FALSE = разовый нагрев
// --- Служебные ---
PLC_READ             : BOOL := TRUE; // 13. Флаг чтения PLC
END_STRUCT
END_TYPE