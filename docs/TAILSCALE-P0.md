# Cerrar el P0: del túnel público a Tailscale

Estado verificado el **2026-09-11**:

| Qué | Estado |
|---|---|
| Tailscale en el móvil | ✅ `com.tailscale.ipn`, IP **`100.65.50.219`** |
| Tailscale en el PC | ❌ **no instalado** (ni app, ni servicio, ni ejecutable) |
| `cloudflared` publicando el 8082 | 🔴 **sigue vivo**, pid 28646 |
| Puerto 8082 del móvil | escucha en `0.0.0.0` (todas las interfaces) |
| Token del gateway | ✅ generado (43 chars) y guardado en `.env` |

---

## 1. Instalar Tailscale en el PC (lo haces tú, 2 min)

El instalador ya está descargado:

```
C:\Users\Alejandro\aig\data\instaladores\tailscale-setup-amd64.msi
```

Doble clic → instalar. Pide permisos de administrador (normal, crea un
servicio). Al abrirse, **inicia sesión con la MISMA cuenta que usaste en el
móvil**: si son cuentas distintas, las dos máquinas no se ven.

Comprobar:

```bash
ping 100.65.50.219
```

Antes de instalar da "tiempo de espera agotado". Cuando funcione, responde.

---

## 2. Matar el `cloudflared` en el móvil (lo haces tú en Termux, 5 s)

adb **no puede** matarlo: el proceso es de Termux y el móvil no tiene root
(`kill: 28646: Operation not permitted`). En Termux:

```bash
pkill cloudflared
```

Y para que **no vuelva a arrancar** (lo vigila un `runsv`):

```bash
sv down cloudflared          # para el servicio ahora
rm -f ~/../usr/var/service/cloudflared   # lo quita del arranque (opcional)
```

Comprobar en el móvil:

```bash
pgrep -a cloudflared         # no debe devolver nada
```

> ⚠️ No hace falta `am force-stop com.termux`: eso mataría también el gateway
> y todo lo que tengas corriendo en Termux.

---

## 3. Verificar que el agujero está cerrado

Desde el PC:

```bash
curl -m 5 http://192.168.1.133:8082/     # debe fallar (conexión rechazada)
```

Y en DanielaOS: `GET /api/guard/scan`. El nivel debe bajar de **CRITICO**.

Ojo: el 8082 escucha en `0.0.0.0`, así que sigue siendo alcanzable por
cualquiera en tu WiFi. Con Tailscale lo ideal es que el gateway escuche solo
en la IP de Tailscale (`100.65.50.219`) en vez de en todas. Eso se cambia en
el móvil, en el arranque del gateway.

---

## 4. Poner el token en el móvil

El token está en tu `.env` (variable `PIXEL_GATEWAY_TOKEN`). Para verlo:

```bash
grep PIXEL_GATEWAY_TOKEN .env
```

En Termux, añádelo al entorno del gateway:

```bash
echo 'export PIXEL_GATEWAY_TOKEN=<pega_aqui_el_token>' >> ~/.bashrc
source ~/.bashrc
```

Luego reinicia el gateway. Hasta que el token coincida en los dos lados, las
llamadas devolverán 401 (fail-closed: mejor cerrado que abierto).

---

## 5. Qué se ha configurado ya en el `.env`

```
PIXEL_IP=100.65.50.219
PIXEL_GATEWAY_URL=http://100.65.50.219:8082
PIXEL_GATEWAY_TOKEN=<43 chars>
PIXEL_TOKEN=<el mismo>
PIXEL_IPS=100.65.50.219        # IPs que escanea tunnel_guard
```

`PIXEL_GATEWAY_URL` apunta a la IP de Tailscale, así que **no funcionará hasta
que instales Tailscale en el PC**. Es lo esperado.

---

## 6. Incidente encontrado de paso: el `.env` no se cargaba

`config/.env` (556 claves: `DANIELA_PIN`, todas las API) **no lo leía nadie**:
el código busca `.env` en la raíz y no existía. Resultado: `DANIELA_PIN` y
todas las `PIXEL_*` llegaban vacías.

Arreglado copiando `config/.env` → `.env` en la raíz (copia, no movimiento:
no se ha perdido nada). Ahora `DANIELA_PIN` carga correctamente.

Ambos ficheros están ignorados por git, así que no hay riesgo de subirlos.
