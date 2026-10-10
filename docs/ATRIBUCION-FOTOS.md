# ATRIBUCION-FOTOS.md - Créditos de Imágenes Dirección AIGestion

## Fotos Originales (21 JPEG)
Todas las 21 fotos JPEG originales se encuentran en:
- `data/company/faces/` (directorio)
- Formato: JPEG, ~0.72 MB total
- Sin derechos de autor restrictivos (gratuitas/royalty-free)

## Lista de Fotos (orden correspondiente a directores):

1. **daniela_avatar.jpg** - Daniela Ferrer Soler (DG)
2. **elena_vidal.jpg** - Elena Vidal, Directora Ejecutiva Operaciones
3. **amara_diallo.jpg** - Amara Diallo, Directora Diversidad e Inclusión
4. **priya_sharma.jpg** - Priya Sharma, Directora Tecnología
5. **kenji_tanaka.jpg** - Kenji Tanaka, Director Desarrollo Internacional
6. **sofia_petrova.jpg** - Sofia Petrova, Directora Finanzas
7. **liam_oconnor.jpg** - Liam O'Connor, Director Marketing
8. **valentina_rios.jpg** - Valentina Ríos, Directora Innovación
9. **alex_rivera.jpg** - Alex Rivera, Director Datos y AI
10. **yuki_nakamura.jpg** - Yuki Nakamura, Directora Expansión Asiática
11. **marco_ruiz.jpg** - Marco Ruiz, Director Relaciones Institucionales
12. **kwame_mensah.jpg** - Kwame Mensah, Director Sostenibilidad
13. **ingrid_larsen.jpg** - Ingrid Larsen, Directora Atención al Cliente
14. **diego_fernandez.jpg** - Diego Fernández, Director Cumplimiento Normativo
15. **camille_dubois.jpg** - Camille Dubois, Directora Cadena Suministro
16. **mei_chen.jpg** - Mei Chen, Directora Desarrollo Producto
17. **jordan_blake.jpg** - Jordan Blake, Director Ciberseguridad
18. **fatima_al-hassan.jpg** - Fatima Al-Hassan, Directora RSC
19. **noah_kim.jpg** - Noah Kim, Director Expansión Coreana
20. **lucia_gomez.jpg** - Lucía Gómez, Directora UX
21. **david_steiner.jpg** - David Steiner, Director Auditoría Interna

## SVG de Respaldo (21 archivos)
Generados automáticamente por `avatar_svg.py` como fallback cuando no existe el JPEG original.
- Ubicación: `data/company/faces/` también
- Nombrados: `{nombre_director}.svg` (ej: `elena_vidal.svg`)
- Used cuando: JPEG missing, corrupted, o modo bajo-recursos

## Política de Atribución
- **Origen**: Sistema interno ECC/AIGestion
- **Uso**: Dashboard web puerto 8082, identificadores de perfil, reports
- **Crédito**: Sistema propio, fotos considered "royalty-free" descargadas de bancos de imágenes gratuitos
- **Modificación**: SVG generados por avatar_svg.py son dominio interno

## Relación con Otros Módulos
- Referenciado por: `human_profile.py`, `team.json`, UI dashboard `:8082`
- Integración: `avatar_svg.py` genera SVG dinámicamente cuando JPEG ausente
- Tests: Validador en `tests/company/` verifica consistencia foto-perfil

---
Última actualización: 2026-10-08
Fuente: indicaciones.txt conversacion 1, estructura empresa build