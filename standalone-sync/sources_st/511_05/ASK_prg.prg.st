// @OBJECT_ID: 34a98575-253b-42d3-9455-2cb10a7687ff
// @DECLARATION
PROGRAM ASK_prg
VAR
Exatract:	FB_ModbusToFloatArray;
pt : POINTER TO  ARRAY [0..5] OF WORD  ;

//M1_K3_AI_10_08_00 AT %IW58: ARRAY [0..7] OF WORD ; 

buff_abak: ARRAY [0..219] OF WORD ; 
buff_MDS: ARRAY [0..219] OF WORD ; 
buffR_1: ARRAY [0..119] OF REAL ; 
start_ad_mds3rtd:INT:=0;
swap_mds3rtd:INT:=6;
start_ad_mds_8UId:INT:=18;
swap_mds_8UI:INT:=16;

AI: FB_AI;


  
	Info : __SYSTEM.VAR_INFO;

    pAddress : POINTER TO BYTE;
	adress:UDINT;
END_VAR







// @IMPLEMENTATION
//берем  с модуля  M1_K3_AI_10_08_00 значения  и  копируем в промежуточный буфер   
SysMemCpy(ADR(buff_abak), ADR( %IW0), 8 * SIZEOF(WORD));

//берем  с модуля  MDS_3RTD_1  значения  и  копируем в промежуточный буфер   
SysMemCpy(ADR(buff_MDS), ADR( %IW57), 6 * SIZEOF(WORD));


//берем  с  терминала  tv 006
SysMemCpy(ADR(buff_MDS[swap_mds3rtd]), ADR( %IW53), 2* SIZEOF(WORD));

//берем  с  терминала  tv 006
SysMemCpy(ADR(buff_MDS[swap_mds3rtd+2]), ADR( %IW55), 2* SIZEOF(WORD));

Exatract(aDataIn:=buff_MDS,aDataOut=>buffR_1,IQty:=65,iMode:=1);


// 3. Маппинг (Присвоение значений переменным структуры)
// -------------------------------------------------------------

// === Модуль M1 () ===
GVL.gInputRegs. rPosValveDiazo  := AIToFloat(buff_abak[0],0,100); // 
GVL.gInputRegs.rPosValveSoda  := AIToFloat(buff_abak[1],0,100); // 
GVL.gInputRegs.rPosValveSteam  := AIToFloat(buff_abak[2],0,100); // 
GVL.gInputRegs.rPhApp511  := AIToFloat(buff_abak[4],0,14); // 


// === Модуль M5 () ===

GVL.gInputRegs.rTempApp511  :=buffR_1[0];// TT 511
//GVL.gInputRegs.rTempApp511  :=FC_ModbusToRealSwapped(wWord1 := buff_MDS[0], wWord2 := buff_MDS[1]);
// === Модуль M2 () ===
GVL.rCmdValveDiazo := FloatToAI(gvl.gHoldingRegs.AO1_CmdValveDiazo);

GVL.rCmdValveSoda := FloatToAI(gvl.gHoldingRegs.AO2_CmdValveSoda);

GVL.rCmdValveSteam := FloatToAI(gvl.gHoldingRegs.AO3_CmdValveSteam);


// === Модуль M5 (Индексы 0..2) ===
//GVL.gInputRegs.rTempApp511   := buffR_1[0]; // TT 511


//// === весы  tenzo  M1 ===

	//AI(F_WORD_IN:= gvl.WE_1_f, S_WORD_IN:= gvl.WE_1_s, RANGE_CONV:=FALSE, VAL_OUT=> GVL.gInputRegs.WE_1);
GVL.gInputRegs.WE_1:=buffR_1[3];
GVL.gInputRegs.WE_2:=buffR_1[4];
//// === весы  tenzo  M2 ===
//AI(F_WORD_IN:= gvl.WE_2_f, S_WORD_IN:= gvl.WE_2_s, RANGE_CONV:=TRUE, VAL_OUT=> GVL.gInputRegs.WE_2);