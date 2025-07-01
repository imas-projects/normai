from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Avg
from django.utils.timezone import now
from django.db.models import OuterRef, Subquery
from collections import defaultdict
from django.db.models.functions import TruncMonth
from audits.models import AnnualPlan, AuditReport, CorrectiveAction, CorrectiveActionFollowUp, Findings 
from processes.models import Process, ProcessPerformanceIndicators, PerformanceIndicator, ProcessPerformanceMeasurements
from company.models import Area
from risks.models import RiskTreatment
from communications.models import CommunicationTable



# Create your views here.

@login_required
def wellcome_view(request):
    current_year = now().year

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

    for ppm in recientes_process_perform_measure:
        

        indicador = ProcessPerformanceIndicators.objects.get(
            process=ppm.process,
            performanceindicator=ppm.performance_indicator
        )
        
        min_val = indicador.min_acceptable_value
        max_val = indicador.max_acceptable_value

        if ((min_val is not None and ppm.measured_value < min_val) or (max_val is not None and ppm.measured_value > max_val)):
            alerta.append(ppm)

    procesos_en_alerta = len(alerta)
    tasa_procesos_alerta = (procesos_en_alerta / total_procesos) * 100 if realizadas > 0 else 0
       

    # === Indicador 5: Índice de Mejora Continua ===
    ultimo_mes = hoy - timedelta(days=30)
    ultimo_dosmeses = hoy - timedelta(days=60)
    actuales = ProcessPerformanceMeasurements.objects.filter(date__gte=ultimo_mes).values('performance_indicator').annotate(avg_actual=Avg('measured_value'))
    anteriores = ProcessPerformanceMeasurements.objects.filter(date__range=(ultimo_dosmeses, ultimo_mes)).values('performance_indicator').annotate(avg_anterior=Avg('measured_value'))

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

    for key, label in reversed(list(clasificaciones_map.items())):
        clasificaciones_labels.append(label)
        total = next((f['total'] for f in findings_dist if f['classification'] == key), 0)
        clasificaciones_values.append(total)

    areas = Area.objects.all()

    processes_with_findings = Process.objects.annotate(
        total_findings=Count('processrequirement__findings')
    ).order_by('-total_findings')

    current_date = timezone.now().date()
    end_date = current_date + timedelta(days=30)
    risk_treatments = RiskTreatment.objects.filter(target_date__range=(current_date, end_date))
    processes = Process.objects.filter(review_date__range=(current_date, end_date))
    communications = CommunicationTable.objects.filter(review_date__range=(current_date, end_date))
    corrective_actions = CorrectiveAction.objects.filter(due_date__range=(current_date, end_date))
    activities = []

    for rt in risk_treatments:
        activities.append({
            "date": rt.target_date,
            "name": f"Risk Treatment: {rt.treatment_action[:40]}",
            "type": "Risk",
            "responsible": ", ".join([pos.name for pos in rt.responsible.all()]),
        })

    for p in processes:
        activities.append({
            "date": p.review_date,
            "name": f"Process Review: {p.name}",
            "type": "Process",
            "responsible": p.responsible.name if p.responsible else "",
        })

    for c in communications:
        activities.append({
            "date": c.review_date,
            "name": f"Communication Review: {c.code}",
            "type": "Communication",
            "responsible": c.reviewed_by.name if c.reviewed_by else "",
        })

    for ca in corrective_actions:
        activities.append({
            "date": ca.due_date,
            "name": f"Corrective Action: {ca.corrective_action[:40]}",
            "type": "Audit",
            "responsible": ca.responsible_user.username,
        })

    activities.sort(key=lambda x: x['date'])




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

        'procesos_en_alerta': procesos_en_alerta,
        'total_procesos': total_procesos,
        'tasa_procesos_alerta':tasa_procesos_alerta,

        'indice_mejora_continua':indice_mejora_continua,
        'areas_empresa':areas_empresa,


        'auditorias_labels': auditorias_labels,
        'auditorias_values': auditorias_values,

        'clasificaciones_labels': clasificaciones_labels,
        'clasificaciones_values': clasificaciones_values,

        'areas': areas,

        'processes_with_findings': processes_with_findings,

        "activities": activities,
    }

    return render(request, "mistemplates/user-dashboard.html", contexto)

@login_required
def area_view(request):
    return render(request,"mistemplates/area-dashboard.html")


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
