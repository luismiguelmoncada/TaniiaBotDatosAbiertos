from email.mime import message
import json
from app.services.whatsapp_service import whatsapp_service 
from app.services.openai_service import openai_service,transcribe_audio
from app.services.elasticsearch_service import get_random_places, index_conversation, search_place_by_name_with_timeout,get_place_byrnt,get_place_near

MAPEO_CATEGORIAS_GPT_A_ES = {
            # Tipos de Alojamiento
            "HOTEL": "HOTEL",
            "HOSTAL": "HOSTAL",
            "APARTAMENTO_TURISTICO": "APARTAMENTO TURÍSTICO",
            "FINCA_TURISTICA": "FINCA TURISTICA (ALOJAMIENTO RURAL)",
            "APARTAHOTEL": "APARTAHOTEL",
            "CASA_TURISTICA": "CASA TURÍSTICA",
            "GLAMPING": "GLAMPING",
            
            # Agencias y Operadores
            "AGENCIA_VIAJES": "AGENCIAS DE VIAJES Y DE TURISMO", # Unifica los 3 tipos de agencias
            "OPERADOR_EVENTOS": "OPERADOR PROFESIONAL DE CONGRESOS FERIAS Y CONVENCIONES",
            "GUIA_TURISMO": "GUIA DE TURISMO",
            
            # Otros Servicios
            "RESTAURANTE": "RESTAURANTE",
            "TRANSPORTE_ESPECIAL": "TRANSPORTE TERRESTRE AUTOMOTOR ESPECIAL",
            "ARRENDADOR_VEHICULOS": "ARRENDADOR DE VEHICULOS PARA TURISMO NACIONAL E INTERNACIONAL",
            
            # Categorías Varias / Residuales (Unificadas)
            "CONCESIONARIO_PARQUE": "CONCESIONARIO DE SERVICIOS TURÍSTICOS EN PARQUE", # Unifica las dos variantes de CONCESIONARIO
            "OTROS_HOSPEDAJE": "OTROS TIPOS DE HOSPEDAJE TURÍSTICOS NO PERMANENTES",
            "VIVIENDA_TURISTICA": "OTRO TIPO DE VIVIENDA TURÍSTICA"
        }

class MessageHandler:
    def __init__(self):
        self.appointment_state = {}
        self.assistant_state = {}

        self.booking_state = {}
        self.info_state = {}
        self.faq_state = {}
        self.feedback_state = {}
        self.transport_state = {}
        self.recommendation_state = {}
        self.event_state = {}
        self.menu_state = {}

        self.output_language_state = {}
        self.places_select = {}


    async def handle_incoming_message(self, message, sender_info):

        print("Appointment state:", self.appointment_state)
        print("Assistant state:", self.assistant_state)
         
        if message.get("type") == "text":
            incoming_message = message.get("text", {}).get("body", "").lower().strip()

            if self.is_greeting(incoming_message):
                await self.send_welcome_menu(message["from"],sender_info) 
            else:
                await self.handle_menu_option(message["from"], incoming_message,incoming_message,sender_info)
            await whatsapp_service.mark_as_read(message["id"])


        elif message.get("type") == "interactive":
            option = (
                message.get("interactive", {}).get("button_reply", {}).get("id")
            )
            await self.handle_menu_option(message["from"], option,None,sender_info)
            await whatsapp_service.mark_as_read(message["id"])

        elif message.get("type") == "image":
            messages = {
                    "Spanish": "Actualmente no puedo procesar imágenes. Por favor, envíame un mensaje de texto o un audio. 😊",
                    "English": "Currently, I cannot process images. Please send me a text message or audio. 😊",
                    "French": "Actuellement, je ne peux pas traiter les images. Veuillez m'envoyer un message texte ou un audio. 😊"
                }
            user_language = self.output_language_state.get(message["from"], "Spanish") # "Spanish" por defecto
            message_to_send = messages.get(user_language, messages["Spanish"])   
            await whatsapp_service.send_message(message["from"], message_to_send) 
            await whatsapp_service.mark_as_read(message["id"])

        elif message.get("type") == "location":
            messages = {
                    "Spanish": "Vamos a buscar lugares cercanos a tu ubicación. 😊",
                    "English": "Let's look for places near your location. 😊",
                    "French": "Recherchons des lieux près de votre position. 😊"
                }
            user_language = self.output_language_state.get(message["from"], "Spanish") # "Spanish" por defecto
            message_to_send = messages.get(user_language, messages["Spanish"])   
            await whatsapp_service.send_message(message["from"], message_to_send) 
            await whatsapp_service.mark_as_read(message["id"])

            #BUSCA LUGARE CERCANOS POR GEOREFRENCIACION EN eLASTICSEARCH

            latitud = message.get('location', {}).get('latitude')
            longitud = message.get('location', {}).get('longitude')

            response_elasticSearch = await get_place_near(latitud, longitud, radio_km=5, sub_categoria=None, timeout=5)
            print("Lugares CERCANOS:", response_elasticSearch)
            await self.pintar_lugares_botones(message["from"], response_elasticSearch, user_language)

        elif message.get("type") == "audio":
            media_id = message.get("audio", {}).get("id")
            audio_content = await whatsapp_service.load_whatsapp_audio(message_id=media_id)  
        
            if audio_content: # Esto es True si se descargó bien
                print(f"Audio descargado, tamaño en bytes: {len(audio_content)}") # Esto está bien si hay contenido
                transcripcion = await transcribe_audio(audio_content)
                print("Transcripción del audio:", transcripcion)

                if transcripcion:
                    await self.handle_menu_option(message["from"], transcripcion, transcripcion, sender_info)
                # ... el resto del código para transcribir
            else:
                print("No se pudo descargar el audio") # Esto se ejecuta si audio_content es None
                await whatsapp_service.send_message(message["from"], "Lo siento, no pude descargar el audio que enviaste. Intenta escribir tu mensaje o enviarlo de nuevo.")


    def is_greeting(self, msg):
        greetings = ["hola", "hello", "hi", "buenas tardes"] #lo que no esta aca bringa al agente GPT y si es relacionaado con saludo lo clasifica
        return msg in greetings

    def get_sender_name(self, sender_info):
        return (
            sender_info.get("profile", {}).get("name")
            or sender_info.get("wa_id")
        )

    async def send_welcome_menu(self, to,sender_info):
        name = self.get_sender_name(sender_info)
        user_language = self.output_language_state.get(to, "Spanish") # "Spanish" por defecto
        
        messages = {
                            "Spanish": f"Hola {name}, Soy Tannia. Tu agente virtual de turismo impulsado por inteligencia artificial. 😊",
                            "English":  f"Hello {name}, I'm Tannia. Your AI-powered virtual tourism agent. 😊",
                            "French":  f"Bonjour {name}, Je suis Tannia. Votre agent virtuel de tourisme propulsé par l'intelligence artificielle. 😊"
                    }
        message_to_send = messages.get(user_language, messages["Spanish"]) 
                    
        media_url = "https://thoht.com.co/uploads/perfil/fotoPerfil/tannia.png" 
        media_type = "image"
        await whatsapp_service.send_media_message(to, media_type, media_url, message_to_send) 
         

        user_language = self.output_language_state.get(to, "Spanish") # "Spanish" por defecto
        messages = {
                    "Spanish": "¿Como te puedo ayudar? Puedes elegir una Opción",
                    "English": "How can I help you? You can choose an Option",
                    "French": "Comment puis-je vous aider? Vous pouvez choisir une option"
                }
        message_to_send = messages.get(user_language, messages["Spanish"])  

        messages1 = {
                        "Spanish": "Sitios Turísticos"  ,
                        "English": "Tourist Sites",
                        "French": "Sites touristiques"
                    }
        message_to_send1 = messages1.get(user_language, messages1["Spanish"]) 

        messages2 = {
                        "Spanish": "Restaurantes"  ,
                        "English": "Restaurants",
                        "French": "Restaurants"
                    }
        message_to_send2 = messages2.get(user_language, messages2["Spanish"]) 

        messages3 = {
                        "Spanish": "Hoteles"  ,
                        "English": "Hotels",
                        "French": "Hôtels"
                    }
        message_to_send3 = messages3.get(user_language, messages3["Spanish"])  
        
        buttons = [
                    {"type": "reply", "reply": {"id": "option_cg1", "title": message_to_send1}},
                    {"type": "reply", "reply": {"id": "option_cg2", "title": message_to_send2}},
                    {"type": "reply", "reply": {"id": "option_cg3", "title": message_to_send3}},
                ]
        
        await whatsapp_service.send_interactive_buttons(to, message_to_send, buttons)

    async def handle_menu_option(self, to, option,incoming_message,sender_info):
        print("incoming_message:", incoming_message)
        user_language = self.output_language_state.get(to, "Spanish") # "Spanish" por defecto
        response = None

        if option == "option_il1":
            self.output_language_state[to] = "Spanish"
            response = "Has seleccionado Español como idioma de respuesta." 
        elif option == "option_il3":
            self.output_language_state[to] = "French"
            response = "Vous avez sélectionné le français comme langue de réponse." 
        elif option == "option_il2":
            self.output_language_state[to] = "English"
            response = "You have selected English as your response language." 

        elif option == "option_cg1":
            self.places_select[to] = "GLAMPING" 
            messages = {
                        "Spanish": "Estoy buscando los sitios mas populares de la región."  ,
                        "English": "I am looking for the most popular sites in the region.",
                        "French": "Je recherche les sites les plus populaires de la région."
                    }
            message_to_send = messages.get(user_language, messages["Spanish"])  
            response = ""  
            await whatsapp_service.send_message(to, message_to_send )
            await self.consultar_bd_categoria(to, "GLAMPING", user_language)
        elif option == "option_cg2":
            self.places_select[to] = "RESTAURANTE" 
            messages = {
                        "Spanish": "Voy a consultar en mi base de datos los restaurantes con mejor calificación."  ,
                        "English": "I will check my database for the highest rated restaurants.",
                        "French": "Je vais consulter ma base de données pour les restaurants les mieux notés."
                    }
            message_to_send = messages.get(user_language, messages["Spanish"])  
            response = "" 
            await whatsapp_service.send_message(to, message_to_send )
            await self.consultar_bd_categoria(to, "RESTAURANTE", user_language)
        elif option == "option_cg3":
            self.places_select[to] = "HOTEL"
            messages = {
                        "Spanish": "Estoy buscando los mejores hoteles para ti."  ,
                        "English": "I will check my database for the highest rated hotels.",
                        "French": "Je vais consulter ma base de données pour les hôtels les mieux notés."
                    }
            message_to_send = messages.get(user_language, messages["Spanish"])  
            response = "" 
            await whatsapp_service.send_message(to, message_to_send )
            await self.consultar_bd_categoria(to, "HOTEL", user_language)
        
        elif option.startswith("rntBuscarLugar_"):
            try: 
                parts = option.split("_")
                 
                codigo_rnt = parts[-1]
                 
                if codigo_rnt and codigo_rnt.isdigit():
                    
                    messages = {
                                "Spanish": f"Pronto tendremos información detallada de este lugar: {codigo_rnt} ",
                                "English": f"Soon we will have detailed information about this place: {codigo_rnt} ",
                                "French": f"Bientôt, nous aurons des informations détaillées sur cet endroit : {codigo_rnt} "
                        }
                    
                    messages2 = {
                            "Spanish": f"Aqui tienes información del lugar, si necesitas algo más, no dudes en preguntarme. " ,
                            "English": f"Here is some information about the place, if you need anything else, feel free to ask me. ",
                            "French": "Voici quelques informations sur le lieu, si vous avez besoin de quelque chose d'autre, n'hésitez pas à me le demander. "
                    }
                    
                  
                    response_elasticSearch = await get_place_byrnt(codigo_rnt, timeout=5)
                    print("Lugares EXACTO POR RNT:", response_elasticSearch)

                    if response_elasticSearch and len(response_elasticSearch) > 0:
                        hotel_data_source = response_elasticSearch[0].get('_source') # Usamos .get() para evitar KeyError si '_source' no existe
                        
                        if hotel_data_source: 
                            # Usamos .get() para extraer cada valor. Esto devolverá 'None'
                            # si la clave no existe, en lugar de lanzar un error.
                            imagen_url = hotel_data_source.get('IMAGEN')
                            pdf_url = hotel_data_source.get('PDF')
                            latitud = hotel_data_source.get('LATITUD')
                            longitud = hotel_data_source.get('LONGITUD')
                            horario = hotel_data_source.get('HORARIO')
                            nombre = hotel_data_source.get('RAZON_SOCIAL_ESTABLECIMIENTO')
                            direccion = hotel_data_source.get('DIRECCION')
                            telefono = hotel_data_source.get('TELEFONO')

                            ubicacion = hotel_data_source.get('UBICACION') 
                            latitud = None
                            longitud = None

                            if isinstance(ubicacion, dict):
                                latitud = ubicacion.get('lat')
                                longitud = ubicacion.get('lon')
                                latitude = float(latitud)
                                longitude = float(longitud)
                                name = nombre or "Ubicación del lugar"
                                address = direccion or "Dirección no disponible"
                                await whatsapp_service.send_location_message(to, latitude, longitude, name, address)

                            if imagen_url:
                                media_type = "image"
                                await whatsapp_service.send_media_message(to, media_type, imagen_url, f"{nombre}\n{direccion}\nHorario: {horario} \nTel: {telefono}") 

                            if pdf_url:
                                media_type = "document"
                                await whatsapp_service.send_media_message(to, media_type, pdf_url, f"Revisa esta información adicional") 
                             
                            else:
                                message_to_send = messages.get(user_language, messages["Spanish"])  
                                await whatsapp_service.send_message(to, message_to_send )
                        
                        else: 
                            message_to_send = messages.get(user_language, messages["Spanish"])  
                            await whatsapp_service.send_message(to, message_to_send ) 
                    else:
                         message_to_send = messages.get(user_language, messages["Spanish"])  
                         await whatsapp_service.send_message(to, message_to_send ) 
                    
                else:
                    print("ERROR: El contenido después del prefijo 'rntBuscarLugar_' no es un código válido.")
                    
            except Exception as e:
                print(f"Error al procesar el ID de botón: {e}")
            
        else: 
            name = self.get_sender_name(sender_info) 
            prompt_usuario =  incoming_message 
            response = await openai_service(prompt_usuario,to,user_language,None)

            print("Respuesta del asistente JSON FINAL:", response)

            if to in self.assistant_state:
                del self.assistant_state[to]


        if response:
            function_name = ""
            print("response Mensaje a enviar:", response) 
            
            try:
                function_name = (json.loads(response).get("function_name") or "") if response else "" 
            except Exception:
                function_name = ""  

            if function_name:
                print("Function name detected:", function_name)
            else:
                await whatsapp_service.send_message(to, response)


            if function_name == "saludo":
                await self.send_welcome_menu(to,sender_info)

            if function_name == "ubicacion":
                await whatsapp_service.send_message(to, 'Buscando ubicación...')

            if function_name == "otra":
                menu_message = "No entendi bien lo que buscas. ¿Qué quieres consultar?"
                buttons = [
                    {"type": "reply", "reply": {"id": "option_cg1", "title": "Sitios Turísticos"}},
                    {"type": "reply", "reply": {"id": "option_cg2", "title": "Restaurantes"}},
                    {"type": "reply", "reply": {"id": "option_cg3", "title": "Hoteles"}},
                ]
                await whatsapp_service.send_interactive_buttons(to, menu_message, buttons)

            if function_name == "cambiar_idioma_respuesta":

                response_dict = json.loads(response)  ##si tannia identifica el idioma lo cambia sino pregunta
                idioma = response_dict.get('idioma_solicitado') or ""
                if "español" in idioma.lower():
                    self.output_language_state[to] = "Spanish"
                    response1 = "Has seleccionado Español como idioma de respuesta." 
                    await whatsapp_service.send_message(to,  response1)
                elif "inglés" in idioma.lower() or "ingles" in idioma.lower():
                    self.output_language_state[to] = "English"
                    response2 = "You have selected English as your response language." 
                    await whatsapp_service.send_message(to,  response2)
                elif "francés" in idioma.lower() or "frances" in idioma.lower():
                    self.output_language_state[to] = "French"
                    response3 = "Vous avez sélectionné le français comme langue de réponse." 
                    await whatsapp_service.send_message(to,  response3) 
                else: 
                    messages = {
                                "Spanish": "¿Qué idioma de respuesta prefieres?",
                                "English": "What response language do you prefer?",
                                "French": "Quelle langue de réponse préférez-vous?"
                            }
                    message_to_send = messages.get(user_language, messages["Spanish"])
                    
                    buttons = [
                        {"type": "reply", "reply": {"id": "option_il1", "title": "Español"}},
                        {"type": "reply", "reply": {"id": "option_il2", "title": "Inglés"}},
                        {"type": "reply", "reply": {"id": "option_il3", "title": "Francés"}},
                    ]
                    await whatsapp_service.send_interactive_buttons(to, message_to_send, buttons)

            if function_name == "manejar_conversacion_simple":

                response_dict = json.loads(response)  
                print("response_dict FINAL ARGUMENTS:", response_dict)
                intencion_simple = response_dict.get("intencion_simple") or ""

                if intencion_simple == "saludo":  
                    await self.send_welcome_menu(to,sender_info)

                if intencion_simple == "despedida":
                    await whatsapp_service.send_message(to, f"Hasta pronto {self.get_sender_name(sender_info)}! Que tengas un excelente día.") 
                if intencion_simple == "agradecimiento":
                    await whatsapp_service.send_message(to, f"Es un gusto ayudarte {self.get_sender_name(sender_info)}! no dudes en contactarme nuevamente.") 
                if intencion_simple == "emergencia":
                    await whatsapp_service.send_message(to, f"No entres en pánico, Busca ayuda inmediatamente.") 
                    response = (
                        "Si esto es una emergencia, te invitamos a llamar a nuestra linea de atención."
                      )
                    await self.send_contact(to) 
                if intencion_simple == "otra":
                    menu_message = "¿Qué quieres consultar?"
                    tool_call_message_original = response_dict.get("tool_call_message_original") or ""

                    responseGpt = await openai_service(tool_call_message_original,to,user_language,response_dict) #response lleva los datos del tool call
                    print("Respuesta final con lo q GPT considere:", responseGpt)

                    await whatsapp_service.send_message(to, responseGpt)

            if function_name == "buscar_lugar_turistico":
               
                response_dict = json.loads(response)

                print("response_dict FINAL ARGUMENTS:", response_dict)
                tipo_entidad_gpt = response_dict.get("tipo_entidad") or "" 
                criterio_busqueda_gpt = response_dict.get("criterio_busqueda") or "" 
                tipo_busqueda_gpt = response_dict.get("tipo_busqueda") or "" 
                tipo_entidad_elastic = MAPEO_CATEGORIAS_GPT_A_ES.get(tipo_entidad_gpt, "")

                print("Tipo de entidad GPT detectada:", tipo_entidad_gpt)
                print("Respuesta del asistente JSON FINAL ARGUMENTS CON IDCALL:", response)

                if tipo_busqueda_gpt == "BUSQUEDA_GENERAL":   
                    print("Tipo de entidad mapeada para ElasticSearch:", tipo_entidad_elastic)
                    await self.consultar_bd_categoria_tool(to, tipo_entidad_elastic, user_language,response_dict,prompt_usuario)

                else:
                    if tipo_busqueda_gpt == "NOMBRE_EXACTO_O_PARCIAL": #buscamos en elastic
                        print("tipo_busqueda_gpt.",tipo_busqueda_gpt) 
                        await self.consultar_bd_nombre(to, criterio_busqueda_gpt, user_language) 

                    if tipo_busqueda_gpt == "FILTROS_SEMANTICOS": #Hacemos busqueda semantica RAG
                        print("tipo_busqueda_gpt.",tipo_busqueda_gpt)  
                        response_elasticSearch = await self.consultar_bd_nombre(to, criterio_busqueda_gpt, user_language) 

                        if not response_elasticSearch:
                            messages = {
                                    "Spanish": "Actualmente solo puedo buscar lugares por su nombre o tipo. Por favor, intenta de nuevo. 🧐",
                                    "English": "I can currently only search for places by name or type. Please try again. 🧐",
                                    "French": "Je ne peux actuellement chercher des lieux que par leur nom ou leur type. Veuillez réessayer. 🧐"
                            }
                            message_to_send = messages.get(user_language, messages["Spanish"])
                            await whatsapp_service.send_message(to, message_to_send)

                #llamo a gpt con el tool

            if function_name == "consultar_informacion_estatica":
               tool_call_message_original = response.get("tool_call_message_original") or ""
               responseGpt = await openai_service(tool_call_message_original,to,user_language,response_dict) #response lleva los datos del tool call
               print("Respuesta final con lo q GPT considere:", responseGpt)

               await whatsapp_service.send_message(to, responseGpt)

            if function_name == "obtener_geolocalizacion":
                messages = {
                            "Spanish": "Aun no puedo geolocalizar sitios exactos. Pero puedes compartirme tu ubicación actual para buscarte lugares cercanos.",
                            "English": "I can't yet geolocate exact sites. But you can share your current location with me to find nearby places.",
                            "French": "Je ne peux pas encore géolocaliser des sites exacts. Mais vous pouvez me partager votre position actuelle pour trouver des lieux à proximité."
                        }
                message_to_send = messages.get(user_language, messages["Spanish"])
                await whatsapp_service.send_message(to, message_to_send)

            name = self.get_sender_name(sender_info)
            index_conversation(to, f"Usuario {name} dice: {incoming_message}", function_name, response, self.get_sender_name(sender_info),  None,  [], None)#guardo la conversacion en ES
            
    async def consultar_bd_categoria_tool(self, to, tipo_entidad_elastic, user_language,response_dict,prompt_usuario):
        
        response_elasticSearch = await get_random_places(tipo_entidad_elastic, timeout=5)
        print("Lugares recomendados desde ElasticSearch:", response_elasticSearch)

        items_bd = [
            {
                "Nombre": doc["_source"]["RAZON_SOCIAL_ESTABLECIMIENTO"],
                "RegistroOficial": doc["_source"]["CODIGO_RNT"],
                #"RegistroEstado": doc["_source"]["ESTADO_RNT"],
                #"Camas": doc["_source"]["NUMERO_DE_CAMAS"],
                #"Habitaciones": doc["_source"]["NUMERO_DE_HABITACIONES"]
            }
            for doc in response_elasticSearch
        ]

        response_dict["result_bd"] = items_bd # Agrego los resultados de la BD al response
        responseGpt = await openai_service(prompt_usuario,to,user_language,response_dict) #response lleva los datos del tool call
        print("Respuesta final con lugares incluidos:", responseGpt)

        await whatsapp_service.send_message(to, responseGpt)

    async def consultar_bd_categoria(self, to, tipo_entidad_elastic, user_language):
        
        response_elasticSearch = await get_random_places(tipo_entidad_elastic, timeout=5)
        print("Lugares recomendados desde ElasticSearch:", response_elasticSearch)

        buttons = [] 
        added_titles = set()
        MAX_BUTTONS = 3 # Establece el límite estricto de WhatsApp

        for item in response_elasticSearch: 

            # 1. Romper el loop si ya alcanzamos el límite
            if len(buttons) >= MAX_BUTTONS:
                break

            source_data = item.get('_source', {}) 
            
            razon_social = source_data.get('RAZON_SOCIAL_ESTABLECIMIENTO', 'Lugar Desconocido')
            
            # IMPORTANTE: Usamos el título truncado (hasta 20 caracteres) para la validación, 
            # ya que WhatsApp solo muestra 20. Si dos nombres largos se truncan al mismo título,
            # solo se añadirá uno.
            button_title = razon_social[:20] 

            # === [LÓGICA DE VALIDACIÓN DE DUPLICADOS] ===
            if button_title in added_titles:
                # Si el título truncado ya existe en nuestro conjunto, saltamos este ítem.
                print(f"DEBUG: Omitiendo duplicado '{button_title}'.")
                continue 
            
            # Si no está en el conjunto, lo añadimos para futuras verificaciones.
            added_titles.add(button_title)
            # ============================================
            
            codigo_rnt = source_data.get('CODIGO_RNT', '00000') 
            button_id = f"rntBuscarLugar_{codigo_rnt}" 
            
            button = {
                "type": "reply",
                "reply": {
                    "id": button_id,
                    "title": button_title 
                }
            }
            buttons.append(button)
            print("Botón añadido:", buttons)
        if buttons: 
            messages = {
                                "Spanish": "He encontrado el/los siguiente(s) lugar(es). Selecciona uno para más detalles:",
                                "English": "I have found the following place(s). Select one for more details:",
                                "French": "J'ai trouvé le(s) lieu(x) suivant(s). Sélectionnez-en un pour plus de détails:"
                        }
            message_to_send = messages.get(user_language, messages["Spanish"]) 
            await whatsapp_service.send_interactive_buttons(to, message_to_send, buttons )
        else:
            await whatsapp_service.send_message(to, "Lo siento, no encontré lugares con ese nombre. Por favor, intenta de nuevo.")
  
    async def consultar_bd_nombre(self, to, criterio_busqueda_gpt,user_language):
        response_elasticSearch = await search_place_by_name_with_timeout(criterio_busqueda_gpt, timeout=5)
        print("Lugares EXACTO POR NOMBRE desde ElasticSearch:", response_elasticSearch)

        if response_elasticSearch:   
            buttons = [] 
            added_titles = set()
            MAX_BUTTONS = 3 # Establece el límite estricto de WhatsApp

            for item in response_elasticSearch: 

                 # 1. Romper el loop si ya alcanzamos el límite
                if len(buttons) >= MAX_BUTTONS:
                    break

                source_data = item.get('_source', {}) 
                
                razon_social = source_data.get('RAZON_SOCIAL_ESTABLECIMIENTO', 'Lugar Desconocido')
                
                # IMPORTANTE: Usamos el título truncado (hasta 20 caracteres) para la validación, 
                # ya que WhatsApp solo muestra 20. Si dos nombres largos se truncan al mismo título,
                # solo se añadirá uno.
                button_title = razon_social[:20] 

                # === [LÓGICA DE VALIDACIÓN DE DUPLICADOS] ===
                if button_title in added_titles:
                    # Si el título truncado ya existe en nuestro conjunto, saltamos este ítem.
                    print(f"DEBUG: Omitiendo duplicado '{button_title}'.")
                    continue 
                
                # Si no está en el conjunto, lo añadimos para futuras verificaciones.
                added_titles.add(button_title)
                # ============================================
                
                codigo_rnt = source_data.get('CODIGO_RNT', '00000') 
                button_id = f"rntBuscarLugar_{codigo_rnt}" 
                
                button = {
                    "type": "reply",
                    "reply": {
                        "id": button_id,
                        "title": button_title 
                    }
                }
                buttons.append(button)
            if buttons:
                messages = {
                                "Spanish": "He encontrado el/los siguiente(s) lugar(es). Selecciona uno para más detalles:",
                                "English": "I have found the following place(s). Select one for more details:",
                                "French": "J'ai trouvé le(s) lieu(x) suivant(s). Sélectionnez-en un pour plus de détails:"
                        }
                message_to_send = messages.get(user_language, messages["Spanish"]) 
              
                await whatsapp_service.send_interactive_buttons(to, message_to_send, buttons )
                return response_elasticSearch
            else:
                await whatsapp_service.send_message(to, "Lo siento, no encontré lugares con ese nombre. Por favor, intenta de nuevo.")
                return None
        else:
            await whatsapp_service.send_message(to, "Lo siento, no encontré lugares con ese nombre. Por favor, intenta de nuevo.")
            return None
 
    async def pintar_lugares_botones(self, to, response_elasticSearch, user_language):
         
        print("Lugares recomendados desde ElasticSearch:", response_elasticSearch)

        buttons = [] 
        added_titles = set()
        MAX_BUTTONS = 3 # Establece el límite estricto de WhatsApp

        for item in response_elasticSearch: 

            # 1. Romper el loop si ya alcanzamos el límite
            if len(buttons) >= MAX_BUTTONS:
                break

            source_data = item
            
            razon_social = source_data.get('RAZON_SOCIAL_ESTABLECIMIENTO', 'Lugar Desconocido')
            
            # IMPORTANTE: Usamos el título truncado (hasta 20 caracteres) para la validación, 
            # ya que WhatsApp solo muestra 20. Si dos nombres largos se truncan al mismo título,
            # solo se añadirá uno.
            button_title = razon_social[:20] 

            # === [LÓGICA DE VALIDACIÓN DE DUPLICADOS] ===
            if button_title in added_titles:
                # Si el título truncado ya existe en nuestro conjunto, saltamos este ítem.
                print(f"DEBUG: Omitiendo duplicado '{button_title}'.")
                continue 
            
            # Si no está en el conjunto, lo añadimos para futuras verificaciones.
            added_titles.add(button_title)
            # ============================================
            
            codigo_rnt = source_data.get('CODIGO_RNT', '00000') 
            button_id = f"rntBuscarLugar_{codigo_rnt}" 
            
            button = {
                "type": "reply",
                "reply": {
                    "id": button_id,
                    "title": button_title 
                }
            }
            buttons.append(button)
            print("Botón añadido:", buttons)
        if buttons: 
            messages = {
                                "Spanish": "He encontrado el/los siguiente(s) lugar(es). Selecciona uno para más detalles:",
                                "English": "I have found the following place(s). Select one for more details:",
                                "French": "J'ai trouvé le(s) lieu(x) suivant(s). Sélectionnez-en un pour plus de détails:"
                        }
            message_to_send = messages.get(user_language, messages["Spanish"]) 
            await whatsapp_service.send_interactive_buttons(to, message_to_send, buttons )
        else:
            await whatsapp_service.send_message(to, "Lo siento, no encontré lugares con ese nombre. Por favor, intenta de nuevo.")
  
    async def send_contact(self, to):
        print("Enviando contacto a:", to)
        contact = {
            "addresses": [
                {
                    "street": "Calle 21 # 10-52",
                    "city": "Chiquinquirá",
                    "state": "Boyacá",
                    "zip": "12345",
                    "country": "Colombia",
                    "country_code": "CO",
                    "type": "WORK",
                }
            ],
            "emails": [{"email": "contactenos@chiquinquira-boyaca.gov.co", "type": "WORK"}],
            "name": {
                "formatted_name": "Urgencias Chiquinquirá",
                "first_name": "Urgencias",
                "last_name": "Chiquinquirá",
                "middle_name": "",
                "suffix": "",
                "prefix": "",
            },
            "org": {
                "company": "Alcaldia Chiquinquira",
                "department": "Atención al Cliente",
                "title": "Representante",
            },
            "phones": [
                {"phone": "+1234567890", "wa_id": "1234567890", "type": "WORK"}
            ],
            "urls": [{"url": "https://www.chiquinquira-boyaca.gov.co", "type": "WORK"}],
        }
        await whatsapp_service.send_contact_message(to, contact)

 
# Instancia global, como en JS
message_handler = MessageHandler()