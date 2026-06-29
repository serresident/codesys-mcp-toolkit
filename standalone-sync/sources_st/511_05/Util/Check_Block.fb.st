// @OBJECT_ID: a53145cf-05f5-44e2-98c8-5640a1ec8c65
// @DECLARATION
FUNCTION_BLOCK Check_Block
VAR_INPUT
	State_Mixer : BOOL;
	Weight : REAL;
END_VAR
VAR_OUTPUT
	State_Block : BOOL;
	State_Block_P102 : BOOL; 
END_VAR
VAR
END_VAR








// @IMPLEMENTATION
IF NOT State_Mixer THEN
	State_Block := TRUE;
ELSE
	State_Block := FALSE;
END_IF;
IF Weight > 3000 THEN
	State_Block_P102 := TRUE;
ELSE 
	State_Block_P102 := FALSE;
END_IF;