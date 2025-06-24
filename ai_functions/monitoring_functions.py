from openai import OpenAI
import openai
import json
import re
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from collections import defaultdict
from django.db.models import Count
from risks.models import RiskIdentification, RiskEvaluation, ContingencyPlan
from communications.models import CommunicationTable, CommunicationMessage
from processes.models import Process
from audits.models import (
    AnnualProgram, AuditProgramHeader,
    AnnualPlanAuditor, AnnualPlanAudited, AnnualPlan,
    User, Findings, ProcessRequirement, Checklist, AuditorEvaluation, AuditReport
)
from django.contrib.auth.models import User  
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
Nivel: {eval.risk_level}"""  # Aquí sin .name
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
Nivel: {eval.risk_level}"""
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
Nivel: {eval.risk_level}"""
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
                f"Área: {other_risk.area.name} | Riesgo: {other_risk.identified_risk} | "
                f"Evaluación: Severidad {eval.severity}, Ocurrencia {eval.occurrence}, Detección {eval.detection}, "
                f"Nivel de riesgo {eval.risk_level}."
            )

    historical_text = "\n".join(historical_treatments) if historical_treatments else "No hay datos históricos relevantes."

    # Info del riesgo actual y evaluaciones
    risk_info = (
        f"Riesgo identificado: {risk.identified_risk}\n"
        f"Área: {risk.area.name}\n"
        f"Actividad: {risk.activity_name}\n"
        f"Consecuencias: {risk.consequences}\n"
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()
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


def suggest_contingency_actions(risk_id, max_results=3):
    """
    Sugiere acciones de contingencia para un riesgo específico, basándose en:
    - La identificación, evaluación y tratamiento del riesgo.
    - Datos históricos de riesgos similares.
    - Norma ISO 9001:2015 (Cláusulas 6.1 y 8.4).

    Retorna una lista de diccionarios con la clave "contingency_action".
    """

    def clean_json_markdown_block(text):
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        return text

    try:
        risk = RiskIdentification.objects.get(id=risk_id)
        evaluations = risk.evaluations.all()
        treatments = risk.treatments.all()
    except RiskIdentification.DoesNotExist:
        return []

    # Información actual del riesgo
    risk_info = (
        f"Riesgo identificado: {risk.identified_risk}\n"
        f"Área: {risk.area.name}\n"
        f"Actividad: {risk.activity_name}\n"
        f"Consecuencias: {risk.consequences or 'No especificado'}\n"
    )

    eval_info = ""
    for i, ev in enumerate(evaluations, 1):
        eval_info += (
            f"Evaluación {i}:\n"
            f"  Severidad: {ev.severity}\n"
            f"  Ocurrencia: {ev.occurrence}\n"
            f"  Detección: {ev.detection}\n"
            f"  Nivel de riesgo: {ev.risk_level}\n"
            f"  Controles preventivos: {ev.current_preventive_controls or 'Ninguno'}\n"
            f"  Controles de detección: {ev.current_detection_controls or 'Ninguno'}\n"
        ) or "No hay evaluaciones disponibles para este riesgo."

    treatment_info = ""
    for i, tr in enumerate(treatments, 1):
        treatment_info += (
            f"Tratamiento {i}:\n"
            f"  Acción: {tr.treatment_action}\n"
            f"  Fecha objetivo: {tr.target_date}\n"
            f"  Fecha real: {tr.actual_date}\n"
        )
    if not treatment_info:
        treatment_info = "No hay tratamientos registrados para este riesgo."

    # Información histórica
    historical_context = ""

    for other_risk in RiskIdentification.objects.exclude(id=risk.id)[:5]:
        other_evals = other_risk.evaluations.all()
        other_treatments = other_risk.treatments.all()
        other_plans = ContingencyPlan.objects.filter(risk=other_risk)

        historical_context += (
            f"Área: {other_risk.area.name} | Riesgo: {other_risk.identified_risk}\n"
        )

        for ev in other_evals:
            historical_context += (
                f"  Evaluación - Severidad: {ev.severity}, Ocurrencia: {ev.occurrence}, "
                f"Detección: {ev.detection}, Nivel: {ev.risk_level}\n"
            )
        for tr in other_treatments:
            historical_context += f"  Tratamiento: {tr.treatment_action}\n"

        for plan in other_plans:
            actions = ", ".join([dict(plan.ACTION_CHOICES).get(a) for a in plan.contingency_actions])
            historical_context += f"  Acciones de contingencia aplicadas: {actions}\n"

        historical_context += "\n"

    if not historical_context:
        historical_context = "No hay registros históricos disponibles para comparar."

    # Prompt para la IA
    prompt = f"""
Eres un experto en gestión de riesgos conforme a la norma ISO 9001:2015, en particular las cláusulas 6.1 y 8.4.

Con base en la siguiente información, recomienda {max_results} acciones de contingencia priorizadas, seleccionadas de la siguiente lista predefinida:

- Establecer procedimientos alternativos
- Identificar proveedores sustitutos
- Asignar personal de respaldo
- Mantener inventarios de emergencia
- Implementar redundancias tecnológicas
- Establecer protocolos de comunicación de crisis
- Realizar simulacros y pruebas periódicas
- Contratar seguros o coberturas específicas
- Externalizar temporalmente operaciones críticas
- Crear manuales de operación ante fallos

Información del riesgo actual:
{risk_info}

Evaluaciones asociadas:
{eval_info}

Tratamientos aplicados:
{treatment_info}

Historial de riesgos similares:
{historical_context}

Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON. Ejemplo:
[
  {{
    "contingency_action": "Mantener inventarios de emergencia"
  }},
  {{
    "contingency_action": "Asignar personal de respaldo"
  }},
  {{
    "contingency_action": "Establecer protocolos de comunicación de crisis"
  }}
]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()
        print("Respuesta IA:", content)

        content = clean_json_markdown_block(content)  # Limpieza del bloque Markdown

        suggestions = json.loads(content)

        if isinstance(suggestions, list) and all("contingency_action" in item for item in suggestions):
            return suggestions[:max_results]

        return []

    except json.JSONDecodeError as e:
        print("Error al decodificar JSON:", e)
        print("Contenido recibido:", repr(content))
        return []
    except Exception as e:
        print("Error al generar sugerencia IA:", e)
        return []


def suggest_reevaluation_rating_ranges(risk_id):
    try:
        risk = RiskIdentification.objects.select_related("area").get(id=risk_id)
    except RiskIdentification.DoesNotExist:
        return {"error": "No se encontró el riesgo especificado."}

    # Información base del riesgo
    risk_info = (
        f"Riesgo identificado: {risk.identified_risk}\n"
        f"Área: {risk.area.name}\n"
        f"Actividad: {risk.activity_name}\n"
        f"Consecuencias: {risk.consequences or 'No especificado'}\n"
    )

    # Evaluaciones iniciales del riesgo actual
    evaluations = risk.evaluations.all()
    eval_info = ""
    for i, ev in enumerate(evaluations, 1):
        eval_info += (
            f"Evaluación {i}:\n"
            f"  Severidad: {ev.severity}\n"
            f"  Ocurrencia: {ev.occurrence}\n"
            f"  Detección: {ev.detection}\n"
            f"  Nivel de riesgo: {ev.risk_level}\n"
        )

    if not eval_info:
        eval_info = "No hay evaluaciones disponibles"

    # Tratamientos del riesgo actual
    treatments = risk.treatments.all()
    treatment_info = ""
    for i, tr in enumerate(treatments, 1):
        treatment_info += (
            f"Tratamiento {i}:\n"
            f"  Acción: {tr.treatment_action}\n"
            f"  Fecha objetivo: {tr.target_date}\n"
            f"  Fecha real: {tr.actual_date}\n"
        )

    if not treatment_info:
        treatment_info = "No hay tratamientos registrados para este riesgo."

    # Planes de contingencia del riesgo actual
    contingency_plans = ContingencyPlan.objects.filter(risk=risk)
    contingency_info = ""
    for plan in contingency_plans:
        actions = ", ".join([dict(plan.ACTION_CHOICES).get(code) for code in plan.contingency_actions])
        contingency_info += f"Acciones de contingencia aplicadas: {actions}\n"

    if not contingency_info:
        contingency_info = "No hay acciones de contingencia registradas."

    # Contexto histórico de otros riesgos
    historical_context = ""
    other_risks = RiskIdentification.objects.exclude(id=risk.id)[:5]

    for other_risk in other_risks:
        historical_context += (
            f"Área: {other_risk.area.name} | Riesgo: {other_risk.identified_risk}\n"
        )

        for ev in other_risk.evaluations.all():
            historical_context += (
                f"  Evaluación - Severidad: {ev.severity}, Ocurrencia: {ev.occurrence}, "
                f"Detección: {ev.detection}, Nivel: {ev.risk_level}\n"
            )

        for tr in other_risk.treatments.all():
            historical_context += f"  Tratamiento: {tr.treatment_action}\n"

        for plan in ContingencyPlan.objects.filter(risk=other_risk):
            actions = ", ".join([dict(plan.ACTION_CHOICES).get(a) for a in plan.contingency_actions])
            historical_context += f"  Acciones de contingencia aplicadas: {actions}\n"

        for ree in other_risk.reevaluations.all():
            historical_context += (
                f"  Reevaluación - Severidad: {ree.severity}, Ocurrencia: {ree.occurrence}, "
                f"Detección: {ree.detection}, Nivel: {ree.risk_level}\n"
            )

        historical_context += "\n"

    if not historical_context:
        historical_context = "No hay registros históricos disponibles para comparar."

    # Construcción del prompt para IA (sin controles preventivos/detección)
    prompt = f"""
Eres un experto en gestión de riesgos conforme a la norma ISO 9001:2015.

Basándote en la siguiente información, sugiere rangos recomendados para:
- Severidad
- Ocurrencia
- Detección

Información del riesgo:
{risk_info}

Evaluaciones iniciales:
{eval_info}

Tratamientos aplicados:
{treatment_info}

Planes de contingencia:
{contingency_info}

Contexto histórico de otros riesgos:
{historical_context}

Responde únicamente en el siguiente formato JSON:
{{
  "severity_range": "entre 2 y 5",
  "occurrence_range": "entre 3 y 6",
  "detection_range": "entre 4 y 8"
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        raw_content = response.choices[0].message.content.strip()
        print("Respuesta IA cruda:", raw_content)

        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if not match:
            return {"error": "No se encontró un JSON válido en la respuesta."}

        data = json.loads(match.group(0))
        return {
            "severity_range": data.get("severity_range", ""),
            "occurrence_range": data.get("occurrence_range", ""),
            "detection_range": data.get("detection_range", "")
        }

    except Exception as e:
        return {"error": str(e)}

def suggest_reevaluation_risk_level(risk_id, severity, occurrence, detection):
    try:
        risk = RiskIdentification.objects.select_related("area").get(id=risk_id)
    except RiskIdentification.DoesNotExist:
        return {"error": "No se encontró el riesgo especificado."}

    # Información del riesgo
    risk_info = (
        f"Riesgo identificado: {risk.identified_risk}\n"
        f"Área: {risk.area.name}\n"
        f"Actividad: {risk.activity_name}\n"
        f"Consecuencias: {risk.consequences or 'No especificado'}\n"
    )

    # Evaluaciones propias del riesgo
    evaluations = risk.evaluations.all()
    eval_info = ""
    for i, ev in enumerate(evaluations, 1):
        eval_info += (
            f"Evaluación {i}:\n"
            f"  Severidad: {ev.severity}\n"
            f"  Ocurrencia: {ev.occurrence}\n"
            f"  Detección: {ev.detection}\n"
            f"  Nivel de riesgo: {ev.risk_level}\n"
            f"  Controles preventivos: {ev.current_preventive_controls or 'Ninguno'}\n"
            f"  Controles de detección: {ev.current_detection_controls or 'Ninguno'}\n"
        )

    # Tratamientos del riesgo
    treatments = risk.treatments.all()
    treatment_info = ""
    for i, tr in enumerate(treatments, 1):
        treatment_info += (
            f"Tratamiento {i}:\n"
            f"  Acción: {tr.treatment_action}\n"
            f"  Fecha objetivo: {tr.target_date}\n"
            f"  Fecha real: {tr.actual_date}\n"
        )

    # Planes de contingencia
    contingency_plans = ContingencyPlan.objects.filter(risk=risk)
    contingency_info = ""
    for plan in contingency_plans:
        actions = ", ".join([dict(plan.ACTION_CHOICES).get(code) for code in plan.contingency_actions])
        contingency_info += f"Acciones de contingencia aplicadas: {actions}\n"

    # Contexto histórico (otros riesgos similares)
    historical_context = ""
    for other_risk in RiskIdentification.objects.exclude(id=risk.id)[:5]:
        other_evals = other_risk.evaluations.all()
        other_treatments = other_risk.treatments.all()
        other_plans = ContingencyPlan.objects.filter(risk=other_risk)
        other_reevs = other_risk.reevaluations.all()

        historical_context += (
            f"Área: {other_risk.area.name} | Riesgo: {other_risk.identified_risk}\n"
        )

        for ev in other_evals:
            historical_context += (
                f"  Evaluación - Severidad: {ev.severity}, Ocurrencia: {ev.occurrence}, "
                f"Detección: {ev.detection}, Nivel: {ev.risk_level}\n"
            )
        for tr in other_treatments:
            historical_context += f"  Tratamiento: {tr.treatment_action}\n"

        for plan in other_plans:
            actions = ", ".join([dict(plan.ACTION_CHOICES).get(a) for a in plan.contingency_actions])
            historical_context += f"  Acciones de contingencia aplicadas: {actions}\n"

        for ree in other_reevs:
            historical_context += (
                f"  Reevaluación - Severidad: {ree.severity}, Ocurrencia: {ree.occurrence}, "
                f"Detección: {ree.detection}, Nivel: {ree.risk_level}\n"
            )

        historical_context += "\n"

    if not historical_context:
        historical_context = "No hay registros históricos disponibles para comparar."

    # Valores actuales del usuario
    user_values = f"""
Valores reevaluados ingresados:
- Severidad: {severity}
- Ocurrencia: {occurrence}
- Detección: {detection}
"""

    # Construcción del prompt para IA
    prompt = f"""
Eres un analista experto en riesgos según la norma ISO 9001:2015.

Utiliza toda la siguiente información para **estimar el nivel de riesgo (🟥, 🟨, 🟩)** más adecuado tras una reevaluación.

Información del riesgo:
{risk_info}

Evaluaciones previas:
{eval_info or "Sin evaluaciones"}

Tratamientos aplicados:
{treatment_info or "Sin tratamientos"}

Acciones de contingencia:
{contingency_info or "Sin acciones registradas"}

Contexto histórico de otros riesgos:
{historical_context}

{user_values}

Responde en formato JSON como este:
{{"risk_level": "🟥 Riesgo Alto"}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )

        raw_content = response.choices[0].message.content.strip()
        print("Respuesta IA cruda:", raw_content)

        match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if not match:
            return {"error": "No se encontró JSON válido."}

        data = json.loads(match.group(0))
        return {"risk_level": data.get("risk_level", "")}

    except Exception as e:
        return {"error": str(e)}



def generate_communication_flow_map(table_id):
    """
    Genera un grafo de flujo de comunicación a partir de una tabla específica.
    Incluye nodos, conexiones y una inferencia IA para identificar problemas o patrones,
    según cláusulas de la norma ISO 9001:2015.
    """
    try:
        table = CommunicationTable.objects.select_related('emiter').get(id=table_id)
        messages = CommunicationMessage.objects.select_related('receiver', 'message', 'periodicity').filter(table=table)

        if not messages.exists():
            return {
                "nodes": [],
                "edges": [],
                "ia_insights": {
                    "patterns": [],
                    "weaknesses": [],
                    "recommendations": ["No se encontraron mensajes en esta tabla."]
                }
            }

        edges = []
        nodes = set()
        ia_examples = []

        for msg in messages:
            emiter = table.emiter
            receiver = msg.receiver
            msg_name = msg.message.name
            freq = msg.periodicity.name

            if emiter and receiver:
                edges.append({
                    "from": f"{emiter.name} ({emiter.area.name})",
                    "to": f"{receiver.name} ({receiver.area.name})",
                    "label": msg_name,
                    "frequency": freq
                })

                nodes.add(f"{emiter.name} ({emiter.area.name})")
                nodes.add(f"{receiver.name} ({receiver.area.name})")

                ia_examples.append(f"De: {emiter.name} → A: {receiver.name} | Frecuencia: {freq} | Mensaje: {msg_name}")

        prompt = f"""
Eres un experto en auditoría interna y mejora continua según la norma ISO 9001:2015 (cláusulas 4.4.1 y 5.3).
A continuación se muestra un resumen del flujo de comunicaciones internas entre procesos y puestos en una organización industrial:

{chr(10).join(ia_examples)}

Tu tarea:
1. Detecta patrones (flujo excesivo o escaso entre ciertas áreas).
2. Sugiere posibles debilidades o barreras de comunicación.
3. Da una recomendación de mejora concreta según la norma ISO.

Por favor, responde exclusivamente con un JSON que contenga las claves: "patterns", "weaknesses" y "recommendations". Cada una debe ser una lista de strings.

Ejemplo de respuesta JSON:

{{
  "patterns": ["Patrón 1", "Patrón 2"],
  "weaknesses": ["Debilidad 1", "Debilidad 2"],
  "recommendations": ["Recomendación 1", "Recomendación 2"]
}}
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )

        insights_raw = response.choices[0].message.content.strip()

        # Limpieza para eliminar backticks y etiquetas JSON del string
        insights_clean = re.sub(r"```json|```", "", insights_raw).strip()

        try:
            insights_json = json.loads(insights_clean)
        except json.JSONDecodeError:
            # En caso de fallo, retornamos el texto completo como recomendación para que no se pierda info
            insights_json = {
                "patterns": [],
                "weaknesses": [],
                "recommendations": [insights_raw]
            }

        return {
            "nodes": list(nodes),
            "edges": edges,
            "ia_insights": insights_json
        }

    except CommunicationTable.DoesNotExist:
        return {
            "nodes": [],
            "edges": [],
            "ia_insights": {
                "patterns": [],
                "weaknesses": [],
                "recommendations": ["Tabla no encontrada."]
            }
        }
    except Exception as e:
        print("Error general en la generación del mapa:", str(e))
        return {
            "nodes": [],
            "edges": [],
            "ia_insights": {
                "patterns": [],
                "weaknesses": [],
                "recommendations": [f"Error inesperado: {str(e)}"]
            }
        }


def suggest_audit_fields(year: int, max_results=3):
    """
    Sugiere automáticamente hasta 3 combinaciones de objetivo, alcance, criterios y estándares,
    basándose en:
    - Registros históricos del modelo AuditProgramHeader
    - Reglas y buenas prácticas de la norma ISO 9001:2015

    Retorna una lista de diccionarios:
    [
        {
            "objective": "...",
            "scope": "...",
            "audit_criteria": "...",
            "security_standards": "..."
        },
        ...
    ]
    """

    historical_headers = AuditProgramHeader.objects.exclude(year=year).order_by('-year')[:10]

    if not historical_headers.exists():
        prompt = f"""
Eres un experto en auditorías internas de calidad bajo la norma ISO 9001:2015.

Basándote en buenas prácticas y la norma ISO 9001:2015, sugiéreme TRES propuestas completas (objetivo, alcance, criterios de auditoría y estándares de seguridad)
para un programa de auditoría anual del año {year}.

Responde únicamente en formato JSON, como una lista de 3 objetos con las claves:
- "objective"
- "scope"
- "audit_criteria"
- "security_standards"

Ejemplo:
[
  {{
    "objective": "Asegurar la conformidad del sistema de gestión con la norma ISO 9001:2015",
    "scope": "Todas las áreas del sistema de gestión de calidad",
    "audit_criteria": "ISO 9001:2015 cláusulas 4 a 10",
    "security_standards": "Controles de seguridad según política interna y requisitos legales aplicables"
  }},
  ...
]
"""
    else:
        examples = []
        for h in historical_headers:
            examples.append(
                f"Año: {h.year} | "
                f"Objetivo: {h.objective.strip()} | "
                f"Alcance: {h.scope.strip()} | "
                f"Criterios: {h.audit_criteria.strip()} | "
                f"Estándares: {h.security_standards.strip()}"
            )

        prompt = f"""
Eres un auditor líder experto en ISO 9001:2015.

Usando el siguiente historial de programas de auditoría anteriores, genera TRES propuestas de objetivo, alcance, criterios de auditoría y estándares de seguridad
para el año {year}. Sigue el formato anterior, en orden de prioridad (más completo o relevante primero).

Historial:
{chr(10).join(examples)}

Por favor responde en JSON como una lista de objetos con las claves:
- "objective"
- "scope"
- "audit_criteria"
- "security_standards"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        print("Respuesta IA (cruda):", repr(content))

        clean_content = re.sub(r'^```json\s*|\s*```$', '', content).strip()
        suggestions = json.loads(clean_content)

        if isinstance(suggestions, list) and all(isinstance(item, dict) for item in suggestions):
            return [
                {
                    "objective": item.get("objective", "").strip(),
                    "scope": item.get("scope", "").strip(),
                    "audit_criteria": item.get("audit_criteria", "").strip(),
                    "security_standards": item.get("security_standards", "").strip()
                }
                for item in suggestions[:max_results]
            ]

        print("Formato inesperado:", type(suggestions))
        return []

    except json.JSONDecodeError as jde:
        print("Error JSON:", str(jde))
        print("Contenido no parseable:", repr(clean_content))
        return []
    except Exception as e:
        print("Error general IA:", str(e))
        return []


def suggest_annual_processes_ai(program_header_id: int, max_results=3):
    """
    Sugiere automáticamente hasta 3 procesos y meses para auditar en un AuditProgramHeader dado,
    basándose en:
    - Historial de AnnualProgram
    - Indicadores de criticidad del modelo Process
    - Clasificaciones de hallazgos (NC mayor, menor)
    - Buenas prácticas ISO 9001:2015
    """
    try:
        header = AuditProgramHeader.objects.get(id=program_header_id)
    except AuditProgramHeader.DoesNotExist:
        return []

    year = header.year
    all_processes = Process.objects.all()
    if not all_processes.exists():
        return []

    today = date.today()
    past_programs = AnnualProgram.objects.exclude(program_header__year=year).select_related('process', 'program_header')
    past_findings = Findings.objects.select_related('report__audit__annual_program__process')

    # --- Preparar historial si lo hay ---
    if past_programs.exists():
        audit_history = defaultdict(list)
        for entry in past_programs:
            audit_history[entry.process.id].append(entry.month)

        findings_by_process = defaultdict(lambda: {"NC_MAYOR": 0, "NC_MENOR": 0})
        for f in past_findings:
            try:
                process_id = f.report.audit.annual_program.process.id
                findings_by_process[process_id][f.classification] += 1
            except:
                continue

        process_data_examples = []
        for process in all_processes:
            entry = {
                "process_name": process.name,
                "process_code": process.process_code,
                "months_audited": audit_history.get(process.id, []),
                "review_date": str(process.review_date) if process.review_date else "None",
                "creation_date": str(process.creation_date),
                "staff_roles": bool(process.staff_roles),
                "equipment": bool(process.equipment),
                "materials": bool(process.materials),
                "transport_resources": bool(process.transport_resources),
                "nc_mayor": findings_by_process[process.id]["NC_MAYOR"],
                "nc_menor": findings_by_process[process.id]["NC_MENOR"]
            }
            process_data_examples.append(entry)

        prompt = f"""
Eres un auditor líder experto en ISO 9001:2015.

Con base en el siguiente historial de auditorías y características de los procesos, sugiere TRES combinaciones de proceso y mes para auditar en el año {year}.
Prioriza:
- Procesos con más no conformidades (NC_MAYOR > NC_MENOR)
- Procesos con alta complejidad (campos poblados)
- Procesos no auditados recientemente o nuevos
- Procesos sin revisión reciente
- Distribución de auditorías a lo largo del año (meses menos usados)

Cada sugerencia debe incluir:
- process_name
- process_code
- suggested_month
- justification (una frase clara con el razonamiento)

Datos:
{json.dumps(process_data_examples[:15], indent=2)}

Responde en formato JSON como una lista de objetos con las claves:
- "process_name"
- "process_code"
- "suggested_month"
- "justification"
"""
    else:
        # --- Sin historial, guiarse solo por ISO 9001:2015 ---
        fallback_processes = all_processes[:10]
        process_data = [
            {
                "process_name": p.name,
                "process_code": p.process_code,
                "creation_date": str(p.creation_date),
                "review_date": str(p.review_date) if p.review_date else "None",
                "staff_roles": bool(p.staff_roles),
                "equipment": bool(p.equipment),
                "materials": bool(p.materials),
                "transport_resources": bool(p.transport_resources),
            }
            for p in fallback_processes
        ]

        prompt = f"""
No hay historial de auditorías disponibles.

Eres un experto en auditoría ISO 9001:2015 y tienes la siguiente lista de procesos activos. 
Basándote en su criticidad, fecha de creación, complejidad (campos poblados), y la norma ISO 9001:2015, 
sugiere TRES procesos con el mes ideal para auditarlos este año ({year}).

Cada sugerencia debe contener:
- process_name
- process_code
- suggested_month
- justification (basada en los datos disponibles)

Datos:
{json.dumps(process_data, indent=2)}

Responde en JSON como lista de objetos con esas claves.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1000,
        )

        content = response.choices[0].message.content.strip()
        print("IA Response:", repr(content))

        clean_content = re.sub(r'^```json\s*|\s*```$', '', content).strip()
        data = json.loads(clean_content)

        MONTHS_MAP = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return [
                {
                    "process_name": item.get("process_name", "").strip(),
                    "process_code": item.get("process_code", "").strip(),
                    "suggested_month": MONTHS_MAP.get(item.get("suggested_month", "January"), 1),
                    "justification": item.get("justification", "").strip()
                }
                for item in data[:max_results]
            ]

        print("Formato inesperado:", type(data))
        return []

    except json.JSONDecodeError as e:
        print("Error JSON:", str(e))
        print("Contenido recibido:", repr(clean_content))
        return []
    except Exception as e:
        print("Error general IA:", str(e))
        return []
        

def suggest_audited_ai(plan_id: int, max_results=5):
    try:
        plan = AnnualPlan.objects.select_related('annual_program__program_header', 'annual_program__process').get(id=plan_id)
        annual_program = plan.annual_program
        header = annual_program.program_header
        process = annual_program.process
    except AnnualPlan.DoesNotExist:
        return []

    today = date.today()
    three_months_ago = today - timedelta(days=90)

    users_scores = defaultdict(lambda: {"score": 0, "reasons": []})

    # 1. Ha sido auditado en este proceso
    previously_audited = AnnualPlanAudited.objects.filter(
        annual_plan__annual_program__process=process
    ).select_related('user')

    for audited in previously_audited:
        uid = audited.user.id
        users_scores[uid]["score"] += 3
        users_scores[uid]["reasons"].append("Experiencia previa siendo auditado en este proceso")

    # 2. Ha sido auditor en este proceso (visión inversa útil)
    past_auditors = AnnualPlanAuditor.objects.filter(
        annual_plan__annual_program__process=process
    ).select_related('user')

    for auditor in past_auditors:
        uid = auditor.user.id
        users_scores[uid]["score"] += 2
        users_scores[uid]["reasons"].append("Experiencia como auditor en este proceso, puede aportar visión crítica")

    # 3. Ha sido asignado a un AnnualProgram del proceso
    prev_programs = AnnualProgramUser.objects.filter(
        annual_program__process=process
    ).select_related('user', 'annual_program__program_header')

    for apu in prev_programs:
        uid = apu.user.id
        users_scores[uid]["score"] += 2
        users_scores[uid]["reasons"].append("Participación en programas del proceso")

        if apu.annual_program.program_header.year == header.year:
            users_scores[uid]["score"] -= 1
            users_scores[uid]["reasons"].append("Ya participó este año, se prioriza rotación")

    # 4. Ha sido líder en auditorías del proceso
    leaders = AnnualPlan.objects.filter(
        annual_program__process=process
    ).select_related('lider')

    for leader in leaders:
        if leader.lider:
            uid = leader.lider.id
            users_scores[uid]["score"] += 1
            users_scores[uid]["reasons"].append("Ha liderado auditorías de este proceso")

    # 5. Ha auditado requisitos técnicos similares
    process_reqs = ProcessRequirement.objects.filter(
        process=process
    ).values_list('requirement_id', flat=True)

    similar_checklists = Checklist.objects.filter(
        question__requirement_id__in=process_reqs
    ).select_related('audit_plan__lider')

    for checklist in similar_checklists:
        if checklist.audit_plan and checklist.audit_plan.lider:
            uid = checklist.audit_plan.lider.id
            users_scores[uid]["score"] += 1
            users_scores[uid]["reasons"].append("Experiencia con requisitos técnicos similares")

    # 6. Evaluaciones positivas en auditorías
    good_eval = AuditorEvaluation.objects.filter(
        audit__annual_program__process=process,
        rate__gte=7
    ).select_related('audit__lider')

    for eval in good_eval:
        if eval.audit and eval.audit.lider:
            uid = eval.audit.lider.id
            users_scores[uid]["score"] += 1
            users_scores[uid]["reasons"].append("Obtuvo buenas evaluaciones como auditor")

    # 7. Penalización por saturación reciente
    for uid in list(users_scores.keys()):
        last_dates = []

        last_apu = AnnualProgramUser.objects.filter(user_id=uid).order_by('-annual_program__program_header__year').first()
        if last_apu:
            year = last_apu.annual_program.program_header.year
            last_dates.append(date(year, 12, 31))

        last_ap = AnnualPlanAuditor.objects.filter(user_id=uid).order_by('-annual_plan__audit_opening_date').first()
        if last_ap and last_ap.annual_plan.audit_opening_date:
            last_dates.append(last_ap.annual_plan.audit_opening_date)

        last_apa = AnnualPlanAudited.objects.filter(user_id=uid).order_by('-annual_plan__audit_opening_date').first()
        if last_apa and last_apa.annual_plan.audit_opening_date:
            last_dates.append(last_apa.annual_plan.audit_opening_date)

        last_leader = AnnualPlan.objects.filter(lider_id=uid).order_by('-audit_opening_date').first()
        if last_leader and last_leader.audit_opening_date:
            last_dates.append(last_leader.audit_opening_date)

        if last_dates and max(last_dates) > three_months_ago:
            users_scores[uid]["score"] -= 2
            users_scores[uid]["reasons"].append("Actividad reciente, penalización por evitar sobrecarga")

    # Preparar para IA
    scored_users = []
    for uid, info in users_scores.items():
        try:
            user = User.objects.get(id=uid)
            scored_users.append({
                "user_id": uid,
                "username": user.username,
                "score": info["score"],
                "justification": "; ".join(info["reasons"])[:200]
            })
        except User.DoesNotExist:
            continue

    scored_users.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = scored_users[:max_results]

    if not top_candidates:
        top_candidates = [{
            "user_id": 0,
            "username": "N/A",
            "score": 0,
            "justification": "No hay historial suficiente para sugerir candidatos. Se recomienda seleccionar según criterios de la ISO 9001:2015."
        }]

    prompt = f"""
Eres un asistente experto en auditorías ISO. A continuación tienes una lista de posibles candidatos para ser auditados en un plan anual. Cada uno tiene un puntaje y una justificación técnica:

{json.dumps(top_candidates, indent=2)}

Si no hay candidatos válidos, indica que debe seleccionarse según criterio profesional y normas ISO.

Devuelve JSON con: user_id, username, score, justification.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en auditorías ISO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        gpt_response = response.choices[0].message.content
        clean_response = re.sub(r'^```json|```$', '', gpt_response).strip()
        return json.loads(clean_response)
    except json.JSONDecodeError as jde:
        print(f"Error al decodificar JSON: {jde}")
        print("Contenido recibido:", repr(clean_response))
        return top_candidates
    except Exception as e:
        print(f"Error GPT: {e}")
        return top_candidates


def suggest_audit_questions(requirement_obj, process_name, max_results=5):
    """
    Genera dinámicamente preguntas de auditoría para un objeto Requirement,
    aplicadas a un proceso específico.

    - requirement_obj: instancia del modelo Requirement
    - process_name: string, ej. "Producción aeroespacial"
    - max_results: número de preguntas a sugerir (máx. 5 por defecto)

    Retorna una lista de strings con preguntas sugeridas por IA.
    """

    # Usamos el nombre como identificador del requisito (ej. "8.5.1")
    clause_identifier = requirement_obj.name

    # Texto más descriptivo para enriquecer el prompt (si decides añadirlo en el modelo más adelante)
    clause_description = getattr(requirement_obj, "description", "")  # si decides agregarlo

    # Prompt enriquecido
    prompt = f"""
Eres un experto en auditorías de calidad bajo la norma ISO 9001:2015, con experiencia específica en la industria aeroespacial.

Quiero que generes {max_results} preguntas de auditoría bien formuladas, prácticas y alineadas con el requisito/cláusula "{clause_identifier}" de la norma ISO 9001:2015.

{f'Descripción del requisito: {clause_description}' if clause_description else ''}

Estas preguntas deben estar orientadas a auditar el proceso de: "{process_name}".

Cada pregunta debe:
- Estar en español
- Ser clara, directa, y enfocada en verificar el cumplimiento del requisito
- Ser útil para identificar conformidades o no conformidades en una auditoría real

Por favor responde únicamente con una lista JSON de strings. Ejemplo:

[
  "¿Pregunta 1...?",
  "¿Pregunta 2...?",
  ...
]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=700,
        )

        content = response.choices[0].message.content.strip()
        print("Respuesta cruda de IA:", repr(content))

        # Limpiar posibles delimitadores de markdown
        clean_content = re.sub(r'^```json\s*|\s*```$', '', content).strip()
        questions = json.loads(clean_content)

        if isinstance(questions, list) and all(isinstance(q, str) for q in questions):
            return [q.strip() for q in questions[:max_results]]

        print("Formato inesperado de respuesta IA:", type(questions))
        return []

    except json.JSONDecodeError as jde:
        print("Error al parsear JSON:", str(jde))
        print("Contenido recibido:", repr(clean_content))
        return []
    except Exception as e:
        print("Error general al generar preguntas de auditoría:", str(e))
        return []

def suggest_compliance_rating(checklist_obj):
    """
    Usa IA para sugerir un rating (0-10) de cumplimiento basado en:
    - La pregunta de auditoría
    - La evidencia ingresada
    - El requisito asociado
    - Criterios de la norma ISO 9001:2015

    checklist_obj: instancia de Checklist con campos 'evidence', 'question', 'orden', etc.

    Retorna un entero entre 0 y 10, o None si no se puede obtener.
    """

    question_text = checklist_obj.question.question_text
    requirement_name = checklist_obj.question.requirement.name if checklist_obj.question.requirement else "N/A"
    evidence = checklist_obj.evidence or ""
    process_name = checklist_obj.audit_plan.annual_program.process.name
    clause_description = getattr(checklist_obj.question.requirement, "description", "")  # opcional

    # Prompt para IA
    prompt = f"""
Eres un auditor experto en calidad bajo la norma ISO 9001:2015, especialmente en el sector industrial.

Te presento una **pregunta de auditoría**, una **evidencia objetiva** recabada durante la auditoría, y el requisito de la norma que aplica.

Debes analizar y proponer un grado de cumplimiento del 0 al 10, donde:
- 0 significa "incumplimiento total"
- 10 significa "cumplimiento total"
- Los valores intermedios reflejan distintos niveles de cumplimiento parcial.

Tu evaluación debe seguir los criterios de ISO 9001:2015.

---

**Requisito/cláusula ISO:** {requirement_name}
{f'Descripción del requisito: {clause_description}' if clause_description else ''}

**Proceso auditado:** {process_name}

**Pregunta de auditoría:** {question_text}

**Evidencia obtenida:** {evidence}

---

Solo responde con el número entero sugerido (0 a 10). Ejemplo: `8`
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # o el que uses
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )

        result = response.choices[0].message.content.strip()

        # Extraer el número sugerido
        match = re.search(r"\b([0-9]|10)\b", result)
        if match:
            rating = int(match.group(1))
            return rating if 0 <= rating <= 10 else None
        else:
            print("Respuesta IA inesperada:", result)
            return None

    except Exception as e:
        print("Error al obtener sugerencia de rating:", str(e))
        return None


def classify_finding_ia(finding_text, requirement_obj=None):
    """
    Clasifica automáticamente un hallazgo según la norma ISO 9001:2015 usando IA.

    Parámetros:
    - finding_text: Texto del hallazgo ingresado por el auditor.
    - requirement_obj: (opcional) Instancia del modelo Requirement asociada al hallazgo.

    Retorna una string: 'NC_MAYOR', 'NC_MENOR' u 'OPORTUNIDAD_MEJORA'
    """

    # Identificador de cláusula
    clause_identifier = requirement_obj.name if requirement_obj else ""
    clause_description = getattr(requirement_obj, "description", "") if requirement_obj else ""

    prompt = f"""
Eres un experto en auditorías de calidad bajo la norma ISO 9001:2015.

Quiero que clasifiques el siguiente hallazgo en una de las siguientes categorías:
- NC_MAYOR: No conformidad mayor
- NC_MENOR: No conformidad menor
- OPORTUNIDAD_MEJORA: Oportunidad de mejora

Tu clasificación debe basarse en los criterios de la norma ISO 9001:2015.

{f'Este hallazgo está relacionado con la cláusula "{clause_identifier}".' if clause_identifier else ''}
{f'Descripción de la cláusula: {clause_description}' if clause_description else ''}

Texto del hallazgo:
\"\"\"{finding_text}\"\"\"

Responde únicamente con uno de estos tres valores exactos (sin comillas ni explicación):
NC_MAYOR
NC_MENOR
OPORTUNIDAD_MEJORA
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=10,
        )

        result = response.choices[0].message.content.strip().upper()

        if result in ["NC_MAYOR", "NC_MENOR", "OPORTUNIDAD_MEJORA"]:
            return result

        print("Respuesta IA no válida:", repr(result))
        return None

    except Exception as e:
        print("Error en clasificación IA:", str(e))
        return None

def suggest_audit_report_fields(audit_plan_id: int):
    """
    Genera automáticamente un resumen (summary) y fortalezas (strengths) para un AuditReport
    basado en hallazgos, cumplimiento, criterios y contexto ISO 9001:2015.

    Requiere:
    - audit_plan_id: ID del AnnualPlan.

    Devuelve:
    {
        "summary": "...",
        "strengths": "..."
    }
    """
    try:
        audit_plan = AnnualPlan.objects.select_related(
            'annual_program__program_header',
            'annual_program__process'
        ).prefetch_related(
            'findings',
            'checklists__question',
        ).get(id=audit_plan_id)

        # Encabezado
        header = audit_plan.annual_program.program_header
        process = audit_plan.annual_program.process

        # Recolección de datos
        findings = audit_plan.findings.all()
        checklist = audit_plan.checklists.all()

        compliance_summary = {
            "total": checklist.count(),
            "compliant": checklist.filter(compliance=True).count(),
            "non_compliant": checklist.filter(compliance=False).count()
        }

        finding_texts = [f"- {f.finding_text} ({f.classification})" for f in findings]
        strengths_list = [
            f.question.question_text for f in checklist.filter(compliance=True)[:5]
        ]

        # Construcción del prompt
        prompt = f"""
Eres un auditor experto en la norma ISO 9001:2015, especialmente en la cláusula 9.1.2 (seguimiento, medición, análisis y evaluación).

Debes redactar un **informe de auditoría** con dos secciones:
- summary: resumen estructurado y claro del desarrollo de la auditoría
- strengths: fortalezas detectadas en el proceso auditado

Toma en cuenta:
- **Objetivo:** {header.objective}
- **Alcance:** {header.scope}
- **Criterios de auditoría:** {header.audit_criteria}
- **Estándares de seguridad:** {header.security_standards}
- **Proceso auditado:** {process.name} ({process.process_code})
- **Hallazgos encontrados:** {chr(10).join(finding_texts) or 'Ninguno'}
- **Cumplimiento general:** {compliance_summary['compliant']}/{compliance_summary['total']} ítems cumplidos
- **Fortalezas (resumidas de la checklist):** {chr(10).join(strengths_list) or 'Ninguna observada'}

Por favor, responde en JSON con las claves:
- "summary"
- "strengths"

La redacción debe ser profesional, precisa y orientada a las recomendaciones de auditoría interna bajo ISO 9001:2015.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )

        content = response.choices[0].message.content.strip()
        clean_content = re.sub(r'^```json\s*|\s*```$', '', content).strip()
        suggestions = json.loads(clean_content)

        return {
            "summary": suggestions.get("summary", "").strip(),
            "strengths": suggestions.get("strengths", "").strip()
        }

    except Exception as e:
        print(f"Error al generar informe IA: {str(e)}")
        return {
            "summary": "",
            "strengths": ""
        }
