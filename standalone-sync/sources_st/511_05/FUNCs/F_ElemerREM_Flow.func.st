// @OBJECT_ID: 22b7d66b-5897-4426-b661-360de4c0c760
// @DECLARATION
(* Мгновенный расход F2: 2 регистра WORD, Big-Endian REAL *)
FUNCTION F_ElemerREM_Flow : REAL
VAR_INPUT
    pBuf : POINTER TO ARRAY[0..1] OF WORD;
END_VAR
VAR
    dw : DWORD;
	END_VAR








// @IMPLEMENTATION
IF pBuf <> 0 THEN
    // Склеиваем два WORD в один DWORD (старшее слово сдвигаем на 16 бит влево)
    dw := SHL(WORD_TO_DWORD(pBuf^[0]), 16) OR WORD_TO_DWORD(pBuf^[1]);

    // Копируем память "бит-в-бит" из DWORD в REAL
    SysMemCpy(pDest := ADR(F_ElemerREM_Flow), pSrc := ADR(dw), udiCount := 4);
END_IF