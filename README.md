# 🤖 Taniia Bot - Agente Virtual de Turismo Inteligente

Bot conversacional inteligente impulsado por GPT-4 que funciona como asistente virtual de turismo para WhatsApp. Taniia Bot proporciona información turística personalizada, recomendaciones de lugares y gestión de consultas en múltiples idiomas.

## 📋 Descripción

Taniia Bot es un agente conversacional basado en IA diseñado específicamente para el sector turístico de Chiquinquirá, Colombia pero expandible a todas las regiones. Utiliza GPT-4 de OpenAI para procesar lenguaje natural y Elasticsearch para búsquedas semánticas, ofreciendo respuestas contextuales e inteligentes sobre hoteles, restaurantes, sitios turísticos y más.

### ✨ Características Principales

- 🌐 **Multiidioma**: Soporta Español, Inglés y Francés
- 🧠 **IA Conversacional**: Procesamiento de lenguaje natural con GPT-4o-mini
- 🎤 **Transcripción de Audio**: Convierte mensajes de voz a texto con Whisper
- 📍 **Búsqueda Geoespacial**: Encuentra lugares cercanos por geolocalización
- 🔍 **Búsquedas Inteligentes**: Fuzzy search y búsquedas semánticas con Elasticsearch
- 💬 **Context-Aware**: Mantiene historial de conversaciones para respuestas contextuales
- 🏨 **Información Detallada**: Datos completos de establecimientos turísticos (RNT)
- 📱 **WhatsApp Business API**: Integración nativa con Meta WhatsApp

## 🏗️ Arquitectura del Sistema

```
TaniiaBotDatosAbiertos/
│
├── main.py                      # Aplicación FastAPI principal
├── run.py                       # Script de ejecución con SSL
├── requirements.txt             # Dependencias del proyecto
│
├── app/
│   ├── config/
│   │   └── config.py           # Configuración y variables de entorno
│   │
│   ├── controllers/
│   │   └── webhook_controller.py   # Controlador de webhooks de WhatsApp
│   │
│   ├── routes/
│   │   └── webhook_routes.py   # Definición de rutas FastAPI
│   │
│   ├── services/
│   │   ├── message_handler.py      # Orquestador principal de mensajes
│   │   ├── openai_service.py       # Servicio de integración con OpenAI
│   │   ├── whatsapp_service.py     # Servicio de mensajería WhatsApp
│   │   ├── elasticsearch_service.py # Servicio de búsquedas
│   │   └── http_request/
│   │       └── send_to_whatsapp.py # Envío de mensajes HTTP
│   │
│   └── static/
│       └── index.html          # Página de inicio clientes
│
└── ssl/                         # Certificados SSL (producción)
```

## 🔄 Flujo de Procesamiento de Mensajes

```
┌─────────────────┐
│  Usuario envía  │
│  mensaje/audio  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│   Webhook Controller    │
│  (webhook_controller)   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Message Handler       │
│  (message_handler.py)   │
│  - Clasifica tipo       │
│  - Gestiona estados     │
│  - Coordina servicios   │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ OpenAI  │ │Elasticsearch │
│ Service │ │   Service    │
│ - GPT-4 │ │ - Búsquedas  │
│ -Whisper│ │ - Historial  │
└────┬────┘ └──────┬───────┘
     │             │
     └──────┬──────┘
            ▼
   ┌─────────────────┐
   │WhatsApp Service │
   │ - Envía resp.   │
   │ - Marca leído   │
   └─────────────────┘
```

## 🧠 Sistema de Inteligencia Artificial

### GPT Function Calling

Taniia Bot utiliza **Function Calling** de OpenAI para clasificar intenciones y ejecutar acciones específicas:

#### Funciones Disponibles:

1. **`buscar_lugar_turistico`**
   - Busca hoteles, restaurantes, glamping, etc.
   - Clasifica búsquedas en: `BUSQUEDA_GENERAL`, `NOMBRE_EXACTO_O_PARCIAL`, `FILTROS_SEMANTICOS`
   - Categorías: HOTEL, RESTAURANTE, GLAMPING, AGENCIA_VIAJES, etc.

2. **`obtener_geolocalizacion`**
   - Solicita ubicación o coordenadas exactas
   - Genera mapas y rutas

3. **`cambiar_idioma_respuesta`**
   - Detecta cambios de idioma (Español/Inglés/Francés)
   - Adapta respuestas al idioma seleccionado

4. **`manejar_conversacion_simple`**
   - Gestiona: saludos, despedidas, agradecimientos, emergencias
   - Respuestas contextuales sin búsquedas

### Búsquedas con Elasticsearch

#### 1. Búsqueda Aleatoria por Categoría
```python
# Busca 5 lugares aleatorios de una categoría
await get_random_places("HOTEL", timeout=5)
```

#### 2. Búsqueda Fuzzy por Nombre
```python
# Búsqueda tolerante a errores con n-gramas
await search_place_by_name_with_timeout("Gran Central", timeout=5)
```

#### 3. Búsqueda Geoespacial
```python
# Encuentra lugares cercanos (radio de 5km)
await get_place_near(latitud=5.615, longitud=-73.817, radio_km=5)
```

#### 4. Búsqueda por RNT (Registro Nacional de Turismo)
```python
# Obtiene detalles exactos por código RNT
await get_place_byrnt("12345", timeout=5)
```

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.9+
- Cuenta de WhatsApp Business API
- API Key de OpenAI
- Elasticsearch/OpenSearch configurado
- Certificados SSL (para producción)

### Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/luismiguelmoncada/TaniiaBotDatosAbiertos.git
cd TaniiaBotDatosAbiertos
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

Crear archivo `.env` en la raíz del proyecto:

```env
# WhatsApp Configuration
WEBHOOK_VERIFY_TOKEN=tu_token_de_verificacion
API_TOKEN=tu_token_de_whatsapp_api
BUSINESS_PHONE=numero_telefono_business
API_VERSION=v19.0

# OpenAI Configuration
OPENAI_API_KEY=tu_api_key_de_openai

# Elasticsearch Configuration
ELASTICSEARCH_URL=https://tu-elasticsearch-url
ELASTICSEARCH_API_KEYU=tu_usuario_api_key
ELASTICSEARCH_API_KEYP=tu_password_api_key

# Server Configuration
PORT=3000
BASE_URL=https://tu-dominio.com

# SSL Configuration (Producción)
SSL_KEYFILE=/app/privkey.pem
SSL_CERTFILE=/app/fullchain.pem
```

### Ejecución

#### Desarrollo Local (sin SSL)
```bash
python run.py
```

#### Producción (con SSL)
```bash
python run.py
```

#### Docker
```bash
docker build -t taniia-bot .
docker run -p 3000:3000 taniia-bot
```

## 📡 API Endpoints

### Webhook de WhatsApp

#### POST `/webhook`
Recibe mensajes entrantes de WhatsApp
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": []
      }
    }]
  }]
}
```

#### GET `/webhook`
Verifica el webhook con Meta
```
GET /webhook?hub.mode=subscribe&hub.verify_token=TU_TOKEN&hub.challenge=CHALLENGE
```

### Página Principal

#### GET `/`
Retorna la página de inicio (`index.html`)

## 💬 Tipos de Mensajes Soportados

| Tipo | Descripción | Acción |
|------|-------------|--------|
| `text` | Mensajes de texto | Procesamiento con GPT |
| `audio` | Mensajes de voz | Transcripción con Whisper → GPT |
| `image` | Imágenes | Mensaje de no soportado |
| `location` | Ubicación compartida | Búsqueda geoespacial |
| `interactive` | Botones/respuestas | Ejecución de opciones |

## 🎯 Casos de Uso

### Ejemplo 1: Búsqueda de Hoteles
```
Usuario: "Quiero un hotel en Chiquinquirá"
Taniia: [Busca en BD] → Muestra 3 hoteles con botones
Usuario: [Selecciona hotel]
Taniia: Envía imagen, mapa, PDF con detalles
```

### Ejemplo 2: Búsqueda por Ubicación
```
Usuario: [Comparte ubicación GPS]
Taniia: "Voy a buscar lugares cercanos a tu ubicación"
       → Busca en radio de 5km
       → Muestra 3 lugares más cercanos
```

### Ejemplo 3: Búsqueda por Voz
```
Usuario: [Envía audio "Restaurantes con parqueadero"]
Taniia: [Transcribe con Whisper]
       → "Voy a consultar restaurantes..."
       → [Busca en BD]
       → Muestra resultados
```

## 🔧 Tecnologías Utilizadas

| Tecnología | Propósito |
|------------|-----------|
| **FastAPI** | Framework web asíncrono |
| **OpenAI GPT-4o-mini** | Procesamiento de lenguaje natural |
| **Whisper** | Transcripción de audio |
| **Elasticsearch/OpenSearch** | Motor de búsquedas y almacenamiento |
| **WhatsApp Business API** | Canal de comunicación |
| **Uvicorn** | Servidor ASGI |
| **Python Asyncio** | Programación asíncrona |

## 🔐 Seguridad

- ✅ SSL/TLS en producción
- ✅ Verificación de tokens de webhook
- ✅ Variables de entorno para secretos
- ✅ Timeout en consultas a servicios externos
- ✅ Validación de entrada de usuarios

## 📈 Mejoras Futuras

- [ ] Búsquedas RAG (Retrieval Augmented Generation) avanzadas
- [ ] Soporte para más tipos de medios (video, documentos)
- [ ] Sistema de reservas y ventas integrado
- [ ] Dashboard de analytics
- [ ] Integración con más plataformas (Telegram, Instagram)
- [ ] Multilingual embeddings para búsquedas semánticas

## 👨‍💻 Autor

**Luis Miguel Moncada Ocampo - Ingeniero de Sistemas, Magister en Ingenieria de Software**
- GitHub: [@luismiguelmoncada](https://github.com/luismiguelmoncada/TaniiaBotDatosAbiertos.git)
- Proyecto: TaniiaBotDatosAbiertos por Zenzuite, una suite de soluciones.
- Url Clientes: https://www.zenzuite.com/taniia

## 📄 Contacto

luis05247@gmail.com.

---

**Taniia Bot** - Turismo Inteligente con IA 🤖✨
