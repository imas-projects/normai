# Revisión F1 - Cambios solicitados

## 1. Revisar correctamente la migración de `ProcessRequirement` hacia `StandardRequirement`

Aquí quiero que te pares un momento a revisar bien el cambio que has hecho en la relación `ProcessRequirement.requirement`, porque es justo el tipo de cambio que puede parecer correcto en el modelo pero dar problemas serios al aplicarlo sobre una base con datos.

Hasta ahora, ese campo apuntaba al modelo antiguo de requisitos. En esta fase lo has cambiado para que apunte al nuevo modelo `StandardRequirement`. A nivel de diseño la idea puede tener sentido, pero el problema no está en el modelo en sí, sino en qué pasa con los datos que ya pudiera haber en la base de datos.

Ahora mismo, la migración cambia la clave foránea para que deje de apuntar a la tabla antigua y pase a apuntar a la nueva, pero no explica cómo se trasladan los datos previos. Dicho de forma muy simple: si antes había registros guardados que apuntaban a requisitos antiguos, no vale con decir “a partir de ahora este campo apunta a otra tabla”. Hay que comprobar qué ocurre con esos valores y cómo se mantiene su significado.

Lo que necesito que revises de forma expresa es esto:

- Si en la base de datos ya existen registros en `ProcessRequirement`.
- A qué modelo y a qué tabla apuntaban esos registros antes del cambio.
- Si existe una equivalencia real entre los requisitos antiguos y los nuevos `StandardRequirement`.
- Qué ocurre al ejecutar la migración sobre una base con datos ya cargados.
- Si las relaciones antiguas se conservan correctamente o si se rompen.

La pregunta clave que debes responder es esta:

> Si existe ya información guardada en la base de datos y aplico esta migración, ¿los registros siguen apuntando correctamente a su requisito correspondiente o la relación queda inconsistente?

Si no puedes garantizar que esa transición funciona bien, entonces la migración no está cerrada.

### Qué espero que corrijas

Necesito que plantees una transición segura de datos. Algunas formas razonables de resolverlo serían:

- Mantener temporalmente el campo antiguo y crear uno nuevo hacia `StandardRequirement`.
- Crear una migración de datos que copie o transforme la información antigua hacia el nuevo modelo.
- Eliminar el campo antiguo solo después de comprobar que la correspondencia se ha realizado bien.

Si en tu planteamiento asumes que no hay que conservar datos previos porque la base se considera reinicializable en esta fase, entonces también tienes que dejarlo documentado de forma explícita y justificarlo. No puede quedar como una suposición implícita.

### Qué debes entregarme en la corrección

- Una explicación breve de cómo has resuelto la transición entre el modelo antiguo y el nuevo.
- La migración o secuencia de migraciones corregida.
- Una comprobación de que el cambio funciona no solo en una base vacía, sino también en el escenario en el que existan datos previos.

## 2. No reescribir ni romper el historial de migraciones del módulo `risks`

Aquí necesito que revises cómo has gestionado las migraciones del módulo `risks`, porque ahora mismo el branch deja el historial en un estado bastante frágil.

El problema no es solo que hayas cambiado modelos del módulo `risks`, sino que has modificado la migración inicial y además has eliminado migraciones posteriores. Eso puede parecer aceptable si uno mira únicamente el esquema final, pero en Django las migraciones no son solo una foto del estado actual: también representan el historial de cómo ha ido evolucionando la base de datos.

Dicho de forma sencilla: una vez que una migración forma parte del proyecto y puede haber sido aplicada en una base de datos, no conviene reescribirla como si el pasado no hubiera existido. Si cambias una `0001_initial.py` ya publicada y además eliminas migraciones intermedias, dejas de garantizar que otra instalación pueda reconstruir o actualizar su base de datos siguiendo el mismo camino.

Aquí es importante que tengas clara la diferencia entre estas dos cosas:

- Cambiar los modelos actuales del sistema.
- Reescribir el historial de cómo se llegó a esos modelos.

Lo primero es normal. Lo segundo solo puede hacerse con mucho cuidado y siguiendo una estrategia compatible.

### Por qué esto es un problema

Piensa en las migraciones como una secuencia de pasos numerados que Django usa para saber:

- qué cambios se hicieron,
- en qué orden,
- y cuáles ya se aplicaron en cada base de datos.

Si una base de datos ya aplicó `0001`, `0002`, `0003`, `0004` y `0005`, y en tu rama desaparecen `0002` a `0005` o se modifica el contenido de `0001`, entonces el historial que conoce esa base de datos ya no coincide con el historial que hay en el código.

Eso puede provocar varios problemas:

- que una instalación existente no pueda migrar correctamente;
- que Django detecte inconsistencias entre el estado registrado y los archivos reales;
- que una base nueva y una base ya existente lleguen al “mismo” modelo final por caminos incompatibles;
- o que el proyecto funcione en una instalación limpia, pero falle al actualizar una instalación previa.

En otras palabras: no basta con que “en limpio me cree bien las tablas”. También tiene que quedar garantizado que una base anterior pueda evolucionar sin romperse.

### Qué necesito que revises y compruebes

Lo que necesito que compruebes aquí es lo siguiente:

- Si `risks/0001_initial.py` ya formaba parte del historial previo del proyecto.
- Si las migraciones `0002`, `0003`, `0004` y `0005` habían existido como parte del desarrollo anterior.
- Qué ocurre si alguien tiene una base de datos que ya aplicó esas migraciones antiguas y actualiza a tu branch.
- Si tu solución actual permite tanto instalaciones nuevas como actualizaciones desde estados anteriores.

La pregunta clave que debes responder es esta:

> ¿La evolución del módulo `risks` sigue siendo compatible con una base de datos que ya hubiera aplicado el historial anterior, o solo funciona en una instalación nueva?

Si solo funciona en limpio, entonces la solución no está bien cerrada.

### Qué espero que corrijas

Necesito que dejes el historial de migraciones en un estado consistente. Dependiendo de la solución que adoptes, eso puede implicar:

- restaurar las migraciones eliminadas;
- dejar intacta la migración inicial si ya formaba parte del historial publicado;
- crear nuevas migraciones a partir del estado anterior, en vez de reescribir las existentes;
- o, si de verdad quieres compactar el historial, hacerlo mediante una estrategia de squash compatible y no borrando directamente las migraciones anteriores en esta misma fase.

Lo importante aquí es que no se rompa ni la trazabilidad del esquema ni la capacidad de actualizar bases de datos que ya existían.

### Qué debes entregarme en la corrección

- Una explicación breve de qué problema había en el historial de migraciones y cómo lo has corregido.
- Un historial de migraciones de `risks` que sea coherente y compatible.
- Una comprobación razonada de que el módulo funciona tanto en instalación nueva como en actualización desde el historial anterior.

## 3. Revisar las referencias que siguen usando el modelo antiguo de requisitos

Aquí necesito que revises todas las partes del código que dependen del modelo de requisitos, porque el refactor no termina al cambiar el modelo y las migraciones. También hay que adaptar bien el código que consume esos datos.

He detectado al menos un caso claro en el módulo `ai_functions`, donde el código sigue accediendo al requisito como si la estructura anterior siguiera vigente. Después del cambio que has introducido, esa suposición ya no vale.

Dicho de forma simple: has cambiado la estructura de los datos, pero hay partes del código que todavía “piensan” que los datos siguen siendo como antes.

### Qué está pasando exactamente

Antes, determinadas funciones trabajaban con una relación de requisitos más simple o con otro tipo de objeto. Ahora, tras el refactor, `checklist_obj.question.requirement` ya no representa directamente el requisito final, sino un `ProcessRequirement`, y dentro de él aparece el nuevo `StandardRequirement`.

Eso significa que cualquier código que acceda a atributos antiguos sin revisar la nueva cadena de relaciones puede quedar roto.

En el caso detectado, el código intenta acceder a un atributo que ya no existe en el nuevo modelo. El resultado más probable es un error en ejecución cuando se invoque esa funcionalidad.

Este tipo de problema es importante porque muchas veces no se ve solo mirando modelos o migraciones: aparece cuando se ejecuta una funcionalidad real de la aplicación. Por eso, después de un refactor de dominio, no basta con que el modelo “cuadre” sobre el papel; hay que revisar también los puntos donde ese modelo se usa de verdad.

### Qué necesito que revises y compruebes

Lo que necesito que revises aquí es lo siguiente:

- Qué partes del proyecto acceden al campo `requirement` o a objetos relacionados con requisitos.
- Si esas partes del código siguen siendo válidas con la nueva estructura `ProcessRequirement -> StandardRequirement`.
- Si hay funciones, vistas, utilidades o integraciones IA que siguen usando atributos del modelo antiguo.
- Si los textos, referencias o descripciones que antes se obtenían de un modelo ahora deben obtenerse de otro.

La pregunta clave que debes responder es esta:

> Después del refactor, ¿todo el código que usa requisitos está recorriendo correctamente las nuevas relaciones o sigue habiendo funciones que acceden a atributos que ya no existen?

### Qué espero que corrijas

Necesito que hagas una revisión completa de las referencias al modelo antiguo y adaptes el código a la nueva estructura real.

Eso implica:

- corregir los accesos erróneos ya detectados;
- revisar si hay otros accesos similares en vistas, utilidades, serialización o lógica de negocio;
- comprobar que los nombres, textos y referencias que se muestran al usuario siguen teniendo sentido con el nuevo modelo.

No quiero solo una corrección puntual “para que no falle esa línea”, sino una revisión coherente del impacto del refactor en todo el código que depende de esos datos.

### Qué debes entregarme en la corrección

- Una explicación breve de qué partes seguían usando el modelo antiguo.
- Las correcciones realizadas en los puntos afectados.
- Una comprobación de que las funcionalidades relacionadas con auditorías y asistencia IA siguen funcionando con el nuevo modelo de requisitos.

## 4. Eliminar la configuración local hardcodeada y parametrizar correctamente el proyecto

Aquí necesito que revises la configuración del proyecto, porque ahora mismo has dejado en el repositorio datos de conexión locales escritos directamente en `settings.py`.

Esto no es un detalle menor ni una simple cuestión de estilo. Cuando en un proyecto se dejan el nombre de la base de datos, el usuario, la contraseña o el host escritos directamente en el código, el proyecto queda acoplado al entorno personal de quien lo ha desarrollado y deja de ser fácil de reproducir por otra persona.

Además, esto contradice la propia idea que se describe en la documentación, donde se indica que la configuración debería depender de variables de entorno.

### Por qué esto es un problema

Dicho de forma sencilla: el código del proyecto no debería depender de tu máquina concreta para poder ejecutarse.

Ahora mismo, la configuración deja ver esta idea:

- la base de datos se llama de una forma concreta;
- el usuario es uno concreto;
- la contraseña es una concreta;
- y el host también está fijado.

Eso provoca varios problemas:

- otra persona no puede ejecutar el proyecto sin editar el código fuente;
- la configuración del entorno queda mezclada con la lógica de la aplicación;
- se exponen credenciales o datos sensibles dentro del repositorio;
- y se dificulta la revisión, el despliegue y el mantenimiento.

Aunque el proyecto sea académico, esto hay que corregirlo porque forma parte de una práctica básica de desarrollo ordenado y seguro.

### Qué necesito que revises y compruebes

Lo que necesito que revises aquí es lo siguiente:

- Qué parámetros de configuración están escritos directamente en `settings.py`.
- Cuáles de esos parámetros dependen del entorno local.
- Si el proyecto puede ejecutarse en otra máquina sin modificar manualmente el código.
- Si la documentación realmente coincide con la forma en que se configura el proyecto.

La pregunta clave que debes responder es esta:

> ¿El proyecto puede configurarse desde fuera del código, de forma que otra persona lo ejecute aportando sus propios valores, o sigue dependiendo de valores fijos escritos en `settings.py`?

### Qué espero que corrijas

Necesito que parametrices la configuración del proyecto y saques del código todos los valores que dependen del entorno.

Eso implica, como mínimo:

- no dejar credenciales de base de datos hardcodeadas;
- leer los parámetros sensibles o variables del entorno desde variables externas;
- mantener `settings.py` como configuración general del proyecto, no como reflejo de una instalación personal;
- dejar preparado un mecanismo claro para que otra persona pueda definir sus propios valores.

Además, la documentación tiene que ser coherente con esa solución. Si dices que el proyecto se configura con variables de entorno, entonces el código y los archivos de apoyo tienen que responder de verdad a ese planteamiento.

### Qué debes entregarme en la corrección

- Una explicación breve de cómo has desacoplado la configuración del entorno local.
- La configuración corregida para que no dependa de credenciales fijas en el código.
- Una forma clara y documentada de que otro usuario pueda arrancar el proyecto con su propia configuración.

## 5. Corregir la documentación de puesta en marcha para que sea realmente ejecutable

Aquí necesito que revises la documentación de arranque del proyecto, porque ahora mismo no es consistente con la estructura real del repositorio.

Esto es importante porque la documentación de onboarding no debe ser solo orientativa: tiene que servir de verdad para que otra persona pueda clonar el proyecto, instalar lo necesario y ponerlo en marcha sin tener que adivinar pasos ni corregir rutas por su cuenta.

Ahora mismo hay indicaciones que no encajan con lo que realmente existe en el repositorio. Eso hace que la documentación no sea una guía fiable de validación.

### Por qué esto es un problema

Dicho de forma sencilla: si alguien sigue tus instrucciones tal y como están escritas y no consigue arrancar el proyecto, entonces la documentación no está cumpliendo su función.

La documentación de puesta en marcha debe ser:

- correcta;
- completa;
- coherente con el código real;
- y suficiente para que otro revisor repita el proceso sin depender de aclaraciones adicionales.

Cuando en la documentación aparecen rutas, comandos o archivos que no coinciden con la realidad del repositorio, se transmite una imagen de trabajo no cerrado, aunque el código pueda tener partes bien resueltas.

### Qué necesito que revises y compruebes

Lo que necesito que revises aquí es lo siguiente:

- Si las rutas y nombres de archivos mencionados en la documentación existen realmente.
- Si los comandos de instalación y ejecución corresponden a la estructura actual del proyecto.
- Si los archivos auxiliares que mencionas existen de verdad en el repositorio.
- Si una persona que no ha trabajado en tu entorno puede seguir la guía sin tener que improvisar.

La pregunta clave que debes responder es esta:

> ¿Puede otra persona clonar el repositorio y arrancar el proyecto siguiendo únicamente esta documentación, o necesita corregir pasos porque la guía no coincide con el proyecto real?

### Qué espero que corrijas

Necesito que rehagas la documentación de puesta en marcha para que refleje exactamente el estado real del proyecto.

Eso implica:

- corregir rutas erróneas;
- corregir comandos que no correspondan a la estructura actual;
- eliminar referencias a archivos que no existan;
- añadir los pasos mínimos necesarios para que el proceso sea reproducible;
- y dejar claro qué requisitos previos necesita el proyecto para funcionar.

No quiero una guía genérica, sino una guía realista, concreta y verificable.

### Qué debes entregarme en la corrección

- La documentación de onboarding corregida y coherente con el repositorio actual.
- Una revisión práctica de que los pasos descritos pueden seguirse realmente.
- Una explicación breve de qué errores había en la documentación anterior y cómo los has corregido.
