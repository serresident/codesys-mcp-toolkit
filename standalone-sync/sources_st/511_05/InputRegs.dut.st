// @OBJECT_ID: e329769f-e235-4ed6-8989-e7d305dd0344
// @DECLARATION
{attribute 'pack_mode' := '4'}
TYPE InputRegs : 
STRUCT
	COILS : DINT := 0;
	INPUTS: DINT := 0;
	HOLDINGS: DINT := 0;
	INPUTREGS: DINT := 0;
	
  // МОДУЛЬ АНАЛОГОВЫХ ВХОДОВ (AI)
  	{region M1_K3_AI_10_08_00 }
    // =========================================================================
    // Первые 3 канала: Сигнализация положений (% открытия) клапанов [1, 2]
    (* adr 9 *)  rPosValveDiazo  : REAL; // Канал 1: Обратная связь клапана диазосоединения
    (* adr 11 *) rPosValveSoda   : REAL; // Канал 2: Обратная связь клапана едкого натра 14%
    (* adr 13 *) rPosValveSteam  : REAL; // Канал 3: Обратная связь клапана пара
    
    // Канал 4: рН-метр
    (* adr 15 *) rPhApp511       : REAL; // Канал 4: Показания pH-метра аппарата 511 (диапазон 9,5..12 ед.)
			{endregion}
				 
				 
				 
	{region M5_MDS_3RTD_1 }
	(* adr 17 *) rTempApp511     : REAL; // Температура в аппарате 511 (до 100 С°)
				
   	{endregion}
		 
	{region tenzo tv006c }
	(* adr 19 *) WE_1            : REAL;
	(* adr 21 *) WE_2            : REAL;
		 
   	{endregion}
		 		 
	{region tenzo ELMER }

	(* adr 23 *) IR_FlowSoda   : REAL; // Текущий расход щелочи , л/мин (или м3/ч)
	(* adr 25 *) IR_TotalSoda   : REAL; // Накопленный объем щелочи, л (или м3)
	(* adr 27 *) IR_FlowWater     : REAL; // Текущий расход воды, л/мин (или м3/ч)
	(* adr 29 *) IR_TotalWater   : REAL; // Накопленный объем воды, л (или м3)
		 
    // Выходные сигналы загрузки воды
	(* adr  31*)   rWaterLoaded   : REAL;    // Сколько воды загружено, м³
	(* adr 32*)    rWaterStatus   : REAL;    // Статус загрузки воды: 0=IDLE 1=RUNNING 2=DONE 3=ABORTED
		 
	(* adr  33*)  IR_FlowDiazo   : REAL; // Текущий мгновенный расход диазосоединения (м3/ч) [3]
	(* adr  35*)  IR_TotalDiazo   : REAL; // Текущий расход диазосоединения, л/мин (или м3/ч)
		 
	(* adr  37*)  rDizoStatus   : REAL; // Текущий расход диазосоединения, л/мин (или м3/ч)

	(* adr  39*) rDiazoLoaded   : REAL; // Текущий расход диазосоединения, л/мин (или м3/ч)
rTimeLeft_511:REAL ;///Оставшиеся секунды при падении расхода
	 rStateCode_511:REAL;//
		  
   	{endregion}
		 
END_STRUCT
END_TYPE