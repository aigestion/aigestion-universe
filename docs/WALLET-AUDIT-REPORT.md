# AUDITORIA DE WALLETS - aig
## Fecha: 2026-09-05
## Investigador: Sistema Automatizado

---

## RESUMEN EJECUTIVO

Se han identificado **4 wallets** asociadas al usuario Alejandro Fernandez. 

**NINGUNA de las wallets verificadas posee LAND en Decentraland.**

**La wallet SafePal (`0x80e8...9b65`) POSEE 1 LAND en The Sandbox** (Token ID: 93495, coordenadas -141, 25, tipo Regular). Verificada on-chain via Alchemy NFT API + Etherscan + RPC publico.

La wallet con mayor actividad (`0xacA9...435DA`) tiene 50 transacciones en Ethereum y 21 en Polygon, con 27 NFTs (principalmente Starbucks Odyssey), pero ningun LAND.

---

## WALLETS IDENTIFICADAS

### WALLET 1: MetaMask (de .env.master)
| Campo | Valor |
|-------|-------|
| **Direccion** | `0xD601baf7A7511b3b57A3055Ac4bBFbC79E34F31f` |
| **Origen** | Archivo .env.master / .env12 |
| **Clave privada** | Expuesta en archivos .env |
| **Saldo ETH** | ~0.000001 ETH |
| **Transacciones ETH** | 4 |
| **Transacciones Polygon** | 0 |
| **NFTs** | 0 |
| **LAND Decentraland** | NO |

**Ultimas transacciones ETH:**
| Fecha | Tipo | Valor | Estado |
|-------|------|-------|--------|
| 2026-08-08 | Contract Call (0x3f707e6b) | 0 ETH | OK |
| 2026-08-07 | Transfer | 0.000027 ETH | OK |
| 2026-05-12 | Token Transfer | 0 ETH | OK |
| 2026-05-12 | Transfer | 0.000047 ETH | OK |

---

### WALLET 2: MetaMask Profile 5 - Cuenta 1
| Campo | Valor |
|-------|-------|
| **Direccion** | `0x8a1b4d661d038822ebc9b4f4f420e73b6a498ab0` |
| **Origen** | Chrome Profile 5 - Vault MetaMask |
| **Saldo ETH** | ~0 ETH |
| **Transacciones ETH** | 0 |
| **Transacciones Polygon** | 0 |
| **NFTs** | 0 |
| **LAND Decentraland** | NO |

**Estado:** Wallet vacia, sin actividad.

---

### WALLET 3: MetaMask Profile 5 - Cuenta 2 (MAS ACTIVA)
| Campo | Valor |
|-------|-------|
| **Direccion** | `0xacA92E438df0B2401fF60dA7E4337B687a2435DA` |
| **Origen** | Chrome Profile 5 - Vault MetaMask |
| **Saldo ETH** | ~0 ETH |
| **Transacciones ETH** | 50 |
| **Transacciones Polygon** | 21 |
| **NFTs Polygon** | 27 |
| **LAND Decentraland** | NO |

**Actividad reciente ETH (ultimas 10 de 50):**
| # | Fecha | De | Para | Valor | Metodo |
|---|-------|-----|------|-------|--------|
| 1 | 2026-09-05 | 0x762D... | 0xacA9... | 0 ETH | transfer |
| 2 | 2026-09-05 | 0x3740... | 0xacA9... | 0 ETH | transfer |
| 3 | 2026-09-05 | 0x553A... | 0xacA9... | 0 ETH | approve |
| 4 | 2026-09-05 | 0x370A... | 0xacA9... | 0 ETH | transferFrom |
| 5 | 2026-09-05 | 0xFE76... | 0xacA9... | 0 ETH | approve |
| 6 | 2026-09-05 | 0x18DD... | 0xacA9... | 0 ETH | transferFrom |
| 7 | 2026-09-05 | 0x3247... | 0xacA9... | 0 ETH | transfer |
| 8 | 2026-09-05 | 0xAfa4... | 0xacA9... | 0 ETH | approve |
| 9 | 2026-09-05 | 0xa450... | 0xacA9... | 0 ETH | approve |
| 10 | 2026-09-05 | 0x3247... | 0xacA9... | 0 ETH | transfer |

**Actividad Polygon (21 transacciones):**
- Periodo: 2025-09-29 a 2026-03-05
- Total recibido: ~7.2 MATIC
- Tipos: Transferencias simples, sin interaccion con contratos de Decentraland

**NFTs en Polygon (27 total):**
| # | Coleccion | Token ID |
|---|-----------|----------|
| 1 | Doing Good Journey Stamp | 29067 |
| 2 | Coffee Heritage Journey Stamp | 3041 |
| 3 | The Starbucks Siren Collection | 1131 |
| 4 | Going Places Journey Stamp | 464 |
| 5 | 2023 Unwrapped Journey Stamp | 9547 |
| 6 | The Holiday Cup Collection | 2595 |
| 7 | Heritage Journey Stamp | 2748 |
| 8 | Constant Conversation Airdrop Stamp | 12004 |
| 9 | Aku's Rocket Journey Stamp | 4188 |
| 10 | 20 Years of PSL Journey Stamp | 5023 |
| 11 | The Starbucks Green Apron Collection | 1418 |
| 12 | The Starbucks Green Apron Collection | 202 |
| 13 | Jade Purple Brown Airdrop Stamp | 2076 |
| 14 | World of Coffee Journey Stamp | 4669 |
| 15 | Bean to Cup Journey Stamp | 3295 |
| 16 | Signature Showdown Journey Stamp | 378 |
| 17 | Starbucks Odyssey Achievement Stamp L4 | 447 |
| 18 | CryptoPals | 683 |
| 19 | CryptoPals | 131 |
| 20 | Starbucks Odyssey Avatar Collection | 4204 |
| 21-27 | (Otros NFTs Starbucks/CryptoPals) | - |

**Nota:** Todos los NFTs son de programas de fidelidad (Starbucks Odyssey) o colecciones genericas. **Ningun LAND de Decentraland.**

---

### WALLET 4: SafePal (Seed Phrase) - POSEE LAND EN THE SANDBOX
| Campo | Valor |
|-------|-------|
| **Direccion** | `0x80e87Dd67d25a2Bb3FCb7b1b84c7a9aBbd1e9b65` |
| **Origen** | Archivo .env14 - Seed phrase: `track fossil arm erase gauge local endless exhibit magic rule second green` |
| **Saldo ETH** | ~0.051789 ETH (~$128) |
| **SFP Token** | 54.9 SFP (~$15) |
| **Portfolio multichain** | ~$1,218 (BNB Chain $1,074 + Ethereum $144) |
| **NFTs Ethereum** | 7 (incluye 1 Sandbox LAND) |
| **NFTs Polygon** | 90 (mayoria ERC-1155 sin valor) |
| **SAND balance** | 0 SAND |
| **LAND Decentraland** | NO |
| **LAND The Sandbox** | **SI - VERIFICADO** |

**LAND de The Sandbox encontrada:**
| Campo | Valor |
|-------|-------|
| **Token ID** | 93495 |
| **Nombre** | LAND (-141, 25) |
| **Coordenadas mapa** | X: 63, Y: 229 |
| **Tipo** | Regular (1x1) |
| **Coleccion** | The Sandbox K-verse Hallyu Rising LAND Sale |
| **Contrato** | `0x5CC5B05a8A13E3fBDB0BB9FcCd98D38e50F90c38` (ERC-721) |
| **Blockchain** | Ethereum mainnet |
| **Red marketplace** | Polygon (LAND puentada) |
| **URL** | https://www.sandbox.game/en/lands/dfcbb07d-e594-436d-9d40-dd730527323a/ |
| **Floor price LAND (24h)** | ~$42-45 (0.017-0.0182 ETH) |
| **Origen de fondos** | Binance (3 yrs 231 dias atras) |

**Verificacion on-chain:** Confirmado via Alchemy NFT API (balanceOf = 1) + Etherscan (NFT holdings list) + RPC publico (ethereum.publicnode.com).

---

## ANALISIS DE SEGURIDAD

### Credenciales Expuestas Encontradas

| Archivo | Ruta | Contenido Critico |
|---------|------|-------------------|
| .env | C:\Users\Alejandro\.env | Gemini API Key, Grok API Key |
| .env-critical-backup | C:\Users\Alejandro\.env-critical-backup | Gemini API Key, PIN Daniela |
| .env12 | C:\Users\Alejandro\Documents\XXX\anty\.env12 | **100+ API keys**, MetaMask key, JWT secrets, contrasenas Gmail, Stripe, Twilio |
| .env13 | C:\Users\Alejandro\Documents\XXX\anty\.env13 | Igual que .env12 |
| .env14 | C:\Users\Alejandro\Documents\XXX\anty\.env14 | Igual + **Seed phrase SafePal** |
| .env.master | C:\Users\Alejandro\aig\.env.master | 102 APIs y secrets |

**Riesgo:** CRITICO - Todas las claves privadas y seed phrases estan en texto plano.

---

## CONCLUSIONES

1. **No se encontro LAND de Decentraland** en ninguna de las 4 wallets verificadas.

2. **SE ENCONTRO LAND de The Sandbox** en la Wallet 4 (SafePal):
   - Token ID: 93495 | Coordenadas: (-141, 25) | Tipo: Regular 1x1
   - Coleccion: K-verse Hallyu Rising LAND Sale
   - Contrato: 0x5CC5B05a8A13E3fBDB0BB9FcCd98D38e50F90c38 (Ethereum mainnet)
   - La "parcela perdida" del reporte anterior estaba en The Sandbox, no en Decentraland.

3. **La wallet mas activa** (`0xacA9...435DA`) tiene actividad significativa en ETH y Polygon, pero centrada en:
   - Transacciones DeFi (approve, transferFrom)
   - NFTs de Starbucks Odyssey (27 unidades)
   - Ninguna interaccion con contratos de Decentraland

4. **Resolucion de la "parcela perdida":**
   - La parcela SI existe y esta en la wallet SafePal (Wallet 4)
   - Es una LAND de The Sandbox (no Decentraland como se busco originalmente)
   - La wallet SafePal no fue verificada a fondo en el reporte inicial
   - Verificacion on-chain completada: 1 LAND confirmada

4. **Recomendacion:**
   - **Rotar TODAS las API keys** inmediatamente
   - **Transferir fondos** a wallets nuevas
   - **Borrar** todos los archivos .env expuestos
   - Usar **password manager** (Bitwarden, 1Password)

---

## AUDITORIA DE SEGURIDAD - TRANSACCIONES (2026-09-05)

### Wallet analizada: SafePal (0x80e87Dd67d25a2Bb3FCb7b1b84c7a9aBbd1e9b65)
- Ethereum: 21 transacciones | BSC: 92 transacciones
- Periodo: hace 1327 dias a hace 98 dias

---

### HALLAZGO CRITICO: Interaccion con contrato de phishing

**Fecha:** hace 98 dias (~May 30, 2026) | **Plataforma:** Ethereum + BSC

| Campo | Detalle |
|-------|---------|
| **Tx 1 (ETH)** | `0xd0a2c6b4...` - Approve de 91.5 "AKT" (token falso) |
| **Contrato phishing** | `0xC727f87871ee12Bbcedd2973746D1Deb7529aaD6` (Fake_Phishing4733383) |
| **DEX phishing** | `0x709de0B97e369661C99AD54F2B858139897D3DbA` |
| **Tx 2 (ETH)** | `0x48c11eb4...` - Swap de tokens falsos en DEX phishing |
| **Tx 3 (ETH)** | `0xebb182c6...` - Execute Uniswap V4 (0.29 ETH) misma sesion |
| **Tx BSC** | `0x3740b1d8...` - Swap 0.0666 BNB en mismo DEX phishing |

**Analisis del DEX phishing (0x709de0B9...):**
- Contiene tokens spam: claimvooi.com, gas711.com, BTCFund, DIXT, Duhash.games
- NFTs de "claimvooi.com" (dominio de phishing conocido)
- NO es un DEX legitimo

**Impacto:** El phishing solo afecto tokens falsos/spam. No se robaron activos reales.

---

### HALLAZGO MEDIO: Ataques de dusting

3 micro-transacciones recibidas en BSC desde direcciones desconocidas:

| Fecha | Remitente | Cantidad | Tipo |
|-------|-----------|----------|------|
| hace 98 dias | ghostswap-exchange.bnb | 1 wei | Dusting |
| hace 824 dias | 0xc7A5F5C7... | 0.00000113 BNB | Dusting |
| hace 856 dias | 0xC7A5Cf0f... | 0.000001 BNB | Dusting |

**Proposito:** Rastrear la actividad de la wallet para futuros ataques.

---

### HALLAZGO MEDIO: NFT sospechoso transferido

| Campo | Detalle |
|-------|---------|
| **Fecha** | hace 353 dias (~Sep 17, 2025) |
| **Contrato** | Decentraland LAND (0xF87E31492Faf...) |
| **Token ID** | 115792089237316195423570985008687907835915583952672702402825479028892950855794 |
| **Tipo** | Transfer From (SafePal -> MetaMask 0xD601...F31f) |
| **Nota** | Token ID cercano a 2^256 = NFT de spam/falso, no LAND real |

---

### ESTADO DE ACTIVOS (VERIFICADO ON-CHAIN)

| Activo | Estado | Riesgo |
|--------|--------|--------|
| Sandbox LAND (ID 93495) | SEGURO en wallet | Sin riesgo |
| ETH (0.0518 / ~$128) | Intacto | Sin riesgo |
| SFP (54.9 / ~$15) | Intacto | Sin riesgo |
| BNB Chain ($1,074) | Intacto | Sin riesgo |
| Approvals activos (ETH) | 0 (verificado en revoke.cash) | Sin riesgo |

**Conclusion:** No hubo hackeo de activos reales. El phishing afecto unicamente tokens falsos. La wallet esta siendo rastreada via dusting.

---

### RECOMENDACIONES DE SEGURIDAD

1. **MOVER ACTIVOS A NUEVA WALLET** - Prioridad maxima
   - La wallet interactuo con contratos de phishing
   - La seed phrase esta expuesta en .env14
   - Crear nueva wallet, transferir LAND, ETH, SFP y tokens BSC
2. **Revocar approvals en BSC** - Verificar revoke.cash en BSC
3. **Borrar .env14** - Eliminar seed phrase expuesta
4. **No usar esta wallet** para nuevas transacciones
5. **No firmar transacciones** de sitios desconocidos

---

## AUDITORIA METAMASK WALLET 1 - ATAQUE EIP-7702 (2026-09-05)

### Wallet: 0xD601baf7A7511b3b57A3055Ac4bBFbC79E34F31f (MetaMask .env.master)

### Trazabilidad de la "parcela desaparecida"

| Paso | Fecha | Evento |
|------|-------|--------|
| 1 | hace 353 dias (~Sep 2025) | SafePal transfiere "LAND" a MetaMask (token ID cercano a 2^256 = FALSO/spam) |
| 2 | hace 116 dias (~Jun 2026) | Wallet recibe ETH (0.0000474) y envia MANA tokens |
| 3 | hace 70 dias (~Jun 27 2026) | Atacante 0x789a9FE9... despliega contrato drainer 0xF366FBf9... |
| 4 | hace 28 dias (~Aug 8 2026) | **ATAQUE EIP-7702**: wallet delega al drainer, que transfiere LAND + ETH |

### Detalles del ataque EIP-7702

| Campo | Valor |
|-------|-------|
| **TX** | 0x7346be2e55109bbcdd7966878c4bf3d77f4d87389edf97ea1dc56cf624dc8f28 |
| **Tipo** | EIP-7702 (Type 4) - delegacion de cuenta |
| **Atacante** | 0x789a9FE9f1448E0B1d6Ee0d49333054E590435e2 |
| **Contrato drainer** | 0xF366FBf916917117e6a2782aE5F920b4b0C5B3e4 |
| **Creador del drainer** | 0x789a9FE9... (hace 70 dias) |
| **Funcion drainer** | 0x3f707e6b (error: "Caraleven") |
| **LAND transferida a** | 0x789a9FE9f1448E0B1d6Ee0d49333054E590435e2 |
| **ETH transferida a** | 0x7777FF8eA1FEd0baDCE1149A9b433D708Cd27777 (0.00002749 ETH) |
| **Token ID LAND** | 115792...855794 (cercano a 2^256 = NFT de spam, NO LAND real) |

### Conclusion sobre la "parcela de Decentraland"

**La "parcela" que desaparecio NO era un LAND real de Decentraland.**

- El token ID (115792...855794) esta cercano a 2^256, lo cual es imposible para un LAND real
- Los LAND reales de Decentraland tienen token IDs entre 0 y ~90,000
- Era un NFT de spam/falso que fue airdropado a la wallet SafePal y transferido a MetaMask
- El atacante uso un contrato drainer EIP-7702 para robarlo junto con el ETH restante
- **No se perdio ningun activo de valor real** en este ataque

### Correccion del reporte anterior

| Wallet | Reporte anterior | Realidad |
|--------|-----------------|----------|
| Wallet 3 (0xacA9...) | "MetaMask Profile 5 - Cuenta 2 (MAS ACTIVA)" | **Es el contrato mUSD de MetaMask**, NO una wallet personal |
| Wallet 3 transacciones | "50 transacciones ETH" | 232,636 transacciones del contrato mUSD (no personales) |
| LAND Decentraland | "NO" en todas las wallets | Confirmado: NUNCA hubo un LAND real de Decentraland |

---

## DATOS TECNICOS

- **MetaMask instalado en:** Chrome Profile 5
- **Decentraland Launcher:** Instalado, ultima sesion 2026-09-05 17:15:37
- **Perfiles Chrome encontrados:** 5 (Profile 5, 6, 7, 12, 16)
- **Contraseña vault MetaMask:** `<redactado>` (estaba en este informe; cámbiala en MetaMask)
- **Binance deposit address confirmado:** 0xC7A5C3c9... (transferencias legitimas)
- **DEX phishing confirmado:** 0x709de0B9... (contiene tokens spam claimvooi.com)

---

*Reporte actualizado el 2026-09-05 con auditoria de transacciones y seguridad*
