# Informe de exposicion — tunnel_guard (E-30)

Generado: 2026-09-11 20:33:44  
Escaneos: 7  
**Riesgo: CRITICO**

## Critico

- 192.168.1.133:8082 responde SIN credenciales (tipo=servidor_sin_auth): cualquiera que alcance ese puerto manda peticiones al movil; con el tunel abierto, 'cualquiera' es internet entero

## Alto

- 1 literales del token por defecto en el codigo

## Medio

- PIXEL_TOKEN no esta en el entorno: los modulos caen al default

## Tuneles

Ninguno detectado.

## Plan de migracion a Tailscale

**1. Instala Tailscale en el Pixel**

```
Play Store -> Tailscale -> abrir -> Log in (cuenta de Google vale).
```

**2. Instala Tailscale en el PC**

```
winget install tailscale.tailscale   (o descargalo de tailscale.com)
```

**3. Arranca en el PC**

```
tailscale up
```

**4. Anota la IP del movil**

```
tailscale status        # busca el Pixel; su IP empieza por 100.
```

**5. Dile al proyecto donde esta**

```
PIXEL_IPS=100.x.y.z   en el .env  (o en la variable de entorno)
```

**6. Apaga el tunel publico**

```
En Termux: pkill cloudflared   y quita el servicio: sv stop cloudflared  (o borra ~/.termux/boot/ si lo arranca ahi)
```

**7. Comprueba que se acabo**

```
GET /api/guard/scan  ->  tuneles: 0
```

## Estado de Tailscale

Tailscale no esta instalado en este PC.
