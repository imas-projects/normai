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
    """
    Vista del catálogo normativo — F6-02
    Muestra normas, cláusulas, requisitos y trazabilidad ISO 9001 ↔ AS9100.
    """
    from standards.models import Standard, Clause, StandardRequirement, StandardMapping

    standards = Standard.objects.filter(is_active=True).order_by('id')

    selected_standard_id = request.GET.get('standard_id')
    selected_clause_id = request.GET.get('clause_id')

    if selected_standard_id:
        selected_standard_id = int(selected_standard_id)
        selected_standard = Standard.objects.filter(
            id=selected_standard_id
        ).first()
    else:
        selected_standard = standards.first()
        if selected_standard:
            selected_standard_id = selected_standard.id

    # Cláusulas raíz de la norma seleccionada
    root_clauses = []
    if selected_standard:
        root_clauses = list(
            Clause.objects.filter(
                standard=selected_standard,
                parent__isnull=True
            ).order_by('ordering')
        )

    # Cláusula seleccionada y sus requisitos
    selected_clause = None
    clause_requirements = []
    child_clauses = []
    mappings = []

    if selected_clause_id:
        selected_clause = Clause.objects.filter(
            id=selected_clause_id
        ).select_related('standard', 'parent').first()

        if selected_clause:
            clause_requirements = list(
                StandardRequirement.objects.filter(
                    clause=selected_clause
                ).order_by('ordering')
            )
            child_clauses = list(
                Clause.objects.filter(
                    parent=selected_clause
                ).order_by('ordering')
            )

            # Mapeos para los requisitos de esta cláusula
            req_ids = [r.id for r in clause_requirements]
            mappings = list(
                StandardMapping.objects.filter(
                    source_requirement_id__in=req_ids
                ).select_related(
                    'source_requirement__clause__standard',
                    'target_requirement__clause__standard',
                ) | StandardMapping.objects.filter(
                    target_requirement_id__in=req_ids
                ).select_related(
                    'source_requirement__clause__standard',
                    'target_requirement__clause__standard',
                )
            )

    # Resumen de mapeos entre normas
    mapping_summary = {
        'total': StandardMapping.objects.count(),
        'equivalent': StandardMapping.objects.filter(
            mapping_type='EQUIVALENT'
        ).count(),
        'superset': StandardMapping.objects.filter(
            mapping_type='SUPERSET'
        ).count(),
        'no_equivalent': StandardMapping.objects.filter(
            mapping_type='NO_EQUIVALENT'
        ).count(),
    }

    # Estadísticas de la norma seleccionada
    standard_stats = {}
    if selected_standard:
        total_reqs = StandardRequirement.objects.filter(
            clause__standard=selected_standard
        ).count()
        mandatory_reqs = StandardRequirement.objects.filter(
            clause__standard=selected_standard,
            mandatory=True
        ).count()
        high_criticality = StandardRequirement.objects.filter(
            clause__standard=selected_standard,
            criticality_level='high'
        ).count()
        extensions = StandardRequirement.objects.filter(
            clause__standard=selected_standard,
            is_extension=True
        ).count()

        standard_stats = {
            'total_clauses': Clause.objects.filter(
                standard=selected_standard
            ).count(),
            'total_requirements': total_reqs,
            'mandatory_requirements': mandatory_reqs,
            'high_criticality': high_criticality,
            'extensions': extensions,
        }

    return render(request, 'mistemplates/demo/f6_02_normativo.html', {
        'standards': standards,
        'selected_standard': selected_standard,
        'selected_standard_id': selected_standard_id,
        'root_clauses': root_clauses,
        'selected_clause': selected_clause,
        'selected_clause_id': selected_clause_id,
        'clause_requirements': clause_requirements,
        'child_clauses': child_clauses,
        'mappings': mappings,
        'mapping_summary': mapping_summary,
        'standard_stats': standard_stats,
    })

@login_required
def demo_audit_checklists(request):
    return render(request, 'mistemplates/demo/f6_03_auditorias.html', {})

@login_required
def demo_compliance(request):
    return render(request, 'mistemplates/demo/f6_04_cumplimiento.html', {})

@login_required
def demo_analytics(request):
    return render(request, 'mistemplates/demo/f6_05_analitica.html', {})