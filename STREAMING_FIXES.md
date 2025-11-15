# Correcciones de Streaming Backend

## Problemas Corregidos

### 1. ❌ Error: "Object of type SessionStateSchema is not JSON serializable"

**Causa**: El objeto `SessionStateSchema` (Pydantic model) no se puede serializar directamente a JSON en los eventos SSE.

**Solución**: 
- Convertir el schema a dict antes de serializarlo: `session_obj.dict()`
- Reconstruir el schema desde el dict antes de guardarlo en la DB

**Archivos modificados**:
- `app/api/v1/endpoints/ai_chat.py` líneas 207-214 y 223-232

```python
# Antes
event_data = json.dumps(event, ensure_ascii=False)

# Después
if event["type"] == "complete" and "session" in event["data"]:
    session_obj = event["data"]["session"]
    if hasattr(session_obj, 'dict'):
        event["data"]["session"] = session_obj.dict()
        
event_data = json.dumps(event, ensure_ascii=False)
```

### 2. ❌ Error: "404 models/gemini-1.5-flash is not found for API version v1beta"

**Causa**: El modelo `gemini-1.5-flash` no existe o no está disponible en la API de Google.

**Solución**: Actualizar todas las referencias a `gemini-2.0-flash-exp` que es el modelo correcto.

**Archivos modificados**:
- `app/services/ai_service.py` - 8 instancias actualizadas:
  1. Docstring (línea 6)
  2. Modelo por defecto (línea 45)
  3. Función `guardrail_check` (línea 147)
  4. Función `extract_slots_with_llm` (línea 289)
  5. Función `handle_user_turn` (línea 602)
  6. Función `handle_user_turn_streaming` (línea 821)
  7. Función `generate_chat_response` (línea 932)
  8. Función `generate_profile_summary` (línea 957)

```python
# Antes
model = genai.GenerativeModel('gemini-1.5-flash')

# Después
model = genai.GenerativeModel('gemini-2.0-flash-exp')
```

### 3. ⚠️ Warning: "Error en extracción LLM, usando heurística"

**Causa**: El modelo incorrecto causaba que las extracciones LLM fallaran.

**Resultado**: Con el modelo correcto (`gemini-2.0-flash-exp`), las extracciones deberían funcionar correctamente ahora.

---

## Archivos Modificados

1. **app/services/ai_service.py**
   - ✅ 8 referencias actualizadas de `gemini-1.5-flash` → `gemini-2.0-flash-exp`
   - ✅ Todas las funciones usan el modelo correcto

2. **app/api/v1/endpoints/ai_chat.py**
   - ✅ Serialización correcta de SessionStateSchema a dict
   - ✅ Reconstrucción del schema para guardado en DB

---

## Testing

### Verificación Manual

```bash
# 1. Verificar que no quedan referencias al modelo antiguo
grep -r "gemini-1.5-flash" app/

# 2. Probar el endpoint de streaming
curl -X POST http://localhost:8000/api/v1/ai-chat/send-stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola Flou, necesito ayuda con mi ensayo"}' \
  --no-buffer
```

### Resultados Esperados

✅ Sin errores de modelo no encontrado  
✅ Sin errores de serialización JSON  
✅ Streaming funciona correctamente  
✅ Sesión se guarda correctamente en la DB  
✅ Mensajes se guardan correctamente  

---

## Logs Esperados (después de la corrección)

```
INFO: streaming_request_start
INFO: crisis_check_negative
INFO: slots_extracted (sin warnings)
INFO: strategy_generated
INFO: chunk enviado
INFO: chunk enviado
...
INFO: complete enviado
INFO: sesión guardada correctamente
```

**Sin errores de**:
- ❌ "404 models/gemini-1.5-flash is not found"
- ❌ "Object of type SessionStateSchema is not JSON serializable"
- ⚠️ "Error en extracción LLM, usando heurística"

---

## Impacto en el Frontend

El frontend ahora debería recibir los eventos correctamente sin el error "Response body is null".

Los eventos SSE llegarán en el formato correcto:
```
data: {"type":"metadata","data":{...}}
data: {"type":"chunk","data":{"text":"Hola"}}
data: {"type":"chunk","data":{"text":" ¿cómo"}}
data: {"type":"complete","data":{"session":{...},"quick_replies":[...]}}
```

---

## Próximos Pasos

1. ✅ Hacer commit de los cambios
2. ✅ Deploy a Azure
3. 🧪 Probar en la app móvil
4. 📊 Monitorear logs para verificar que no hay más errores
