from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import asyncio
import threading

datos = []  # Almacena los signos vitales en memoria
app = FastAPI()

@app.get("/")
def home():
    return {"message": "Monitor de Signos Vitales en tiempo real con concurrencia está funcionando"}

@app.get("/historial")
def obtener_historial():
    return {"historial": datos}

# WebSocket para recibir datos del sensor de forma concurrente
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado")

    try:
        while True:
            # Recibir datos del sensor
            data = await websocket.receive_text()
            dato = json.loads(data)

            # Analizar signos vitales concurrentemente
            loop = asyncio.get_event_loop()
            alerta = await loop.run_in_executor(None, detectar_alerta, dato)
            
            dato["estado"] = "alerta" if alerta else "normal"
            datos.append(dato)
            print(f"Recibido: {dato}")

            # Enviar respuesta al cliente
            await websocket.send_text(json.dumps(dato))
    except WebSocketDisconnect:
        print("Cliente desconectado")

# Función concurrente para detección de alertas
def detectar_alerta(dato):
    temp_normal = (36.0, 37.5)
    ritmo_normal = (60, 100)
    presion_normal = (90, 140, 60, 90)  # (Sistólica min, Sistólica max, Diastólica min, Diastólica max)
    
    sistolica, diastolica = map(int, dato["tension_arterial"].split("/"))
    
    if not (temp_normal[0] <= dato["temperatura"] <= temp_normal[1]):
        return True
    if not (ritmo_normal[0] <= dato["ritmo_cardiaco"] <= ritmo_normal[1]):
        return True
    if not (presion_normal[0] <= sistolica <= presion_normal[1] and presion_normal[2] <= diastolica <= presion_normal[3]):
        return True
    
    return False

# Algoritmo recursivo: Factorial (puede ser usado para cálculos de umbrales dinámicos)
def calcular_factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * calcular_factorial(n - 1)

# Hilo para la verificación de alertas en segundo plano
def verificar_alertas():
    while True:
        alertas = [d for d in datos if d["estado"] == "alerta"]
        if alertas:
            print("⚠️ ALERTA: Se detectaron valores anormales:")
            for alerta in alertas:
                print(f"   - Ritmo Cardíaco: {alerta['ritmo_cardiaco']} bpm")
                print(f"   - Temperatura: {alerta['temperatura']}°C")
                print(f"   - Tensión Arterial: {alerta['tension_arterial']}")
                print("-------------------------------------------------")
        
        asyncio.run(asyncio.sleep(5))  # Verifica cada 5 segundos

# Ejecutar la verificación en un hilo aparte
thread = threading.Thread(target=verificar_alertas, daemon=True)
thread.start()
