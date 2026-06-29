// @OBJECT_ID: f24ff6c8-e667-4d1a-8a4a-3707ce6a677c
// @DECLARATION
(* ИСПРАВЛЕНИЕ v4.1.0:
        - Исправлен разбор lrTotalVolume (LREAL / Double 64 бит).
        - Прибор передаёт регистры в порядке Big-Endian (src[0] = MSW, src[3] = LSW).
        - ЦПУ ПЛК — Little-Endian, поэтому выполняется разворот по WORD-словам:
          pW[3] = src[0] (старший), pW[0] = src[3] (младший).
        - Побайтовый подход заменён на пословный (POINTER TO WORD) — корректнее
          и безопаснее, так как каждый WORD внутри уже находится в правильном
          байтовом порядке аппаратуры Little-Endian.
*)
 
FUNCTION_BLOCK fbElemerREM
VAR_INPUT
    pFlowBuffer         : POINTER TO ARRAY[0..1] OF WORD;  (* Канал 0: Мгновенный расход F2, 2 регистра WORD *)
    pVolumeBuffer       : POINTER TO ARRAY[0..3] OF WORD;  (* Канал 1: Накопленный объём F1, 4 регистра WORD *)
    xCommError          : BOOL;                             (* Признак ошибки связи (из статуса Modbus Slave) *)
    xEnableLog          : BOOL := TRUE;                     (* Флаг разрешения детального логирования на HMI *)
END_VAR
VAR_IN_OUT
    xResetTotalizer     : BOOL;  (* Команда сброса сумматора с HMI — автосброс после выполнения *)
END_VAR
VAR_OUTPUT
    xDataValid          : BOOL;         (* Флаг достоверности данных для контуров ТАУ *)
    rInstantFlow        : REAL;         (* Мгновенный расход F2, куб.м/ч *)
    lrTotalVolume       : LREAL;        (* Накопленный общий объём F1, куб.м *)
    sStatus             : STRING(255);  (* Строка текущего шага для оператора панели *)
END_VAR
VAR
    (* Автомат состояний *)
    eState              : E_REM_State;
    eLastState          : E_REM_State;
 
    (* Указатели для разбора REAL (32 бит) *)
    pByteSrc            : POINTER TO BYTE;
    pByteDst            : POINTER TO BYTE;
    dwRealParser        : DWORD;
 
    (* Указатель для разбора LREAL (64 бит) — пословный разворот *)
    pWordDst            : POINTER TO WORD;  (* Указатель на LREAL как массив из 4 WORD *)
 
    (* Системные таймеры *)
    tonStateTimer       : TON;
    udiMinutesInState   : UDINT;
END_VAR
VAR CONSTANT
    DEVICE_DISCONNECTED : REAL := -10000.0;  (* Маркер аварии датчика *)
END_VAR
 








// @IMPLEMENTATION
//==============================================================================
// Расчёт времени нахождения в текущем состоянии (в минутах для HMI)
//==============================================================================
tonStateTimer(IN := (eState = eLastState), PT := T#240h);
udiMinutesInState := TIME_TO_UDINT(tonStateTimer.ET) / 60000;
 
//==============================================================================
// 1. ДИАГНОСТИЧЕСКИЙ КОНТРОЛЬ АВАРИЙ СВЯЗИ ВЕРХНЕГО УРОВНЯ
//==============================================================================
IF xCommError THEN
    eState := E_REM_State.ERROR_COMM;
ELSIF xResetTotalizer AND eState <> E_REM_State.ERROR_COMM THEN
    eState := E_REM_State.RESET_LOGIC;
ELSIF eState <> E_REM_State.ERROR_COMM AND eState <> E_REM_State.RESET_LOGIC THEN
    eState := E_REM_State.OPERATING;
END_IF;
 
//==============================================================================
// 2. СТРУКТУРА СТЕЙТ-МАШИНЫ
//==============================================================================
CASE eState OF
 
    E_REM_State.INIT: //--------------------------------------------------------
        sStatus        := 'ЭЛЕМЕР-РЭМ: Ожидание первого скана и данных от Modbus-каналов';
        rInstantFlow   := DEVICE_DISCONNECTED;
        lrTotalVolume  := LREAL#-10000.0;
        xDataValid     := FALSE;
 
        IF pFlowBuffer <> 0 AND pVolumeBuffer <> 0 AND NOT xCommError THEN
            eState := E_REM_State.OPERATING;
        END_IF;
 
 
    E_REM_State.OPERATING: //---------------------------------------------------
        sStatus := 'ЭЛЕМЕР-РЭМ: Данные успешно обновляются, идёт технологический учёт';
 
        IF pFlowBuffer <> 0 AND pVolumeBuffer <> 0 THEN
 
            // ----------------------------------------------------------------
            // РАЗБОР МГНОВЕННОГО РАСХОДА F2
            // Канал 0, REAL 32 бита, формат прибора DCBA (Big-Endian)
            // Побайтовый разворот → Little-Endian ЦПУ ПЛК
            // ----------------------------------------------------------------
            pByteSrc := ADR(pFlowBuffer^[0]);
            pByteDst := ADR(dwRealParser);
 
            IF pByteSrc <> 0 AND pByteDst <> 0 THEN
                pByteDst[0] := pByteSrc[3]; // D → LSB
                pByteDst[1] := pByteSrc[2]; // C
                pByteDst[2] := pByteSrc[1]; // B
                pByteDst[3] := pByteSrc[0]; // A → MSB
                SysMemCpy(pDest := ADR(rInstantFlow), pSrc := ADR(dwRealParser), udiCount := SIZEOF(rInstantFlow));
            END_IF;
 
 
            // ----------------------------------------------------------------
            // РАЗБОР НАКОПЛЕННОГО ОБЪЁМА F1
            // Канал 1, Double/LREAL 64 бита, Big-Endian порядок WORD-регистров:
            //   src[0] = MSW (старший), src[3] = LSW (младший)
            //
            // Алгоритм прибора (из документации):
            //   v  = (uint64_t)src[0] << 48
            //   v |= (uint64_t)src[1] << 32
            //   v |= (uint64_t)src[2] << 16
            //   v |= (uint64_t)src[3]
            //
            // На Little-Endian ЦПУ ПЛК LREAL в памяти хранится так:
            //   pW[0] = LSW (биты  0..15)
            //   pW[1]        (биты 16..31)
            //   pW[2]        (биты 32..47)
            //   pW[3] = MSW (биты 48..63)
            //
            // Поэтому разворачиваем порядок WORD-ов:
            //   pW[3] := src[0]   (MSW прибора → старший WORD LREAL)
            //   pW[2] := src[1]
            //   pW[1] := src[2]
            //   pW[0] := src[3]   (LSW прибора → младший WORD LREAL)
            //
            // Байты ВНУТРИ каждого WORD НЕ трогаем — аппаратура ПЛК
            // уже прочитала их корректно в Little-Endian.
            // ----------------------------------------------------------------
            pWordDst := ADR(lrTotalVolume);
 
            IF pWordDst <> 0 THEN
                pWordDst[3] := pVolumeBuffer^[0]; // MSW прибора → старший WORD
                pWordDst[2] := pVolumeBuffer^[1];
                pWordDst[1] := pVolumeBuffer^[2];
                pWordDst[0] := pVolumeBuffer^[3]; // LSW прибора → младший WORD
            END_IF;
 
 
            // ----------------------------------------------------------------
            // ЗАЩИТА ТАУ: Валидация на NaN
            // ----------------------------------------------------------------
            IF rInstantFlow <> rInstantFlow OR lrTotalVolume <> lrTotalVolume THEN
                sStatus    := 'ЭЛЕМЕР-РЭМ: Критическая ошибка! Считано неопределённое значение NaN.';
                xDataValid := FALSE;
            ELSE
                xDataValid := TRUE;
            END_IF;
 
        ELSE
            sStatus    := 'ЭЛЕМЕР-РЭМ: Внимание, обнаружен нулевой указатель буферов опроса!';
            xDataValid := FALSE;
        END_IF;
 
 
    E_REM_State.RESET_LOGIC: //-------------------------------------------------
        sStatus    := 'ЭЛЕМЕР-РЭМ: Выполняется процедура сброса сумматора по команде оператора';
        xDataValid := TRUE;
 
        IF NOT xResetTotalizer THEN
            eState := E_REM_State.OPERATING;
        END_IF;
 
 
    E_REM_State.ERROR_COMM: //--------------------------------------------------
        sStatus       := 'АВАРИЯ связи: Прибор не отвечает. Проверьте кабель RS-485!';
        rInstantFlow  := DEVICE_DISCONNECTED;
        lrTotalVolume := LREAL#-10000.0;
        xDataValid    := FALSE;
 
        IF NOT xCommError THEN
            eState := E_REM_State.INIT;
        END_IF;
 
END_CASE;
 
 
//==============================================================================
// 3. ДИАГНОСТИЧЕСКОЕ ЛОГИРОВАНИЕ ДЛЯ ОПЕРАТОРА ПАНЕЛИ
//==============================================================================
IF xEnableLog AND (eState <> eLastState) THEN
    eLastState := eState;
    sStatus    := CONCAT(sStatus, CONCAT(' | Прошло времени: ', UDINT_TO_STRING(udiMinutesInState)));
    sStatus    := CONCAT(sStatus, ' мин.');
END_IF;