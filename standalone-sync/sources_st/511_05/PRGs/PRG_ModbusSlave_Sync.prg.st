// @OBJECT_ID: 808e203d-1a0e-46f1-b7a1-0b905523bfa3
// @DECLARATION
(*
* @fb: PRG_ModbusSlave_Sync
* @desc: Исправленная синхронизация через прямые указатели (устранение C0047/C0077)
*)
PROGRAM PRG_ModbusSlave_Sync
VAR
    fbSlv               : abakplcutils.MDB;
    sStatus             : STRING(255);
    
    // Вспомогательные буферы
    wMbHolding          : ARRAY[0..500] OF WORD; 
    wOldMbHolding       : ARRAY[0..500] OF WORD; 
    
    // Указатели для работы со структурами GVL как с массивами
    pCurrWord           : POINTER TO WORD;
    pOldWord            : POINTER TO WORD;
    
    wIndex              : WORD;
    uiHoldRegsCnt       : WORD;
    uiInRegsCnt         : WORD;
    xFirstLoop          : BOOL := TRUE;
	
    C_INPUT_REG_START   : WORD := 1;
    C_HOLD_REG_START    : WORD := 1000;
END_VAR









// @IMPLEMENTATION
// 1. Инициализация и расчет длин (через SIZEOF, чтобы не зависеть от типов)
IF xFirstLoop THEN
    uiInRegsCnt   := ANY_TO_WORD(SIZEOF(GVL.gInputRegs) / 2);
    uiHoldRegsCnt := ANY_TO_WORD(SIZEOF(GVL.gHoldingRegs) / 2);
    
    // Предзаполнение Modbus и локального зеркала (используем SysMem для скорости)
    fbSlv.SetWordRegs(reg := C_HOLD_REG_START, pBuf := ADR(GVL.gHoldingRegs), cnt := uiHoldRegsCnt);
    SysMem.SysMemCpy(pDest := ADR(wOldMbHolding), pSrc := ADR(GVL.gHoldingRegs), udiCount := uiHoldRegsCnt * 2);
    
    xFirstLoop := FALSE;
    RETURN;
END_IF

// --- ШАГ 1: Input Registers (Запись всей структуры целиком через указатель) ---
sStatus := 'Обновление Input Registers';
fbSlv.SetWordRegs(reg := C_INPUT_REG_START, pBuf := ADR(GVL.gInputRegs), cnt := uiInRegsCnt);

// --- ШАГ 2: Holding Registers (Синхронизация через пошаговый доступ к памяти) ---
sStatus := 'Синхронизация Holding...';
fbSlv.GetWordRegs(reg := C_HOLD_REG_START, pBuf := ADR(wMbHolding), cnt := uiHoldRegsCnt);

FOR wIndex := 0 TO (uiHoldRegsCnt - 1) DO
    // Получаем адреса текущего слова в GVL и в нашем зеркале Old
    pCurrWord := ADR(GVL.gHoldingRegs) + (wIndex * 2); // Смещение в байтах (WORD = 2 байта)
    pOldWord  := ADR(wOldMbHolding) + (wIndex * 2);

    // Сценарий А: Изменение в ПЛК
    IF pCurrWord^ <> pOldWord^ THEN
        fbSlv.SetWord(reg := C_HOLD_REG_START + wIndex, val := pCurrWord^);
        pOldWord^ := pCurrWord^; // Обновляем зеркало
        
    // Сценарий Б: Изменение в Modbus (от SCADA)
    ELSIF wMbHolding[wIndex] <> pOldWord^ THEN
        pCurrWord^ := wMbHolding[wIndex]; // Пишем напрямую в структуру GVL
        pOldWord^  := wMbHolding[wIndex]; // Обновляем зеркало
    END_IF
END_FOR

// Синхронизация с энергонезависимой памятью
PVL.rHoldingRegs := GVL.gHoldingRegs;