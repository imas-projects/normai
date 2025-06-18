from openai import OpenAI
import json
import re
from risks.models import RiskIdentification, RiskEvaluation
from django.conf import settings
from collections import Counter
from openai import OpenAIError

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

        # Limpiar posibles delimitadores markdown
        clean_content = re.sub(r'^```json\s*|\s*```$', '', content).strip()

        suggestions = json.loads(clean_content)

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
        print("Contenido no parseable:", repr(clean_content))
        return []
    except Exception as e:
        print("Error al generar sugerencia IA:", str(e))
        return []



def suggest_controls(risk_id, max_controls=3):
    try:
        risk = RiskIdentification.objects.select_related("area").get(id=risk_id)
    except RiskIdentification.DoesNotExist:
        return {"error": "No se encontró el riesgo especificado."}

    similar_evaluations = RiskEvaluation.objects.filter(
        risk__area=risk.area,
        risk__activity_name=risk.activity_name,
        risk__identified_risk=risk.identified_risk
    )

    if similar_evaluations.exists():
        historical_lines = [
            f"""Área: {eval.risk.area.name} | Actividad: {eval.risk.activity_name} | 
Riesgo: {eval.risk.identified_risk} | Consecuencias: {eval.risk.consequences} | 
Controles preventivos: {eval.current_preventive_controls or "N/A"} | 
Controles de detección: {eval.current_detection_controls or "N/A"} | 
Severidad: {eval.severity}, Ocurrencia: {eval.occurrence}, Detección: {eval.detection} | 
Nivel: {eval.risk_level.name}"""
            for eval in similar_evaluations[:10]
        ]

        prompt = f"""
Eres un experto en gestión de calidad y riesgos bajo ISO 9001:2015 en industria aeroespacial.

Con base en evaluaciones anteriores, sugiere exactamente:
- 3 controles preventivos
- 3 controles de detección

Histórico:
{chr(10).join(historical_lines)}

Nueva entrada:
Área: {risk.area.name}
Actividad: {risk.activity_name}
Riesgo: {risk.identified_risk}
Consecuencias: {risk.consequences}

Responde SOLO con un objeto JSON, sin explicaciones, sin texto adicional.
Formato:
{{"preventive_controls": [...], "detection_controls": [...]}}
"""
    else:
        prompt = f"""
Eres un consultor experto en calidad ISO 9001:2015 para riesgos operativos.

Dado:
Área: {risk.area.name}
Actividad: {risk.activity_name}
Riesgo: {risk.identified_risk}
Consecuencias: {risk.consequences}

Sugiere exactamente 3 controles preventivos y 3 de detección.

Responde SOLO con un objeto JSON, sin texto adicional. Formato:
{{"preventive_controls": [...], "detection_controls": [...]}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
        )

        content = response.choices[0].message.content.strip()

        # Extraer el primer bloque JSON válido
        match = re.search(r"\{.*?\}", content, re.DOTALL)
        if not match:
            print("Respuesta no contiene JSON válido:", content)
            return {"error": "La IA no devolvió un JSON válido."}

        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            print("No se pudo interpretar el JSON:", match.group())
            return {"error": "No se pudo interpretar la respuesta de IA."}

        return {
            "preventive_controls": data.get("preventive_controls", [])[:max_controls],
            "detection_controls": data.get("detection_controls", [])[:max_controls]
        }

    except Exception as e:
        return {"error": str(e)}

def suggest_rating_ranges(risk_id, preventive_controls, detection_controls):
    try:
        risk = RiskIdentification.objects.select_related("area").get(id=risk_id)
    except RiskIdentification.DoesNotExist:
        return {"error": "No se encontró el riesgo especificado."}

    similar_evaluations = RiskEvaluation.objects.filter(
        risk__area=risk.area,
        risk__activity_name=risk.activity_name,
        risk__identified_risk=risk.identified_risk
    )

    controls_text = f"""
Controles preventivos escritos por el usuario:
{chr(10).join(preventive_controls)}

Controles de detección escritos por el usuario:
{chr(10).join(detection_controls)}
"""

    if similar_evaluations.exists():
        historical_lines = [
            f"""Área: {eval.risk.area.name} | Actividad: {eval.risk.activity_name} | 
Riesgo: {eval.risk.identified_risk} | Consecuencias: {eval.risk.consequences} | 
Controles preventivos: {eval.current_preventive_controls or "N/A"} | 
Controles de detección: {eval.current_detection_controls or "N/A"} | 
Severidad: {eval.severity}, Ocurrencia: {eval.occurrence}, Detección: {eval.detection} | 
Nivel: {eval.risk_level.name}"""
            for eval in similar_evaluations[:10]
        ]
        prompt = f"""
Eres un experto en análisis de riesgos ISO 9001:2015.

Basándote en el histórico y los controles introducidos, sugiere rangos adecuados para:
- Severidad
- Ocurrencia
- Detección

Histórico:
{chr(10).join(historical_lines)}

{controls_text}

Devuélvelo como JSON:
{{"severity_range": "...", "occurrence_range": "...", "detection_range": "..."}}        
"""
    else:
        prompt = f"""
Eres un consultor en riesgos operativos ISO 9001:2015.

Dado:
Área: {risk.area.name}
Actividad: {risk.activity_name}
Riesgo: {risk.identified_risk}
Consecuencias: {risk.consequences}

{controls_text}

Sugiere rangos aproximados (ej: "entre 2 y 5") para:
- Severidad
- Ocurrencia
- Detección

Formato JSON:
{{"severity_range": "...", "occurrence_range": "...", "detection_range": "..."}}        
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
        )

        raw_content = response.choices[0].message.content.strip()
        print("🔍 Respuesta cruda de IA:", raw_content)

        # Extraer solo el JSON de la respuesta
        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if not match:
            return {"error": "No se pudo interpretar la respuesta de IA."}

        data = json.loads(match.group(0))

        return {
            "severity_range": data.get("severity_range", ""),
            "occurrence_range": data.get("occurrence_range", ""),
            "detection_range": data.get("detection_range", "")
        }

    except json.JSONDecodeError:
        return {"error": "No se pudo interpretar la respuesta de IA."}
    except Exception as e:
        return {"error": str(e)}

def suggest_risk_level(risk_id, preventive_controls, detection_controls, severity, occurrence, detection):
    try:
        risk = RiskIdentification.objects.select_related("area").get(id=risk_id)
    except RiskIdentification.DoesNotExist:
        return {"error": "No se encontró el riesgo especificado."}

    similar_evaluations = RiskEvaluation.objects.filter(
        risk__area=risk.area,
        risk__activity_name=risk.activity_name,
        risk__identified_risk=risk.identified_risk
    )

    controls_text = f"""
Controles preventivos:
{chr(10).join(preventive_controls)}

Controles de detección:
{chr(10).join(detection_controls)}

Valores ingresados:
Severidad: {severity}
Ocurrencia: {occurrence}
Detección: {detection}
"""

    if similar_evaluations.exists():
        historical_lines = [
            f"""Área: {eval.risk.area.name} | Actividad: {eval.risk.activity_name} | 
Riesgo: {eval.risk.identified_risk} | Consecuencias: {eval.risk.consequences} | 
Controles preventivos: {eval.current_preventive_controls or "N/A"} | 
Controles de detección: {eval.current_detection_controls or "N/A"} | 
Severidad: {eval.severity}, Ocurrencia: {eval.occurrence}, Detección: {eval.detection} | 
Nivel: {eval.risk_level.name}"""
            for eval in similar_evaluations[:10]
        ]
        prompt = f"""
Eres un analista experto en riesgos bajo ISO 9001:2015.

Basándote en las entradas del usuario y en el histórico, sugiere el **nivel de riesgo** más probable: 🟥, 🟨, 🟩.

Histórico:
{chr(10).join(historical_lines)}

{controls_text}

Devuelve solo:
{{"risk_level": "🟨 Riesgo Moderado"}}
"""
    else:
        prompt = f"""
Eres un experto consultor en evaluación de riesgos ISO 9001:2015.

Dado:
Área: {risk.area.name}
Actividad: {risk.activity_name}
Riesgo: {risk.identified_risk}
Consecuencias: {risk.consequences}

{controls_text}

Estima el nivel de riesgo general (🟥, 🟨, 🟩) según tu experiencia.

Formato JSON:
{{"risk_level": "🟥 Riesgo Alto"}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )

        raw_response = response.choices[0].message.content.strip()
        print("Respuesta IA cruda:", raw_response)  # Útil para debug

        try:
            # Primero intenta decodificar directamente
            data = json.loads(raw_response)
        except json.JSONDecodeError:
            # Si falla, intenta extraer el JSON del texto completo
            json_text_match = re.search(r'\{[^}]*risk_level[^}]*\}', raw_response, re.DOTALL)
            if not json_text_match:
                return {"error": f"No se encontró un objeto JSON válido en la respuesta: {raw_response}"}
            try:
                data = json.loads(json_text_match.group(0))
            except json.JSONDecodeError as e:
                return {"error": f"Error al decodificar JSON: {str(e)} | Respuesta: {raw_response}"}

        return {"risk_level": data.get("risk_level", "")}

    except Exception as e:
        return {"error": str(e)}


def suggest_treatment_action(risk_id, max_results=1):
    """
    Sugiere acciones correctivas de tratamiento para un riesgo específico basado en:
    - Datos históricos del riesgo y sus evaluaciones
    - Criterios de la norma ISO 9001:2015

    Retorna una lista con diccionarios con la clave "treatment_action" con la acción sugerida.
    """

    try:
        risk = RiskIdentification.objects.get(id=risk_id)
        evaluations = risk.evaluations.all()
    except RiskIdentification.DoesNotExist:
        return []

    # Construir contexto histórico con ejemplos similares (máx 5)
    historical_treatments = []
    for other_risk in RiskIdentification.objects.filter(area=risk.area).exclude(id=risk.id)[:5]:
        for eval in other_risk.evaluations.all():
            historical_treatments.append(
                f"Área: {other_risk.area.name} | Riesgo: {other_risk.description} | "
                f"Evaluación: Severidad {eval.severity}, Ocurrencia {eval.occurrence}, Detección {eval.detection}, "
                f"Nivel de riesgo {eval.risk_level}."
            )

    historical_text = "\n".join(historical_treatments) if historical_treatments else "No hay datos históricos relevantes."

    # Info del riesgo actual y evaluaciones
    risk_info = (
        f"Descripción del riesgo: {risk.description}\n"
        f"Área: {risk.area.name}\n"
        f"Tipo: {risk.risk_type}\n"
        f"Causa: {risk.cause}\n"
        f"Impacto: {risk.impact}\n"
        f"Probabilidad: {risk.probability}\n"
    )

    eval_info = ""
    if evaluations.exists():
        for i, ev in enumerate(evaluations, 1):
            eval_info += (
                f"Evaluación {i}:\n"
                f"  Severidad: {ev.severity}\n"
                f"  Ocurrencia: {ev.occurrence}\n"
                f"  Detección: {ev.detection}\n"
                f"  Nivel de riesgo: {ev.risk_level}\n"
                f"  Controles preventivos actuales: {ev.current_preventive_controls or 'Ninguno'}\n"
                f"  Controles de detección actuales: {ev.current_detection_controls or 'Ninguno'}\n"
            )
    else:
        eval_info = "No hay evaluaciones disponibles para este riesgo."

    prompt = f"""
Eres un experto en gestión de riesgos y en la norma ISO 9001:2015.

Con base en la siguiente información, sugiere hasta {max_results} acciones correctivas de tratamiento para el riesgo indicado.
La sugerencia debe ser clara, precisa y en lenguaje natural.

Información histórica de riesgos similares:
{historical_text}

Información del riesgo actual:
{risk_info}

Evaluaciones asociadas:
{eval_info}

Por favor responde ÚNICAMENTE con una lista JSON con {max_results} objetos con la clave EXACTA "treatment_action", por ejemplo:

[
  {{
    "treatment_action": "Implementar capacitación específica en seguridad de la información para el área afectada."
  }}
]
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=400,
        )

        content = response.choices[0].message['content'].strip()
        print("Respuesta cruda de IA:", repr(content))

        suggestions = json.loads(content)

        if isinstance(suggestions, list) and all(isinstance(item, dict) for item in suggestions):
            return [
                {"treatment_action": item.get("treatment_action", "").strip()}
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
