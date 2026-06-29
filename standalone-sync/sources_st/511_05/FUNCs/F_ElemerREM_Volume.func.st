// @OBJECT_ID: 4d85027d-cb35-4b94-8eef-0ae63feaf4df
// @DECLARATION
(*  Накопленный объём F1: 4 регистра WORD, Big-Endian Double → REAL  *)
FUNCTION F_ElemerREM_Volume : REAL
VAR_INPUT
    pBuf : POINTER TO ARRAY[0..3] OF WORD;
END_VAR
VAR
    lr   : LREAL;
    pW   : POINTER TO WORD;
END_VAR







// @IMPLEMENTATION
pW    := ADR(lr);
pW[3] := pBuf^[0];
pW[2] := pBuf^[1];
pW[1] := pBuf^[2];
pW[0] := pBuf^[3];
F_ElemerREM_Volume := LREAL_TO_REAL(lr);