// @OBJECT_ID: 1a60827f-517f-4c47-852b-c004dbd7c44c
// @DECLARATION
METHOD PUBLIC Init : BOOL
VAR_INPUT
    pManualVar       : POINTER TO REAL; // Адрес Holding Register (Ручной режим с HMI)
    pAutoVar         : POINTER TO REAL; // Адрес уставки из логики/ПИД (Авто режим)
    pOutputVar       : POINTER TO REAL; // Адрес целевой переменной (куда пишем итог)
END_VAR









// @IMPLEMENTATION


pSetMan  := pManualVar;
pSetAuto := pAutoVar;
pOutReal := pOutputVar;

Init := (pSetMan <> 0 AND pSetAuto <> 0 AND pOutReal <> 0);