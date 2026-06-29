// @OBJECT_ID: 38106bf3-2e28-4407-a341-929dcc35d1f5
// @DECLARATION
// шаг состояния клиента
{attribute 'strict'}
TYPE CLIENT_STATE :
(
	CREATE	:=	 0,
	WAITING	:=	10,
	SEND	:=	20,
	RECEIVE :=  30
);
END_TYPE