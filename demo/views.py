from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from audits.executive_dashboard import get_executive_dashboard


@login_required
def demo_dashboard(request):
    """
    Vista principal de demostración — F6-01
    Muestra el dashboard ejecutivo completo como punto de entrada
    del recorrido de defensa del TFG.
    """
    standard_id = request.GET.get('standard_id')
    if standard_id:
        standard_id = int(standard_id)

    dashboard_data = get_executive_dashboard(standard_id=standard_id)

    from standards.models import Standard
    standards = Standard.objects.filter(is_active=True)

    return render(request, 'mistemplates/demo/f6_01_dashboard.html', {
        'dashboard_data': dashboard_data,
        'standards': standards,
        'selected_standard_id': standard_id,
    })

@login_required
def demo_normative_catalog(request):
    return render(request, 'mistemplates/demo/f6_02_normativo.html', {})

@login_required
def demo_audit_checklists(request):
    return render(request, 'mistemplates/demo/f6_03_auditorias.html', {})

@login_required
def demo_compliance(request):
    return render(request, 'mistemplates/demo/f6_04_cumplimiento.html', {})

@login_required
def demo_analytics(request):
    return render(request, 'mistemplates/demo/f6_05_analitica.html', {})