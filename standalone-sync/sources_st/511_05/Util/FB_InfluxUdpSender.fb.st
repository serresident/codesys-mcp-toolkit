// @OBJECT_ID: e559a9a1-9e90-4a38-bf45-4143c502a1fc
// @DECLARATION
FUNCTION_BLOCK FB_InfluxUdpSender
VAR_INPUT
	sSendData : STRING(2000); // Data to send
    sIPInflux : STRING :='192.168.215.5'; // InfluxIP
    uiPortInflux : UINT := 8089; // Influx port
END_VAR
VAR
	eState: 			CLIENT_STATE;								// Шаг состояния клиента
	
	fbUdpPeer: 			NBS.UDP_Peer;								// ФБ создания UDP-пира
	fbUdpSend: 			NBS.UDP_Send;								// ФБ отправки данных
	sendData : STRING(2000); // Data to send
    numberOfBytesToSend : UDINT := 0; // Number of bytes to send
	influxIP: NBS.IP_ADDR;

	fbSendTrig:			R_TRIG;										// Триггер записи
	
	blinker:BLINK;
	TimeCycle: TIME:= T#10S;
	bStart : BOOL := FALSE;
END_VAR










// @IMPLEMENTATION
	blinker(ENABLE:=bStart,timelow:=TimeCycle, timehigh:=T#1S);
	
CASE eState OF	

	CLIENT_STATE.CREATE:	// создаем UDP-пира на заданном порту
		
		fbUdpPeer
		(
			xEnable		:= TRUE, 
			ipAddr		:= , 
			uiPort		:= ,
			ipMultiCast	:= ,  
		);
	
		IF fbUdpPeer.xActive THEN
			bStart := TRUE;
			eState	:= CLIENT_STATE.WAITING;
			influxIP.sAddr:=sIPInflux;
		ELSIF fbUdpPeer.xError THEN
			; // обработка ошибок
		END_IF

	CLIENT_STATE.WAITING:	// ожидаем команды на запись
	
		fbSendTrig(CLK:=blinker.OUT);
		
		IF fbSendTrig.Q THEN
// Calculate number of bytes to send
			sendData := sSendData;
			numberOfBytesToSend := DINT_TO_UDINT(Stu.StrLenA(ADR(sendData)));			
			
			eState	:= CLIENT_STATE.SEND;
		END_IF
	
	CLIENT_STATE.SEND:		// отправляем запрос серверу
		
			fbUdpSend
			(
				xExecute	:=	TRUE,
				udiTimeOut:= 1000, 
				hPeer		:=	fbUdpPeer.hPeer, 
				ipAddr:=  influxIP, 
				uiPort:= uiPortInflux, 
				szSize:= numberOfBytesToSend, 
				pData:= ADR(sendData), 
			);
			
			IF (fbUdpSend.xDone OR fbUdpSend.xError) THEN
				fbUdpSend(xExecute:=FALSE);
				eState	:= 	CLIENT_STATE.WAITING;
			END_IF
	
END_CASE