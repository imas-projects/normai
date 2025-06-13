from openai import OpenAI
import json
from risks.models import RiskIdentification, RiskEvaluation
from django.conf import settings
from collections import Counter

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



def suggest_evaluation_fields(risk_id, max_controls=3):
    """
    Genera sugerencias de IA para una evaluación de riesgo basada en el RiskIdentification asociado.

    Retorna un dict con:
    - preventive_controls: lista de 3 sugerencias
    - detection_controls: lista de 3 sugerencias
    - severity_range: texto con rango sugerido
    - occurrence_range: texto con rango sugerido
    - detection_range: texto con rango sugerido
    - risk_level: texto coloreado con nivel sugerido (🟥 High, 🟨 Moderate, 🟩 Low)
    """

    try:
        risk = RiskIdentification.objects.select_related("area").get(id=risk_id)
    except RiskIdentification.DoesNotExist:
        return {
            "error": "No se encontró el riesgo especificado."
        }

    # Obtener histórico similar
    similar_evaluations = RiskEvaluation.objects.filter(
        risk__area=risk.area,
        risk__activity_name=risk.activity_name,
        risk__identified_risk=risk.identified_risk
    ).select_related("risk_level")

    # Construir prompt
    if similar_evaluations.exists():
        historical_lines = []
        for eval in similar_evaluations[:10]:
            historical_lines.append(
                f"""Área: {eval.risk.area.name} | Actividad: {eval.risk.activity_name} | 
Riesgo: {eval.risk.identified_risk} | Consecuencias: {eval.risk.consequences} | 
Controles preventivos: {eval.current_preventive_controls or "N/A"} | 
Controles de detección: {eval.current_detection_controls or "N/A"} | 
Severidad: {eval.severity}, Ocurrencia: {eval.occurrence}, Detección: {eval.detection} | 
Nivel: {eval.risk_level.name}"""
            )
        prompt = f"""
Eres un experto en gestión de calidad y riesgos bajo ISO 9001:2015 en industria aeroespacial.

Con base en evaluaciones anteriores, sugiere:
- 3 controles preventivos
- 3 controles de detección
- Rangos sugeridos de severidad, ocurrencia y detección (ej: entre 6 y 8)
- Nivel de riesgo: High 🟥, Moderate 🟨, Low 🟩

Histórico:
{chr(10).join(historical_lines)}

Nueva entrada:
Área: {risk.area.name}
Actividad: {risk.activity_name}
Riesgo: {risk.identified_risk}
Consecuencias: {risk.consequences}

Devuélvelo como un JSON con claves:
"preventive_controls", "detection_controls", 
"severity_range", "occurrence_range", "detection_range", "risk_level"

Ejemplo:
{{
  "preventive_controls": ["Control 1", "Control 2", "Control 3"],
  "detection_controls": ["Control A", "Control B", "Control C"],
  "severity_range": "Severidad sugerida entre 6 y 8",
  "occurrence_range": "Ocurrencia sugerida entre 4 y 6",
  "detection_range": "Detección sugerida entre 3 y 5",
  "risk_level": "🟨 Riesgo Moderado"
}}
        """
    else:
        prompt = f"""
Eres un consultor experto en calidad ISO 9001:2015 para riesgos operativos.

Dado:
Área: {risk.area.name}
Actividad: {risk.activity_name}
Riesgo: {risk.identified_risk}
Consecuencias: {risk.consequences}

Sugiere:
- 3 controles preventivos
- 3 controles de detección
- Rangos sugeridos para severidad, ocurrencia y detección
- Nivel estimado de riesgo con color emoji: 🟥, 🟨, 🟩

Formato JSON con claves:
"preventive_controls", "detection_controls", 
"severity_range", "occurrence_range", "detection_range", "risk_level"
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        print("IA RESPONSE:", content)

        data = json.loads(content)

        return {
            "preventive_controls": data.get("preventive_controls", [])[:max_controls],
            "detection_controls": data.get("detection_controls", [])[:max_controls],
            "severity_range": data.get("severity_range", ""),
            "occurrence_range": data.get("occurrence_range", ""),
            "detection_range": data.get("detection_range", ""),
            "risk_level": data.get("risk_level", "")
        }

    except json.JSONDecodeError:
        return {"error": "No se pudo interpretar la respuesta de IA."}
    except Exception as e:
        return {"error": f"Error al consultar IA: {str(e)}"}



