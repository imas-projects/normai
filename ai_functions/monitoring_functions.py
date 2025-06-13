from openai import OpenAI
import json
from risks.models import RiskIdentification
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def suggest_risk_fields(area_name, activity_name, max_results=3):
    """
    Sugiere automáticamente hasta 3 riesgos y sus consecuencias basándose en:
    - El área seleccionada
    - El nombre de la actividad introducida
    - Riesgos existentes en la base de datos
    - Criterios de ISO 9001:2015

    Retorna una lista de diccionarios como:
    [
        {"identified_risk": "...", "consequences": "..."},
        ...
    ]
    """

    historical_risks = RiskIdentification.objects.select_related('area').all()

    if not historical_risks.exists():
        prompt = f"""
Eres un experto en gestión de calidad ISO 9001:2015 en industria aeroespacial.
Sugiéreme TRES posibles riesgos identificados y sus consecuencias según:

Área: {area_name}
Actividad: {activity_name}

Por favor responde ÚNICAMENTE con una lista JSON de 3 objetos, cada uno con las claves EXACTAS: "identified_risk" y "consequences".

Ejemplo:
[
  {{
    "identified_risk": "Riesgo más crítico",
    "consequences": "Consecuencias más graves"
  }},
  {{
    "identified_risk": "Riesgo intermedio",
    "consequences": "Consecuencias intermedias"
  }},
  {{
    "identified_risk": "Riesgo menos crítico",
    "consequences": "Consecuencias menos graves"
  }}
]
        """
    else:
        examples = []
        for risk in historical_risks[:10]:  # máximo 10 ejemplos
            examples.append(
                f"Área: {risk.area.name} | Actividad: {risk.activity_name} | "
                f"Riesgo: {risk.identified_risk} | Consecuencias: {risk.consequences}"
            )

        prompt = f"""
Eres un asistente experto en gestión de calidad bajo la norma ISO 9001:2015 aplicada al sector aeroespacial.
Dado un área y una actividad, sugiere TRES riesgos identificados y sus consecuencias en orden de importancia (el más crítico primero),
basándote en:

- Historial de riesgos reales
- Estándares de ISO 9001:2015
- Conocimientos expertos del sector

Histórico de riesgos:
{chr(10).join(examples)}

Nueva entrada:
Área: {area_name}
Actividad: {activity_name}

Por favor responde ÚNICAMENTE con una lista JSON de 3 objetos, cada uno con las claves EXACTAS: "identified_risk" y "consequences".

Ejemplo:
[
  {{
    "identified_risk": "Riesgo más crítico",
    "consequences": "Consecuencias más graves"
  }},
  {{
    "identified_risk": "Riesgo intermedio",
    "consequences": "Consecuencias intermedias"
  }},
  {{
    "identified_risk": "Riesgo menos crítico",
    "consequences": "Consecuencias menos graves"
  }}
]
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        print("Respuesta cruda de IA:", repr(content))  

        suggestions = json.loads(content)

        if isinstance(suggestions, list) and all(isinstance(item, dict) for item in suggestions):
            return [
                {
                    "identified_risk": item.get("identified_risk", "").strip(),
                    "consequences": item.get("consequences", "").strip()
                }
                for item in suggestions[:max_results]
            ]

        print("Formato inesperado:", type(suggestions))
        return []

    except json.JSONDecodeError as jde:
        print("Error de JSONDecode:", str(jde))
        print("Contenido no parseable:", repr(content))
        return []
    except Exception as e:
        print("Error al generar sugerencia IA:", str(e))
        return []
