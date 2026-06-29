// @OBJECT_ID: 8982d891-ac0a-4f55-8094-276c0250f702
// @DECLARATION
(*
    ФУНКЦИОНАЛЬНЫЙ БЛОК: FB_WaterLoading
    ВЕРСИЯ: 2.0.0
    ОПИСАНИЕ: Автоматическая загрузка воды заданной дозой.
 
    ЛОГИКА:
      - xStart OFF→ON  : старт → открываем клапан (xAutoControl:=TRUE), фиксируем объём
      - xStart ON→OFF  : прерывание оператором → закрываем клапан (xAutoControl:=FALSE)
      - Доза выполнена : rLoaded >= rDose - rDeadband → закрываем клапан, xStart:=FALSE
 
    ВАЖНО: xMode и xAutoControl — VAR_IN_OUT (прямая ссылка на внешние переменные).
           Присвоение только по триггеру (фронт старта, фронт стопа, завершение дозы).
           В рабочем цикле (xRunning=TRUE) — только обновление rLoaded, клапан не трогаем.
 
    СТАТУСЫ (rStatus):
      0.0 = IDLE
      1.0 = RUNNING
      2.0 = DONE
      3.0 = ABORTED
*)
 (*
    ФУНКЦИОНАЛЬНЫЙ БЛОК: FB_WaterLoading
    ВЕРСИЯ: 2.1.0 (Исправленная)
*)

FUNCTION_BLOCK FB_WaterLoading
VAR_INPUT
    rTotalVolume    : REAL;   (* Текущий объём сумматора расходомера, куб.м *)
    rDose           : REAL;   (* Заданная доза, куб.м *)
    rDeadband       : REAL;   (* Мёртвый остаток для предиктивного закрытия, куб.м *)
END_VAR
VAR_IN_OUT
    xStart          : BOOL;   (* Команда: ON=старт, OFF=стоп/прерывание *)
    xMode           : BOOL;   (* Режим клапана: FALSE=ручной, TRUE=авто *)
    xAutoControl    : BOOL;   (* Автозадание клапана *)
END_VAR
VAR_OUTPUT
    rLoaded         : REAL;   (* Загружено в текущем цикле, куб.м *)
    rStatus         : REAL;   (* 0=IDLE 1=RUNNING 2=DONE 3=ABORTED *)
END_VAR
VAR
    rStartVolume    : REAL;
    xLastStart      : BOOL;
    xRunning        : BOOL;
END_VAR







// @IMPLEMENTATION
// ----------------------------------------------------------------
// ФРОНТ OFF→ON : СТАРТ ДОЗИРОВАНИЯ
// ----------------------------------------------------------------
IF xStart AND NOT xLastStart THEN
    rStartVolume := rTotalVolume;
    rLoaded      := 0.0;
    xRunning     := TRUE;
    rStatus      := 1.0;
    xMode        := TRUE;   // переключаем клапан в авторежим
    xAutoControl := TRUE;   // открываем клапан
END_IF;

// ----------------------------------------------------------------
// РАБОЧИЙ ЦИКЛ: Считаем объем и проверяем достижение дозы
// ----------------------------------------------------------------
IF xRunning THEN
    rLoaded := rTotalVolume - rStartVolume;

    // Доза выполнена — предиктивное закрытие (Высший приоритет)
    IF rLoaded >= (rDose - rDeadband) THEN
        xAutoControl := FALSE;  // закрываем клапан
        xRunning     := FALSE;
        xStart       := FALSE;  // автосброс команды
        rStatus      := 2.0;    // DONE
    END_IF;
END_IF;

// ----------------------------------------------------------------
// ФРОНТ ON→OFF : ПРЕРЫВАНИЕ ОПЕРАТОРОМ
// (Сработает только если доза ЕЩЕ НЕ выполнена в этом цикле)
// ----------------------------------------------------------------
IF NOT xStart AND xLastStart AND xRunning THEN
    xRunning     := FALSE;
    xAutoControl := FALSE;  // закрываем клапан
    rStatus      := 3.0;    // ABORTED
END_IF;

// ----------------------------------------------------------------
// БУФЕР ФРОНТА (в конце скана)
// ----------------------------------------------------------------
xLastStart := xStart;