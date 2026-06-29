// @OBJECT_ID: 0315c496-40b5-48b0-ae72-f392c63e890a
// @DECLARATION
FUNCTION FC_ModbusToRealSwapped : REAL
VAR_INPUT
    wWord1   : WORD;   (* Первое слово из Modbus (например, 53126) *)
    wWord2   : WORD;   (* Второе слово из Modbus (например, 0) *)
END_VAR
VAR
    dwTarget : DWORD;  (* Буфер для сборки 32-битного значения *)
    wTemp1   : WORD;   (* Временные переменные для перестановки байт *)
    wTemp2   : WORD;
    pReal    : POINTER TO REAL; (* Указатель для копирования памяти *)
END_VAR







// @IMPLEMENTATION

(* 1. Переставляем байты внутри каждого слова *)
wTemp1 := ROR(wWord1, 8); (* 0xED0C станет 0x0CED *)
wTemp2 := ROR(wWord2, 8); (* 0x0000 останется 0x0000 *)

(* 2. Собираем DWORD в режиме Little-Endian (wTemp2 сдвигаем в старшие биты) *)
dwTarget := SHL(WORD_TO_DWORD(wTemp2), 16) OR WORD_TO_DWORD(wTemp1);
(* На выходе соберется строка 0x41CD0000 *)

(* 3. Копируем область памяти в REAL *)
pReal := ADR(dwTarget);
FC_ModbusToRealSwapped := pReal^;