// @OBJECT_ID: a5893dca-19fc-4f6d-bdfc-9d37b1592804
// @DECLARATION
{attribute 'pack_mode' := '1'}
TYPE Inputs : 
STRUCT	
			// =============================================================
			// Модуль M11 (MDS DIO-16BD) - Статусы насосов (Дискретные входы)
			// =============================================================
			{region M11 - MDS DIO-16BD (Статусы насосов)}

		
				     
    // Выходная переменная на физическое реле/соленоид
    xWaterValve_Out     : BOOL;  // 1 канал ФЕ
	xWaterValve_SQH :BOOL;
	xWaterValve_SQL   :BOOL;
			{endregion}
END_STRUCT
END_TYPE