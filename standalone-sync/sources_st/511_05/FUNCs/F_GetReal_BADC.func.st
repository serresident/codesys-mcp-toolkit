// @OBJECT_ID: b25eaad9-59ce-4c23-9aa6-5c998f777003
// @DECLARATION
(*
    ФУНКЦИЯ: F_GetReal_BADC
    ОПИСАНИЕ: Разбор REAL 32 бита из 2 регистров WORD, порядок байт BADC.

    Прибор передаёт байты в порядке: B A D C
    (где ABCD = нормальный Big-Endian порядок)

    Раскладка по байтам:
      pSrc[0] = B,  pSrc[1] = A,  pSrc[2] = D,  pSrc[3] = C

    Для Little-Endian ЦПУ нужно собрать DCBA:
      pDst[0] = C = pSrc[3]
      pDst[1] = D = pSrc[2]
      pDst[2] = A = pSrc[1]
      pDst[3] = B = pSrc[0]
*)
FUNCTION F_GetReal_BADC : REAL
VAR_INPUT
    pBuf : POINTER TO ARRAY[0..1] OF WORD;
END_VAR
VAR
    dw   : DWORD;
    pSrc : POINTER TO BYTE;
    pDst : POINTER TO BYTE;
END_VAR








// @IMPLEMENTATION

pSrc    := ADR(pBuf^[0]);
pDst    := ADR(dw);
pDst[0] := pSrc[3]; // C
pDst[1] := pSrc[2]; // D
pDst[2] := pSrc[1]; // A
pDst[3] := pSrc[0]; // B
SysMemCpy(pDest := ADR(F_GetReal_BADC), pSrc := ADR(dw), udiCount := 4);