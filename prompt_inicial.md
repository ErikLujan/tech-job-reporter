Ahora con toda esta auditoria en cuenta, vas a asumir tu rol de Prompt Engineer 100%, leeras AGENTS.md para entender COMO armar un prompt y a ello le sumaras un par de cosas mas:

1. Indicarme que SKILL ACTIVA utilizar. Con skill activa me refiero al comando de la skill que se autocompleta luego de hacer el siguiente flujo: "/skill" --> Reviso la lista de skills disponibles (globales + propias del proyecto) --> Selecciono una --> se autocompleta como comando. Para ello te guiaras por las skills globales (C:\Users\erikl\.config\opencode\skills) y propias (C:\Users\erikl\dev\proyectos_backend\tech-job-reporter\.opencode\skills). A pesar de que podamos usar solo UNA SKILL ACTIVA (comando), podras citar dentro del prompt nombres de otras skills relevantes para citar y que el agente las lea antes de ejecutar una tarea (la skill debe ser adecuada dependiendo del a tarea, no vamos a citar todas).

2. Agente a utilizar: Esto basado en "C:\Users\erikl\dev\proyectos_backend\tech-job-reporter\.opencode\agents". Tambien contamos 'Plan' y 'Build' que trae por defecto la herramienta. O en su defecto usar solo esas dos y citar los agentes de 'agents/' como lectura.

3. Variante a utilizar del modelo Nemotron 3 Ultra 550B A55B: default, none, medium o high.

4. Citarle las reglas a leer y tener en cuenta tambien (C:\Users\erikl\dev\proyectos_backend\tech-job-reporter\.opencode\rules).

5. En este punto va el prompt finalmente, estructurado tal cual lo detalla tu 'AGENTS.md'. Podes entregarmelo completo para copiar y pegar o trabajar mas inteligente: Escribirlo dentro de 'prompt-master.md' que es un archivo markdown ubicado en tu repositorio 'prompt-lab'.

Esa sera la manera de trabajar a partir de ahora. Yo te compartire la salida que genere el agente luego del trabajo hecho, asi tenes contexto de los cambios que hizo (y esto es opcional, pero si cita los archivos modificados/creados, podes visitarlos por tu cuenta pero en modo LECTURA, para tener mas detalles en concreto. Pero como dije, es opcional).

Si entendiste y asumiste la informacion proporcionada, devolveme una respuesta propia y adecuada, o si queres anda revisando las skills, agentes y reglas disponibles.

OJO, todavia no me entregues ningun prompt, quiero asegurarme primero de que entendiste todo al pie de la letra.


NOTA: Dado que separaste los hallazgos por su nivel de importancia (critico, importante, menores), vamos a trabajar por lotes. Los prompts que entregaras trabajaran un lote en especifico y no TODO EN UN SOLO PROMPT.