from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from collections import OrderedDict
from django.db.models.functions import TruncMonth
import json
from django.shortcuts import render
from django.utils.safestring import mark_safe
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, F, Q
from django.utils.timezone import now
from django.db.models import OuterRef, Subquery
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder
from collections import defaultdict
from django.db.models import Prefetch
from django.db.models.functions import TruncMonth
from audits.models import AnnualPlan, AuditReport, CorrectiveAction, CorrectiveActionFollowUp, Findings, AnnualPlanAudited 
from processes.models import Process, ProcessPerformanceIndicators, PerformanceIndicator, ProcessPerformanceMeasurements
from company.models import Area, Position, UserPosition, ExternalClient, ExternalSupplier
from risks.models import RiskTreatment, RiskEvaluation, Reevaluation, RiskIdentification
from communications.models import CommunicationTable



# Create your views here.

@login_required
def wellcome_view(request):
    current_year = now().year
    total_clientes = ExternalClient.objects.count()
    total_proveedores = ExternalSupplier.objects.count()

    # === Indicador 1: Auditorías realizadas / planificadas ===
    audit_plans = AnnualPlan.objects.filter(
        annual_program__program_header__year=current_year
    )
    total_planificadas = audit_plans.count()
    realizadas = AuditReport.objects.filter(audit_plan__in=audit_plans).count()
    pendientes = total_planificadas - realizadas
    porcentaje_cumplimiento = (
        (realizadas / total_planificadas) * 100 if total_planificadas > 0 else 0
    )

    # === Indicador 2: Acciones correctivas abiertas / cerradas ===
    latest_followup_subquery = CorrectiveActionFollowUp.objects.filter(
        corrective_action=OuterRef('pk')
    ).order_by('-followup_date')

    corrective_actions = CorrectiveAction.objects.annotate(
        last_status=Subquery(latest_followup_subquery.values('status')[:1])
    )

    acciones_abiertas = corrective_actions.filter(
        last_status__in=['PENDING', 'IN_PROGRESS']
    ).count()
    total_acciones = corrective_actions.exclude(last_status__isnull=True).count()
    cerradas = total_acciones - acciones_abiertas
    porcentaje_acciones_abiertas = (
        (acciones_abiertas / total_acciones) * 100 if total_acciones > 0 else 0
    )

    # === Indicador 3: Tasa de No Conformidades ===
    nc_classifications = ['NC_MAYOR', 'NC_MENOR']

    audit_ids_with_nc = Findings.objects.filter(
        classification__in=nc_classifications
    ).values('audit_plan').distinct()

    total_auditorias_con_nc = AnnualPlan.objects.filter(
        id__in=audit_ids_with_nc
    ).count()
    auditorias_sin_nc = realizadas - total_auditorias_con_nc

    tasa_nc = (
        (total_auditorias_con_nc / realizadas) * 100 if realizadas > 0 else 0
    )

    # === Indicador 4: Procesos con Indicadores en Alerta ===
    areas_empresa = Area.objects.all()
    total_procesos = Process.objects.count()
    hoy = date.today()
    ultimo_mes = hoy - timedelta(days=30)
    ultimo_dosmes = hoy - timedelta(days=60)

    recientes_process_perform_measure = ProcessPerformanceMeasurements.objects.filter(date__gte=ultimo_mes)
    alerta = []
    procesos_en_alerta = []

    for ppm in recientes_process_perform_measure:
        

        indicador = ProcessPerformanceIndicators.objects.get(
            process=ppm.process,
            performanceindicator=ppm.performance_indicator
        )
        
        min_val = indicador.min_acceptable_value
        max_val = indicador.max_acceptable_value

        if ((min_val is not None and ppm.measured_value < min_val) or (max_val is not None and ppm.measured_value > max_val)):
            alerta.append(ppm)
            procesos_en_alerta.append(ppm.process.name)

    #procesos_en_alerta = len(alerta)
    numero_procesos_alerta = len(set(procesos_en_alerta))
    tasa_procesos_alerta = (numero_procesos_alerta / total_procesos) * 100 if realizadas > 0 else 0
       

    # === Indicador 5: Índice de Mejora Continua ===
    ultimos_dosmeses = hoy - timedelta(days=60)
    ultimo_mes = hoy - timedelta(days=30)
    actuales = ProcessPerformanceMeasurements.objects.filter(date__gte=ultimo_mes).values('performance_indicator').annotate(avg_actual=Avg('measured_value'))
    anteriores = ProcessPerformanceMeasurements.objects.filter(date__range=(ultimos_dosmeses, ultimo_mes)).values('performance_indicator').annotate(avg_anterior=Avg('measured_value'))

    anteriores_dict = {a['performance_indicator']: a['avg_anterior'] for a in anteriores}

    suma_mejoras = Decimal('0.0')
    kpis_comparados = 0

    for actual in actuales:
        pid = actual['performance_indicator']
        valor_actual = actual['avg_actual']
        valor_anterior = anteriores_dict.get(pid)

        if valor_anterior and valor_anterior != 0:
            mejora = ((valor_actual - valor_anterior) / valor_anterior) * 100
            suma_mejoras += mejora
            kpis_comparados += 1

    # Cálculo del índice de mejora continua
    if kpis_comparados > 0:
        indice_mejora_continua = suma_mejoras / kpis_comparados
    else:
        indice_mejora_continua = None


    # === Gráfico: Tendencia de Auditorías Realizadas por Mes ===
    auditorias_por_mes_qs = (
        AnnualPlan.objects.filter(
            annual_program__program_header__year=current_year,
            id__in=AuditReport.objects.values_list('audit_plan_id', flat=True)
        )
        .annotate(month=TruncMonth('audit_opening_date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    auditorias_labels = []
    auditorias_values = []

    for entry in auditorias_por_mes_qs:
        auditorias_labels.append(entry['month'].strftime('%b'))  # Ej: 'Ene', 'Feb'
        auditorias_values.append(entry['total'])
        

    # === Distribución de No Conformidades por Clasificación ===
    # Filtramos findings relacionados con auditorías del año actual
    findings_dist = (
        Findings.objects
        #.filter(audit_plan__annual_program__program_header__year=current_year)
        .values('classification')
        .annotate(total=Count('id'))
    )

    # Mapear para mostrar etiquetas legibles y evitar que falte alguna categoría
    clasificaciones_map = {
        'NC_MAYOR': 'No Conformidad Mayor',
        'NC_MENOR': 'No Conformidad Menor',
        'OPORTUNIDAD_MEJORA': 'Oportunidad de mejora',
    }

    # Inicializar con 0 para todas las categorías
    clasificaciones_labels = []
    clasificaciones_values = []

    for key, label in list(clasificaciones_map.items()):
        clasificaciones_labels.append(label)
        total = next((f['total'] for f in findings_dist if f['classification'] == key), 0)
        clasificaciones_values.append(total)

    areas = Area.objects.all()

    processes_with_findings = Process.objects.annotate(
        total_findings=Count('processrequirement__findings')
    ).order_by('-total_findings')

    current_date = timezone.now().date()
    area_id = request.GET.get("area_id")

    risk_treatments = RiskTreatment.objects.filter(target_date__gte=current_date).prefetch_related('responsible__area')
    processes = Process.objects.filter(review_date__gte=current_date).select_related('responsible__area')
    communications = CommunicationTable.objects.filter(review_date__gte=current_date).select_related('emiter__area')
    corrective_actions = CorrectiveAction.objects.filter(due_date__gte=current_date).select_related('responsible_user')
    annual_plans = AnnualPlan.objects.filter(audit_opening_date__gte=current_date).prefetch_related('audited_users__user__user_position__position__area')

    activities = []

    for rt in risk_treatments:
        for pos in rt.responsible.all():
            area = pos.area
            if not area_id or (area and area.id == int(area_id)):
                activities.append({
                    "date": rt.target_date,
                    "name": f"Tratamiento del Riesgo: {rt.treatment_action}",
                    "type": "Riesgo",
                    "responsible": pos.name,
                    "area": area.name if area else "Sin área",
                    "url": "/risks/",
                })

    for p in processes:
        area = p.responsible.area if p.responsible else None
        if not area_id or (area and area.id == int(area_id)):
            activities.append({
                "date": p.review_date,
                "name": f"Revisión del Proceso: {p.name}",
                "type": "Proceso",
                "responsible": p.responsible.name if p.responsible else "",
                "area": area.name if area else "Sin área",
                "url": "/processes/",
            })

    for c in communications:
        area = c.emiter.area if c.emiter else None
        if not area_id or (area and area.id == int(area_id)):
            activities.append({
                "date": c.review_date,
                "name": f"Revisión de Comunicación: {c.code}",
                "type": "Comunicación",
                "responsible": c.reviewed_by.name if c.reviewed_by else "",
                "area": area.name if area else "Sin área",
                "url": "/communications/",
            })

    for ca in corrective_actions:
        user = ca.responsible_user
        positions = user.user_position.all()
        for up in positions:
            pos = up.position
            area = pos.area if pos else None
            if not area_id or (area and area.id == int(area_id)):
                activities.append({
                    "date": ca.due_date,
                    "name": f"Accion Correctiva: {ca.corrective_action}",
                    "type": "Auditoria",
                    "responsible": pos.name,
                    "area": area.name if area else "Sin área",
                    "url": "/audits/conduct-internal-audits/",
                })

    for ap in annual_plans:
        for audited in ap.audited.all():
            user = audited.user
            for up in user.user_position.all():
                pos = up.position
                area = pos.area if pos else None
                if not area_id or (area and area.id == int(area_id)):
                    activities.append({
                        "date": ap.audit_opening_date,
                        "name": f"Plan de Auditoria: {ap.annual_program}",
                        "type": "Auditoria",
                        "responsible": pos.name,
                        "area": area.name if area else "Sin área",
                        "url": "/audits/annual-audit-plan/",
                    })

    activities.sort(key=lambda x: x['date'])

    paginator = Paginator(activities, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "mistemplates/_activity_list.html", {"page_obj": page_obj})




    # === Gráfico: Número de Alertas Por Proceso ===
    todos_procesos = Process.objects.all()

    process_labels = [proceso.name for proceso in todos_procesos]

    alerta = []
    procesos_alerta = []

    for ppm in recientes_process_perform_measure:
        indicador = ProcessPerformanceIndicators.objects.get(
            process=ppm.process,
            performanceindicator=ppm.performance_indicator
        )

        min_val = indicador.min_acceptable_value
        max_val = indicador.max_acceptable_value

        if ((min_val is not None and ppm.measured_value < min_val) or
            (max_val is not None and ppm.measured_value > max_val)):
            
            alerta.append(ppm)
            procesos_alerta.append(ppm.process.name)
        
        proceso_numero_alertas = {}
        for nombre in procesos_alerta:
            if nombre in proceso_numero_alertas:
                proceso_numero_alertas[nombre] += 1
            else:
                proceso_numero_alertas[nombre] = 1
        procesos_con_alertas = list(proceso_numero_alertas.keys())

        for proceso in Process.objects.all():
            if proceso.name not in proceso_numero_alertas:
                proceso_numero_alertas[proceso.name] = 0.01

    process_labels=list(proceso_numero_alertas.keys()) 
    process_values=list(proceso_numero_alertas.values())

    # === Gráfico: Tendencia Índice de Mejora Continua === #

    mediciones = (
        ProcessPerformanceMeasurements.objects
        .annotate(month=TruncMonth('date'))
        .values('month', 'performance_indicator')
        .annotate(avg_valor=Avg('measured_value'))
        .order_by('month')
    )

    datos_por_mes = OrderedDict()
    for fila in mediciones:
        mes = fila['month'].strftime("%b").upper() # ej: '2025-06'
        kpi = fila['performance_indicator']
        avg = fila['avg_valor']

        if mes not in datos_por_mes:
            datos_por_mes[mes] = {}
        datos_por_mes[mes][kpi] = avg

    kpis_labels = []
    kpis_values = []

    meses_ordenados = list(datos_por_mes.keys())
    

    for i in range(1, len(meses_ordenados)):
        mes_anterior = datos_por_mes[meses_ordenados[i - 1]]
        mes_actual = datos_por_mes[meses_ordenados[i]]

        total_variacion = 0
        indicadores_contados = 0

        for kpi_id, valor_actual in mes_actual.items():
            valor_anterior = mes_anterior.get(kpi_id)
            if valor_anterior and valor_anterior != 0:
                variacion = ((valor_actual - valor_anterior) / valor_anterior) * 100
                total_variacion += variacion
                indicadores_contados += 1

        if indicadores_contados > 0:
            promedio_mes = total_variacion / indicadores_contados
        else:
            promedio_mes = 0

        kpis_labels.append(meses_ordenados[i])
        kpis_values.append(round(promedio_mes, 2))

    # === Recuadros de Alertas ===
    siguiente_auditoria = next(
    (a for a in activities if a['type'] == 'Auditoria' and a['date'] >= current_date),
    None
    )
    siguiente_auditoria_dias_restantes = (siguiente_auditoria['date'] - date.today()).days

    # === Contexto final ===
    contexto = {
        'realizadas': realizadas,
        'pendientes': pendientes,
        'planificadas': total_planificadas,
        'porcentaje': round(porcentaje_cumplimiento, 2),

        'acciones_abiertas': acciones_abiertas,
        'cerradas': cerradas,
        'acciones_totales': total_acciones,
        'acciones_porcentaje': round(porcentaje_acciones_abiertas, 2),

        'auditorias_con_nc': total_auditorias_con_nc,
        'sin_nc': auditorias_sin_nc,
        'tasa_nc': round(tasa_nc, 2),

        'procesos_en_alerta': numero_procesos_alerta,
        'total_procesos': total_procesos,
        'tasa_procesos_alerta':tasa_procesos_alerta,

        'indice_mejora_continua':indice_mejora_continua,
        'areas_empresa':areas_empresa,


        'auditorias_labels': auditorias_labels,
        'auditorias_values': auditorias_values,

        'clasificaciones_labels': clasificaciones_labels,
        'clasificaciones_values': clasificaciones_values,

        'process_labels':process_labels,
        'process_values':process_values,

        'kpis_labels': kpis_labels,
        'kpis_values': kpis_values,

        'areas': areas,

        'processes_with_findings': processes_with_findings,

        'page_obj': page_obj,

        'total_clientes': total_clientes,
        'total_proveedores': total_proveedores,
        'siguiente_auditoria': siguiente_auditoria,
        'siguiente_auditoria_dias_restantes':siguiente_auditoria_dias_restantes,
        'kpis_revision': len(kpis_values),
        'procesos_con_alertas':procesos_con_alertas
    }

    return render(request, "mistemplates/user-dashboard.html", contexto)

@login_required
def area_detail_view(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    current_date = timezone.now().date()

    # === Actividades ===
    activities = []
    risk_treatments = RiskTreatment.objects.filter(target_date__gte=current_date).prefetch_related('responsible__area')
    for rt in risk_treatments:
        for pos in rt.responsible.all():
            if pos.area_id == area.id:
                activities.append({
                    "date": rt.target_date,
                    "name": f"Tratamiento del Riesgo: {rt.treatment_action}",
                    "type": "Riesgo",
                    "responsible": pos.name,
                    "area": pos.area.name,
                    "url": "/risks/",
                })

    processes = Process.objects.filter(review_date__gte=current_date, responsible__area=area).select_related('responsible__area')
    for p in processes:
        if p.responsible:
            activities.append({
                "date": p.review_date,
                "name": f"Revisión del Proceso: {p.name}",
                "type": "Proceso",
                "responsible": p.responsible.name,
                "area": p.responsible.area.name,
                "url": "/processes/",
            })

    communications = CommunicationTable.objects.filter(review_date__gte=current_date).select_related('emiter__area')
    for c in communications:
        if c.emiter and c.emiter.area_id == area.id:
            activities.append({
                "date": c.review_date,
                "name": f"Revisión de Comunicación: {c.code}",
                "type": "Comunicación",
                "responsible": c.reviewed_by.name if c.reviewed_by else "",
                "area": c.emiter.area.name,
                "url": "/communications/",
            })

    corrective_actions = CorrectiveAction.objects.filter(due_date__gte=current_date).select_related('responsible_user')
    for ca in corrective_actions:
        for up in ca.responsible_user.user_position.all():
            pos = up.position
            if pos and pos.area_id == area.id:
                activities.append({
                    "date": ca.due_date,
                    "name": f"Acción Correctiva: {ca.corrective_action}",
                    "type": "Auditoría",
                    "responsible": pos.name,
                    "area": pos.area.name,
                    "url": "/audits/conduct-internal-audits/",
                })

    annual_plans = AnnualPlan.objects.filter(audit_opening_date__gte=current_date).prefetch_related('audited_users__user__user_position__position__area')
    for ap in annual_plans:
        for audited in ap.audited.all():
            for up in audited.user.user_position.all():
                pos = up.position
                if pos and pos.area_id == area.id:
                    activities.append({
                        "date": ap.audit_opening_date,
                        "name": f"Plan de Auditoría: {ap.annual_program}",
                        "type": "Auditoría",
                        "responsible": pos.name,
                        "area": pos.area.name,
                        "url": "/audits/annual-audit-plan/",
                    })

    # === Eliminar duplicados por nombre, tipo y fecha ===
    seen = set()
    unique_activities = []
    for act in activities:
        key = (act['name'], act['type'], act['date'])
        if key not in seen:
            seen.add(key)
            unique_activities.append(act)
    activities = sorted(unique_activities, key=lambda x: x['date'])

    paginator = Paginator(activities, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # === Comunicaciones ===
    comm_queryset = CommunicationTable.objects.filter(
        emiter__area_id=area.id
    ).order_by('-review_date').select_related('emiter', 'reviewed_by', 'approved_by').prefetch_related('message__receiver')

    comm_paginator = Paginator(comm_queryset, 4)
    comm_page_number = request.GET.get('comm_page')
    comm_page_obj = comm_paginator.get_page(comm_page_number)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if 'comm_page' in request.GET:
            return render(request, "mistemplates/_communication_table_list.html", {"comm_page_obj": comm_page_obj})
        else:
            return render(request, "mistemplates/_activity_list.html", {"page_obj": page_obj})

    # Clientes y Proveedores por Área
    procesos_donde_es_cliente = Process.objects.filter(internal_clients=area)
    procesos_donde_es_proveedor = Process.objects.filter(internal_suppliers=area)

    clientes_internos = Area.objects.filter(process_internal_client__in=procesos_donde_es_proveedor).distinct()
    proveedores_internos = Area.objects.filter(process_internal_supplier__in=procesos_donde_es_cliente).distinct()

    clientes_externos = ExternalClient.objects.filter(process_external_client__in=procesos_donde_es_proveedor).distinct()
    proveedores_externos = ExternalSupplier.objects.filter(process_external_supplier__in=procesos_donde_es_cliente).distinct()


    # === KPIs y Procesos con Alertas ===
    procesos_con_alertas = []
    process_labels = []
    process_values = []
    kpis_revision = 0
    kpis_fuera_rango = []

    area_processes = Process.objects.filter(responsible__area=area)

    for proceso in area_processes:
        indicadores_fuera_de_rango = 0
        indicadores = ProcessPerformanceIndicators.objects.filter(process=proceso)

        for indicador in indicadores:
            medicion = ProcessPerformanceMeasurements.objects.filter(
                process=proceso,
                performance_indicator=indicador.performanceindicator
            ).order_by('-date').first()

            if medicion:
                valor = medicion.measured_value
                min_val = indicador.min_acceptable_value
                max_val = indicador.max_acceptable_value

                fuera_de_rango = False
                if min_val is not None and valor < min_val:
                    fuera_de_rango = True
                if max_val is not None and valor > max_val:
                    fuera_de_rango = True

                if fuera_de_rango:
                    indicadores_fuera_de_rango += 1
                    kpis_fuera_rango.append({
                        "indicador": indicador.performanceindicator.name,
                        "proceso": proceso.name,
                        "valor": valor,
                        "rango": f"{min_val} - {max_val}",
                        "fecha": medicion.date,
                    })

        if indicadores_fuera_de_rango > 0:
            procesos_con_alertas.append(proceso)
            process_labels.append(proceso.name)
            process_values.append(indicadores_fuera_de_rango)
            kpis_revision += indicadores_fuera_de_rango

    # === Auditoría más próxima por área ===
    siguiente_auditoria = None
    siguiente_auditoria_dias_restantes = None

    # Buscar todas las auditorías futuras relacionadas al área
    auditorias_area = []

    for ap in AnnualPlan.objects.filter(audit_opening_date__gte=current_date):
        for audited_user in ap.audited.all():
            for up in audited_user.user.user_position.all():
                if up.position.area_id == area.id:
                    auditorias_area.append(ap)
                    break

    # Obtener la más próxima (fecha mínima)
    if auditorias_area:
        siguiente_auditoria = min(auditorias_area, key=lambda x: x.audit_opening_date)
        siguiente_auditoria_dias_restantes = (siguiente_auditoria.audit_opening_date - current_date).days

    # === Riesgos Evaluados y Re-Evaluados ===
    riesgos_eval = (
        RiskEvaluation.objects
        .filter(risk__area=area)
        .values(nombre_proceso=F('risk__process__name'))
        .annotate(
            alto=Count('id', filter=Q(risk_level='High')),
            moderado=Count('id', filter=Q(risk_level='Moderate')),
            bajo=Count('id', filter=Q(risk_level='Low'))
        )
        .order_by('nombre_proceso')
    )

    riesgos_reeval = (
        Reevaluation.objects
        .filter(risk__area=area)
        .values(nombre_proceso=F('risk__process__name'))
        .annotate(
            alto=Count('id', filter=Q(risk_level='High')),
            moderado=Count('id', filter=Q(risk_level='Moderate')),
            bajo=Count('id', filter=Q(risk_level='Low'))
        )
        .order_by('nombre_proceso')
    )

    def descomponer(queryset):
        procesos, altos, moderados, bajos = [], [], [], []
        for r in queryset:
            procesos.append(r['nombre_proceso'])
            altos.append(r['alto'])
            moderados.append(r['moderado'])
            bajos.append(r['bajo'])
        return procesos, altos, moderados, bajos

    procesos_eval, altos_eval, moderados_eval, bajos_eval = descomponer(riesgos_eval)
    procesos_reeval, altos_reeval, moderados_reeval, bajos_reeval = descomponer(riesgos_reeval)

    pie_eval_qs = (
        RiskEvaluation.objects
        .filter(risk__area=area)
        .values('risk_level')
        .annotate(total=Count('id'))
    )

    pie_reeval_qs = (
        Reevaluation.objects
        .filter(risk__area=area)
        .values('risk_level')
        .annotate(total=Count('id'))
    )

    pie_labels_eval = [item['risk_level'] for item in pie_eval_qs]
    pie_values_eval = [item['total'] for item in pie_eval_qs]
    pie_labels_reeval = [item['risk_level'] for item in pie_reeval_qs]
    pie_values_reeval = [item['total'] for item in pie_reeval_qs]

    # === Render ===
    contexto = {
        "area": area,
        "page_obj": page_obj,
        "comm_page_obj": comm_page_obj,
        # Datos para gráficos (evaluaciones)
        "procesos_eval": procesos_eval,
        "riesgo_alto_eval": altos_eval,
        "riesgo_moderado_eval": moderados_eval,
        "riesgo_bajo_eval": bajos_eval,
        "pie_labels_eval": pie_labels_eval,
        "pie_values_eval": pie_values_eval,
        # Re-evaluaciones
        "procesos_reeval": procesos_reeval,
        "riesgo_alto_reeval": altos_reeval,
        "riesgo_moderado_reeval": moderados_reeval,
        "riesgo_bajo_reeval": bajos_reeval,
        "pie_labels_reeval": pie_labels_reeval,
        "pie_values_reeval": pie_values_reeval,
        # Alertas de procesos
        "procesos_con_alertas": procesos_con_alertas,
        "kpis_revision": kpis_revision,
        "kpis_fuera_rango": kpis_fuera_rango,
        "process_labels": process_labels,
        "process_values": process_values,
        # Auditoría próxima
        "siguiente_auditoria": siguiente_auditoria,
        "siguiente_auditoria_dias_restantes": siguiente_auditoria_dias_restantes,
        # Clientes y Proveedores del área
        "clientes_internos": clientes_internos,
        "proveedores_internos": proveedores_internos,
        "clientes_externos": clientes_externos,
        "proveedores_externos": proveedores_externos,
        "total_clientes": clientes_internos.count() + clientes_externos.count(),
        "total_proveedores": proveedores_internos.count() + proveedores_externos.count(),
    }

    return render(request, "mistemplates/area-dashboard.html", contexto)

class PagesView(TemplateView):
    pass

# Authenticatin
pages_normai_landing= PagesView.as_view(template_name="pages/pages-normai-landing.html")

authentication_signin_basic= PagesView.as_view(template_name="pages/authentication/auth-signin-basic.html")
authentication_signin_cover= PagesView.as_view(template_name="pages/authentication/auth-signin-cover.html")
authentication_signup_basic= PagesView.as_view(template_name="pages/authentication/auth-signup-basic.html")
authentication_signup_cover= PagesView.as_view(template_name="pages/authentication/auth-signup-cover.html")
authentication_pass_reset_basic= PagesView.as_view(template_name="pages/authentication/auth-pass-reset-basic.html")
authentication_pass_reset_cover= PagesView.as_view(template_name="pages/authentication/auth-pass-reset-cover.html")
authentication_lockscreen_basic= PagesView.as_view(template_name="pages/authentication/auth-lockscreen-basic.html")
authentication_lockscreen_cover= PagesView.as_view(template_name="pages/authentication/auth-lockscreen-cover.html")
authentication_logout_basic= PagesView.as_view(template_name="pages/authentication/auth-logout-basic.html")
authentication_logout_cover= PagesView.as_view(template_name="pages/authentication/auth-logout-cover.html")
authentication_success_msg_basic= PagesView.as_view(template_name="pages/authentication/auth-success-msg-basic.html")
authentication_success_msg_cover= PagesView.as_view(template_name="pages/authentication/auth-success-msg-cover.html")
authentication_twostep_basic= PagesView.as_view(template_name="pages/authentication/auth-twostep-basic.html")
authentication_twostep_cover= PagesView.as_view(template_name="pages/authentication/auth-twostep-cover.html")
authentication_404_basic= PagesView.as_view(template_name="pages/authentication/auth-404-basic.html")
authentication_404_cover= PagesView.as_view(template_name="pages/authentication/auth-404-cover.html")
authentication_404_alt= PagesView.as_view(template_name="pages/authentication/auth-404-alt.html")
authentication_500= PagesView.as_view(template_name="pages/authentication/auth-500.html")
authentication_pass_change_basic= PagesView.as_view(template_name="pages/authentication/auth-pass-change-basic.html")
authentication_pass_change_cover= PagesView.as_view(template_name="pages/authentication/auth-pass-change-cover.html")
authentication_offline= PagesView.as_view(template_name="pages/authentication/auth-offline.html")
# Pages 
pages_blog_grid= PagesView.as_view(template_name="pages/pages-blog-grid.html")
pages_blog_list= PagesView.as_view(template_name="pages/pages-blog-list.html")
pages_blog_overview= PagesView.as_view(template_name="pages/pages-blog-overview.html")
pages_starter= PagesView.as_view(template_name="pages/pages-starter.html")
pages_profile= PagesView.as_view(template_name="pages/pages-profile.html")
pages_profile_settings= PagesView.as_view(template_name="pages/pages-profile-settings.html")
pages_team= PagesView.as_view(template_name="pages/pages-team.html")
pages_timeline= PagesView.as_view(template_name="pages/pages-timeline.html")
pages_faqs= PagesView.as_view(template_name="pages/pages-faqs.html")
pages_pricing= PagesView.as_view(template_name="pages/pages-pricing.html")
pages_gallery= PagesView.as_view(template_name="pages/pages-gallery.html")
pages_maintenance= PagesView.as_view(template_name="pages/pages-maintenance.html")
pages_coming_soon= PagesView.as_view(template_name="pages/pages-coming-soon.html")
pages_sitemap= PagesView.as_view(template_name="pages/pages-sitemap.html")
pages_search_results= PagesView.as_view(template_name="pages/pages-search-results.html")

pages_landing= PagesView.as_view(template_name="pages/pages-landing.html")
pages_nft_landing = PagesView.as_view(template_name="pages/pages-nft-landing.html")
pages_job_landing = PagesView.as_view(template_name="pages/pages-job-landing.html")

pages_privacy_policy = PagesView.as_view(template_name="pages/pages-privacy-policy.html")
pages_term_conditions = PagesView.as_view(template_name="pages/pages-term-conditions.html")
