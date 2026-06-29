// @OBJECT_ID: 87d9b965-00ad-4702-8b83-68f97ffc0669
// @DECLARATION
PROGRAM PLC_PRG_MBS_TCP_SLAVE
VAR
	bFirstLoop	: BOOL := FALSE;
	fbSlv		: AbakPLCUtils.MDB;	
	
	pInputRegs			:	POINTER TO WORD;
	wInputRegsLength	:	WORD 	:= SIZEOF(GVL.gInputRegs)/2;
	
	pHoldingRegs			:	POINTER TO WORD;
	wHoldingRegsLength	:	WORD 	:= SIZEOF(GVL.gHoldingRegs)/2;
	
	pInputs			:	POINTER TO BOOL;
	wInputsLength	:	WORD 	:= SIZEOF(GVL.gInputs);
	
	pCoils			:	POINTER TO BOOL;
	wCoilsLength	:	WORD 	:= SIZEOF(GVL.gCoils);
	
	wIndex		:	WORD := 0; 
	
	pMbHolding			:	POINTER TO WORD;
	pOldMbHoldingRegs			:	POINTER TO WORD;
	pOldHoldingRegs			:	POINTER TO WORD;
	
	wMbHolding	:   ARRAY[0..1] OF WORD;
	wOldMbHoldingRegs	:   ARRAY[0..( SIZEOF(GVL.gHoldingRegs)/2-1)] OF WORD;
	wOldHoldingRegs	:   ARRAY[0..(SIZEOF(GVL.gHoldingRegs)/2-1)] OF WORD;
	
	pMbCoil		:	POINTER TO BOOL;
	pOldMbCoils			:	POINTER TO BOOL;
	pOldCoils			:	POINTER TO BOOL;
	
	bMbCoil	:   ARRAY[0..0] OF BOOL;
	bOldMbCoils	:   ARRAY[0..(SIZEOF(GVL.gCoils) -1)] OF BOOL;
	bOldCoils	:   ARRAY[0..(SIZEOF(GVL.gCoils) -1)] OF BOOL;
	
	bIsGetMb: BYTE := 0;
	
	    wInputRegsOffset    : WORD := 0;  // InputRegs начинаются с адреса 1000
    wInputsOffset       : WORD := 499;   // Inputs начинаются с адреса  
    wHoldingRegsOffset  : WORD := 100;     // HoldingRegs - без смещения (или задай своё)
    wCoilsOffset        : WORD := 0;     // Coi
END_VAR








// @IMPLEMENTATION
IF NOT bFirstLoop THEN
	fbSlv.IsVirtualModbus := 0;
	
	GVL.gInputRegs.INPUTREGS := SIZEOF(GVL.gInputRegs)/2;
	GVL.gInputRegs.HOLDINGS := SIZEOF(GVL.gHoldingRegs)/2;
	GVL.gInputRegs.INPUTS := SIZEOF(GVL.gInputs);
	GVL.gInputRegs.COILS := SIZEOF(GVL.gCoils);
	
	MBS_HoldingRegs_Change();
	MBS_Coils_Change();
	
	GVL.gHoldingRegs :=PVL.rHoldingRegs;
	bFirstLoop := TRUE;
ELSE
	MBS_HoldingRegs_Change();
	MBS_Coils_Change();

	MBS_InputRegs_WRITE();
	MBS_Inputs_WRITE();
	PVL.rHoldingRegs :=GVL.gHoldingRegs;
END_IF