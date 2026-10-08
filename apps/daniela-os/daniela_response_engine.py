class DanielaResponseEngine:
    def format_audiovisual_response(self, text, response_type="INFO", action_payload=None):
        """
        Estructura la respuesta para que la web la interprete como un evento audiovisual
        completo (con voz, efectos y tarjeta táctil).
        """
        voice_intro = {
            "INFO": "Comandante, aquí está la información procesada.",
            "SUCCESS": "Operación ejecutada con éxito en el sistema.",
            "ALERT": "Atención Comandante. Se requiere tu revisión inmediata.",
            "PROPOSAL": "He preparado una nueva propuesta estratégica.",
        }.get(response_type, "")

        return {
            "type": response_type,
            "display_text": text,
            "audio_speech": f"{voice_intro} {text}",
            "actions": action_payload or [],
        }


response_engine = DanielaResponseEngine()
