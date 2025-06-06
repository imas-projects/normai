import openai
import json
from django.conf import settings
from risks.models import RiskIdentification

# Configurar API key
openai.api_key = settings.OPENAI_API_KEY

def suggest_risk_fields(area_name, activity_name, max_results=1):
    """
    Sugiere automáticamente un riesgo y sus consecuencias basándose en:
    - El área seleccionada
    - El nombre de la actividad introducida
    - Riesgos existentes en la base de datos
    - Criterios de ISO 9001:2015

    Retorna un diccionario con claves:
    {
        "identified_risk": "...",
        "consequences": "..."
    }
    """

    # Extraer riesgos históricos
    historical_risks = RiskIdentification.objects.select_related('area').all()

    # Si no hay datos previos, generar prompt genérico
    if not historical_risks.exists():
        fallback_prompt = f"""
Eres un experto en gestión de calidad ISO 9001:2015 en industria aeroespacial.
Sugiéreme un posible riesgo identificado y sus consecuencias según:

Área: {area_name}
Actividad: {activity_name}

Responde en JSON con las claves: 'identified_risk' y 'consequences'.
        """
        prompt = fallback_prompt
    else:
        examples = []
        for risk in historical_risks[:10]:  # máximo 10 ejemplos
            examples.append(
                f"Área: {risk.area.name} | Actividad: {risk.activity_name} | "
                f"Riesgo: {risk.identified_risk} | Consecuencias: {risk.consequences}"
            )

        prompt = f"""
Eres un asistente experto en gestión de calidad bajo la norma ISO 9001:2015 aplicada al sector aeroespacial.
Dado un área y una actividad, sugiere un riesgo y sus consecuencias con base en ejemplos previos.

Histórico de riesgos:
{chr(10).join(examples)}

Nueva entrada:
Área: {area_name}
Actividad: {activity_name}

Responde en formato JSON con las claves 'identified_risk' y 'consequences'.
        """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )

        content = response.choices[0].message.content.strip()

        suggestion = json.loads(content)
        return {
            "identified_risk": suggestion.get("identified_risk", ""),
            "consequences": suggestion.get("consequences", "")
        }

    except Exception as e:
        print("Error al generar sugerencia IA:", str(e))
        return {"identified_risk": "", "consequences": ""}
