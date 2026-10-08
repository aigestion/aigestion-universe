import logging


def generate_video_clip(prompt):
    try:
        safe_prompt = prompt.replace(" ", "%20")
        # Generador de MP4/GIF dinámico mediante API generativa sintética
        video_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=480&height=270&nologo=true&seed=100"
        logging.info(f"Clip de vídeo solicitado para: {prompt}")
        return video_url
    except Exception as e:
        logging.error(f"Error generando vídeo: {str(e)}")
        return None
