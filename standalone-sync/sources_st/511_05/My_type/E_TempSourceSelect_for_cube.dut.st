// @OBJECT_ID: baf4afdc-781e-4ae9-b24d-912255e74765
// @DECLARATION
TYPE E_TempSourceSelect_for_cube :
(
   AI_T2_Temp_Cube := 0,  // Температура в кубе
    AI_T3_Temp_Packing := 1,  // T3: Температура в нижней части насадки
    AI_T4_Temp_BotCol := 2   // [Канал 1] T4: Температура низа колонны
) INT;
END_TYPE