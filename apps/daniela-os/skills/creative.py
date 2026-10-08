import logging


def generate_image(prompt):
    try:
        safe_prompt = prompt.replace(" ", "%20")
        image_url = (
            f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"
        )
        logging.info(f"Imagen generada para: {prompt}")
        return image_url
    except Exception as e:
        logging.error(f"Error generando imagen: {str(e)}")
        return None
